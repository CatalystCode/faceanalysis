# pylint: disable=too-few-public-methods

import os
import base64
import numpy as np
import face_recognition as fr
from .queue_poll import QueuePoll
from .models.database_manager import DatabaseManager
from .models.models import Image, FeatureMapping, Match, ImageStatus
from .models.image_status_enum import ImageStatusEnum
from .log import get_logger


class Pipeline:
    def __init__(self):
        self.db = DatabaseManager()
        self.logger = get_logger(__name__, os.environ['LOGGING_LEVEL'])
        dirname = os.path.dirname(os.path.abspath(__file__))
        self.img_dir = os.path.join(dirname, 'images')
        file_extensions = os.environ['ALLOWED_IMAGE_FILE_EXTENSIONS'].lower()
        self.allowed_file_extensions = file_extensions.split('_')
        self.logger.debug('pipeline initialized')

    def _add_entry_to_session(self, cls, session, **kwargs):
        self.logger.debug('adding entry to session')
        row = cls(**kwargs)
        session.add(row)
        return row

    # pylint: disable=broad-except
    def _process_img(self, img_id, session):
        self.logger.debug('processing img')
        img_has_been_uploaded = False
        img = None
        for extension in self.allowed_file_extensions:
            img_name = "{}.{}".format(img_id, extension)
            fpath = os.path.join(self.img_dir, img_name)
            try:
                img = fr.load_image_file(fpath)
                img_has_been_uploaded = True
                break
            except Exception:
                continue
        if img_has_been_uploaded:
            self._add_entry_to_session(Image,
                                       session,
                                       img_id=img_id)
        return img

    # pylint: disable=broad-except
    def _delete_img(self, img_id):
        self.logger.debug('deleting img')
        for extension in self.allowed_file_extensions:
            img_name = "{}.{}".format(img_id, extension)
            fpath = os.path.join(self.img_dir, img_name)
            try:
                os.remove(fpath)
                self.logger.debug("removed %s", img_id)
            except Exception:
                continue

    def _process_feature_mapping(self, features, img_id, session):
        self.logger.debug('processing feature mapping')
        feature_str = base64.b64encode(features.dumps())
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
            current_features = np.loads(base64.b64decode(row.features))
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
        curr_img = self._process_img(curr_img_id, session)
        if curr_img is not None:
            prev_img_ids, prev_features = self._get_img_ids_and_features()
            curr_matches = []
            face_locations = fr.face_locations(curr_img)
            if not face_locations:
                error_msg = "No faces found in image"
                self._update_img_status(curr_img_id, error_msg=error_msg)
            for face_location in face_locations:
                top, right, bottom, left = face_location
                curr_cropped_img = curr_img[top:bottom, left:right]
                curr_cropped_features = fr.face_encodings(
                    curr_cropped_img)
                if curr_cropped_features:
                    self._process_feature_mapping(curr_cropped_features[0],
                                                  curr_img_id,
                                                  session)
                    face_distances = fr.face_distance(prev_features,
                                                      curr_cropped_features)
                    for count, distance_score in enumerate(face_distances):
                        distance_score = float(distance_score)
                        that_img_id = prev_img_ids[count]
                        if distance_score < 0.6 and curr_img_id != that_img_id:
                            self._prepare_matches(curr_matches,
                                                  that_img_id,
                                                  distance_score)
            for curr_match in curr_matches:
                self._process_matches(curr_img_id,
                                      curr_match["that_img_id"],
                                      curr_match["distance_score"],
                                      session)
        else:
            error_msg = "Image processed before uploaded"
            self._update_img_status(curr_img_id, error_msg=error_msg)
        self._update_img_status(
            curr_img_id, status=ImageStatusEnum.finished_processing.name)
        self.db.safe_commit(session)
        self._delete_img(curr_img_id)

    def begin_pipeline(self):
        self.logger.debug('pipeline began')
        qp = QueuePoll(os.environ['IMAGE_PROCESSOR_QUEUE'])
        for message in qp.poll():
            self._handle_message_from_queue(message)
            self.logger.debug("polling next iteration")

# pylint: enable=too-few-public-methods
