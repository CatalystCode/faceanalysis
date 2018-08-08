import os

import numpy as np

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
from faceanalysis.queue_poll import QueuePoll
from faceanalysis.settings import ALLOWED_EXTENSIONS
from faceanalysis.settings import DISTANCE_SCORE_THRESHOLD
from faceanalysis.settings import FACE_VECTORIZE_ALGORITHM
from faceanalysis.settings import IMAGE_PROCESSOR_QUEUE


db = get_database_manager()
logger = get_logger(__name__)
img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')


def _add_entry_to_session(cls, session, **kwargs):
    logger.debug('adding entry to session')
    row = cls(**kwargs)
    session.add(row)
    return row


def _find_image(img_id, session):
    logger.debug('finding image %s', img_id)

    img_path = None
    for extension in ALLOWED_EXTENSIONS:
        img_name = "{}.{}".format(img_id, extension)
        fpath = os.path.join(img_dir, img_name)
        if os.path.isfile(fpath):
            img_path = fpath
            break

    if img_path:
        _add_entry_to_session(Image, session, img_id=img_id)

    return img_path


# pylint: disable=broad-except
def _delete_img(img_id):
    logger.debug('deleting img')
    for extension in ALLOWED_EXTENSIONS:
        img_name = "{}.{}".format(img_id, extension)
        fpath = os.path.join(img_dir, img_name)
        try:
            os.remove(fpath)
            logger.debug("removed %s", img_id)
        except Exception:
            continue
# pylint: enable=broad-except


def _process_feature_mapping(features, img_id, session):
    logger.debug('processing feature mapping')
    _add_entry_to_session(FeatureMapping, session,
                          img_id=img_id,
                          features=face_vector_to_text(features))
    return features


def _process_matches(this_img_id, that_img_id, distance_score, session):
    logger.debug('processing matches')
    _add_entry_to_session(Match, session,
                          this_img_id=this_img_id,
                          that_img_id=that_img_id,
                          distance_score=distance_score)
    _add_entry_to_session(Match, session,
                          this_img_id=that_img_id,
                          that_img_id=this_img_id,
                          distance_score=distance_score)


def _get_img_ids_and_features():
    logger.debug('getting all img ids and respective features')
    session = db.get_session()
    known_features = []
    rows = session.query(FeatureMapping).all()
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


def _img_should_be_processed(img_id):
    session = db.get_session()
    img_status = session.query(ImageStatus).filter(
        ImageStatus.img_id == img_id).first()
    session.close()
    if img_status is None:
        return False
    return img_status.status == ImageStatusEnum.on_queue.name


# pylint: disable=len-as-condition
def _compute_distances(face_encodings, face_to_compare):
    if len(face_encodings) == 0:
        return np.empty((0))

    face_to_compare = np.array(face_to_compare)
    return np.linalg.norm(face_encodings - face_to_compare, axis=1)
# pylint: enable=len-as-condition


def _handle_message_from_queue(img_id):
    if not _img_should_be_processed(img_id):
        return

    logger.debug("handling message from queue for image %s", img_id)
    _update_img_status(img_id, status=ImageStatusEnum.processing)
    session = db.get_session()
    img_path = _find_image(img_id, session)
    if img_path is not None:
        prev_img_ids, prev_features = _get_img_ids_and_features()
        matches = []
        face_vectors = get_face_vectors(img_path, FACE_VECTORIZE_ALGORITHM)
        if not face_vectors:
            _update_img_status(img_id, error_msg="No faces found in image")

        for face_vector in face_vectors:
            _process_feature_mapping(face_vector, img_id, session)
            distances = _compute_distances(prev_features, face_vector)
            for that_img_id, distance in zip(prev_img_ids, distances):
                if img_id == that_img_id:
                    continue
                distance = float(distance)
                if distance >= DISTANCE_SCORE_THRESHOLD:
                    continue
                _prepare_matches(matches, that_img_id, distance)

        for match in matches:
            _process_matches(img_id, match["that_img_id"],
                             match["distance_score"], session)
    else:
        _update_img_status(img_id, error_msg="Image processed before uploaded")
    _update_img_status(img_id, status=ImageStatusEnum.finished_processing)
    db.safe_commit(session)
    _delete_img(img_id)


def begin_pipeline():
    logger.debug('pipeline began')
    qp = QueuePoll(IMAGE_PROCESSOR_QUEUE)
    for message in qp.poll():
        _handle_message_from_queue(message.content)
        logger.debug("polling next iteration")
