# pylint: disable=too-few-public-methods

import os
import json
import numpy as np
from .face_vectorizer import get_face_vectors
from .queue_poll import QueuePoll
from .models.database_manager import get_database_manager
from .models.models import Image, FeatureMapping, Match, ImageStatus
from .models.image_status_enum import ImageStatusEnum
from .log import get_logger
from .settings import (IMAGE_PROCESSOR_QUEUE, ALLOWED_EXTENSIONS,
                       DISTANCE_SCORE_THRESHOLD, FACE_VECTORIZE_ALGORITHM)


class Pipeline:
    def __init__(self):
        self.db = get_database_manager()
        self.logger = get_logger(__name__)
        dirname = os.path.dirname(os.path.abspath(__file__))
        self.img_dir = os.path.join(dirname, 'images')
        self.logger.debug('pipeline initialized')

    def _add_entry_to_session(self, cls, session, **kwargs):
        self.logger.debug('adding entry to session')
        row = cls(**kwargs)
        session.add(row)
        return row

    def _find_image(self, img_id, session):
        self.logger.debug('finding image %s', img_id)

        img_path = None
        for extension in ALLOWED_EXTENSIONS:
            img_name = "{}.{}".format(img_id, extension)
            fpath = os.path.join(self.img_dir, img_name)
            if os.path.isfile(fpath):
                img_path = fpath
                break

        if img_path:
            self._add_entry_to_session(Image,
                                       session,
                                       img_id=img_id)

        return img_path

    # pylint: disable=broad-except
    def _delete_img(self, img_id):
        self.logger.debug('deleting img')
        for extension in ALLOWED_EXTENSIONS:
            img_name = "{}.{}".format(img_id, extension)
            fpath = os.path.join(self.img_dir, img_name)
            try:
                os.remove(fpath)
                self.logger.debug("removed %s", img_id)
            except Exception:
                continue

    def _process_feature_mapping(self, features, img_id, session):
        self.logger.debug('processing feature mapping')
        feature_str = json.dumps(features)
        self._add_entry_to_session(FeatureMapping,
                                   session,
                                   img_id=img_id,
                                   features=feature_str)
        return features

    def _process_matches(self, this_img_id,
                         that_img_id, distance_score, session):
        self.logger.debug('processing matches')
        self._add_entry_to_session(Match,
                                   session,
                                   this_img_id=this_img_id,
                                   that_img_id=that_img_id,
                                   distance_score=distance_score)
        self._add_entry_to_session(Match,
                                   session,
                                   this_img_id=that_img_id,
                                   that_img_id=this_img_id,
                                   distance_score=distance_score)

    def _get_img_ids_and_features(self):
        self.logger.debug('getting all img ids and respective features')
        session = self.db.get_session()
        known_features = []
        rows = session.query(FeatureMapping).all()
        session.close()
        img_ids = []
        for row in rows:
            img_ids.append(row.img_id)
            current_features = np.array(json.loads(row.features))
            known_features.append(current_features)
        return img_ids, np.array(known_features)

    @classmethod
    def _prepare_matches(cls, matches, that_img_id, distance_score):
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

    def _update_img_status(self, img_id, status=None, error_msg=None):
        session = self.db.get_session()
        update_fields = {}
        if status:
            update_fields['status'] = status
        if error_msg:
            update_fields['error_msg'] = error_msg
        session.query(ImageStatus).filter(
            ImageStatus.img_id == img_id).update(update_fields)
        self.db.safe_commit(session)

    def _img_should_be_processed(self, img_id):
        session = self.db.get_session()
        img_status = session.query(ImageStatus).filter(
            ImageStatus.img_id == img_id).first()
        session.close()
        if img_status is not None:
            return img_status.status == ImageStatusEnum.on_queue.name
        return False

    # pylint: disable=len-as-condition
    @classmethod
    def _compute_distances(cls, face_encodings, face_to_compare):
        if len(face_encodings) == 0:
            return np.empty((0))

        face_to_compare = np.array(face_to_compare)
        return np.linalg.norm(face_encodings - face_to_compare, axis=1)

    # pylint: disable=too-many-locals
    def _handle_message_from_queue(self, message):
        self.logger.debug("handling message from queue")
        session = self.db.get_session()
        curr_img_id = message.content
        if not self._img_should_be_processed(curr_img_id):
            session.close()
            return
        self._update_img_status(
            curr_img_id, status=ImageStatusEnum.processing.name)
        curr_img_path = self._find_image(curr_img_id, session)
        if curr_img_path is not None:
            prev_img_ids, prev_features = self._get_img_ids_and_features()
            curr_matches = []
            face_vectors = get_face_vectors(
                curr_img_path, FACE_VECTORIZE_ALGORITHM)
            if not face_vectors:
                error_msg = "No faces found in image"
                self._update_img_status(curr_img_id, error_msg=error_msg)
            for face_vector in face_vectors:
                self._process_feature_mapping(
                    face_vector, curr_img_id, session)
                face_distances = self._compute_distances(
                    prev_features, face_vector)
                for i, distance_score in enumerate(face_distances):
                    that_img_id = prev_img_ids[i]
                    if curr_img_id == that_img_id:
                        continue
                    distance_score = float(distance_score)
                    if distance_score >= DISTANCE_SCORE_THRESHOLD:
                        continue
                    self._prepare_matches(
                        curr_matches, that_img_id, distance_score)
            for curr_match in curr_matches:
                self._process_matches(
                    curr_img_id, curr_match["that_img_id"],
                    curr_match["distance_score"], session)
        else:
            error_msg = "Image processed before uploaded"
            self._update_img_status(curr_img_id, error_msg=error_msg)
        self._update_img_status(
            curr_img_id, status=ImageStatusEnum.finished_processing.name)
        self.db.safe_commit(session)
        self._delete_img(curr_img_id)

    def begin_pipeline(self):
        self.logger.debug('pipeline began')
        qp = QueuePoll(IMAGE_PROCESSOR_QUEUE)
        for message in qp.poll():
            self._handle_message_from_queue(message)
            self.logger.debug("polling next iteration")

# pylint: enable=too-few-public-methods
