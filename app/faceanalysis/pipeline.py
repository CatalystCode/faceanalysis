from datetime import datetime

import numpy as np
from celery import Celery

from faceanalysis.face_vectorizer import face_vector_from_text
from faceanalysis.face_vectorizer import face_vector_to_text
from faceanalysis.face_vectorizer import get_face_vectors
from faceanalysis.log import get_logger
from faceanalysis.models.database_manager import get_database_manager
from faceanalysis.models.image_status_enum import ImageStatusEnum
from faceanalysis.models.models import FeatureMapping
from faceanalysis.models.models import Image
from faceanalysis.models.models import ImageStatus
from faceanalysis.models.models import Match
from faceanalysis.settings import DISTANCE_SCORE_THRESHOLD
from faceanalysis.settings import FACE_VECTORIZE_ALGORITHM
from faceanalysis.settings import IMAGE_PROCESSOR_QUEUE
from faceanalysis.settings import CELERY_BROKER
from faceanalysis.storage import StorageError
from faceanalysis.storage import delete_image
from faceanalysis.storage import get_image_path

db = get_database_manager()
logger = get_logger(__name__)
celery = Celery('pipeline', broker=CELERY_BROKER)
celery.conf.task_default_queue = IMAGE_PROCESSOR_QUEUE


def _add_entry_to_session(cls, session, **kwargs):
    logger.debug('adding entry to session')
    row = cls(**kwargs)
    session.add(row)
    return row


def _store_face_vector(features, img_id, session):
    logger.debug('processing feature mapping')
    _add_entry_to_session(FeatureMapping, session,
                          img_id=img_id,
                          features=face_vector_to_text(features))
    return features


def _store_matches(this_img_id, that_img_id, distance_score, session):
    logger.debug('processing matches')
    _add_entry_to_session(Match, session,
                          this_img_id=this_img_id,
                          that_img_id=that_img_id,
                          distance_score=distance_score)
    _add_entry_to_session(Match, session,
                          this_img_id=that_img_id,
                          that_img_id=this_img_id,
                          distance_score=distance_score)


def _load_image_ids_and_face_vectors():
    logger.debug('getting all img ids and respective features')
    session = db.get_session()
    known_features = []
    rows = session.query(FeatureMapping)\
        .all()
    session.close()
    img_ids = []
    for row in rows:
        img_ids.append(row.img_id)
        current_features = np.array(face_vector_from_text(row.features))
        known_features.append(current_features)
    return img_ids, np.array(known_features)


def _prepare_matches(matches, that_img_id, distance_score):
    match_exists = False
    for match in matches:
        if match["that_img_id"] == that_img_id:
            match_exists = True
            match["distance_score"] = min(match["distance_score"],
                                          distance_score)

    if not match_exists:
        matches.append({
            "that_img_id": that_img_id,
            "distance_score": distance_score
        })


def _update_img_status(img_id, status=None, error_msg=None):
    session = db.get_session()
    update_fields = {}
    if status:
        update_fields['status'] = status.name
    if error_msg:
        update_fields['error_msg'] = error_msg
    session.query(ImageStatus).filter(
        ImageStatus.img_id == img_id).update(update_fields)
    db.safe_commit(session)


# pylint: disable=len-as-condition
def _compute_distances(face_encodings, face_to_compare):
    if len(face_encodings) == 0:
        return np.empty((0))

    face_to_compare = np.array(face_to_compare)
    return np.linalg.norm(face_encodings - face_to_compare, axis=1)
# pylint: enable=len-as-condition


@celery.task(ignore_result=True)
def process_image(img_id):
    logger.info('Processing image %s', img_id)
    try:
        img_path = get_image_path(img_id)
    except StorageError:
        logger.error("Can't process image %s since it doesn't exist", img_id)
        _update_img_status(img_id, error_msg='Image processed before uploaded')
        return

    start = datetime.utcnow()
    _update_img_status(img_id, status=ImageStatusEnum.processing)

    prev_img_ids, prev_face_vectors = _load_image_ids_and_face_vectors()
    face_vectors = get_face_vectors(img_path, FACE_VECTORIZE_ALGORITHM)
    logger.info('Found %d faces in image %s', len(face_vectors), img_id)
    _update_img_status(img_id, status=ImageStatusEnum.face_vector_computed)

    session = db.get_session()
    _add_entry_to_session(Image, session, img_id=img_id)
    matches = []
    for face_vector in face_vectors:
        _store_face_vector(face_vector, img_id, session)

        distances = _compute_distances(prev_face_vectors, face_vector)
        for that_img_id, distance in zip(prev_img_ids, distances):
            if img_id == that_img_id:
                continue
            distance = float(distance)
            if distance >= DISTANCE_SCORE_THRESHOLD:
                continue
            _prepare_matches(matches, that_img_id, distance)

    logger.info('Found %d face matches for image %s', len(matches), img_id)
    for match in matches:
        _store_matches(img_id, match["that_img_id"],
                       match["distance_score"], session)

    db.safe_commit(session)
    _update_img_status(img_id,
                       status=ImageStatusEnum.finished_processing,
                       error_msg=('No faces found in image'
                                  if not face_vectors else None))
    delete_image(img_id)

    processing_time = (datetime.utcnow() - start).total_seconds()
    logger.info('Processed image %s in %d seconds', img_id, processing_time)
