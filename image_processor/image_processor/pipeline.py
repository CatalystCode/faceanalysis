import os
from PIL import Image
import imageio
import numpy as np
import face_recognition
from .queue_poll import QueuePoll
from .models.database_manager import DatabaseManager
from .models.models import Image, FeatureMapping, Match
import base64
from .log import get_logger
from sqlalchemy import or_, and_

class Pipeline:
    def __init__(self):
        self.db = DatabaseManager()
        self.logger = get_logger(__name__,
                                 'image_processor.log',
                                 os.environ['LOGGING_LEVEL'])
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

    def _process_img(self, img_id, session):
        self.logger.debug('processing img')
        self._add_entry_to_session(Image,
                                   session,
                                   img_id=img_id)
        for extension in self.allowed_file_extensions:
            img_name = "{}.{}".format(img_id, extension)
            fpath = os.path.join(self.img_dir, img_name)
            try:
                return face_recognition.load_image_file(fpath)
            except FileNotFoundError:
                continue

    def _delete_img(self, img_id):
        self.logger.debug('deleting img')
        for extension in self.allowed_file_extensions:
            img_name = "{}.{}".format(img_id, extension)
            fpath = os.path.join(self.img_dir, img_name)
            try:
                os.remove(fpath)
                self.logger.debug("removed {}".format(img_id))
            except FileNotFoundError:
                continue

    def _process_feature_mapping(self, features, img_id, session):
        self.logger.debug('processing feature mapping')
        feature_str = base64.b64encode(features.dumps())
        self._add_entry_to_session(FeatureMapping,
                                   session,
                                   img_id=img_id,
                                   features=feature_str)
        return features

    def _process_matches(self, this_img_id, that_img_id, distance_score, session):
        self.logger.debug('processing matches')
        if distance_score < 0.6 and this_img_id != that_img_id:
            query_session = self.db.get_session()
            query = session.query(Match).filter(
                    or_(
                        and_(Match.this_img_id == this_img_id,
                             Match.that_img_id == that_img_id),
                        and_(Match.this_img_id == that_img_id,
                             Match.that_img_id == this_img_id)
                    )
            ).first()
            query_session.close()
            if not query:
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

    def _handle_message_from_queue(self, message):
        self.logger.debug("handling message from queue")
        session = self.db.get_session()
        img_id = message.content
        img = self._process_img(img_id, session)
        face_locations = face_recognition.face_locations(img)
        for count, face_location in enumerate(face_locations):
            top, right, bottom, left = face_location
            cropped_img = img[top:bottom, left:right]
            features = face_recognition.face_encodings(cropped_img)
            if len(features):
                self._process_feature_mapping(features[0],
                                              img_id,
                                              session)

                img_ids, known_features = self._get_img_ids_and_features()
                face_distances = face_recognition.face_distance(known_features,
                                                                features)
                for count, face_distance in enumerate(face_distances):
                    self._process_matches(img_id,
                                          img_ids[count],
                                          float(face_distance),
                                          session)
        self.db.safe_commit(session)
        self._delete_img(img_id)

    def begin_pipeline(self):
        self.logger.debug('pipeline began')
        qp = QueuePoll(os.environ['IMAGE_PROCESSOR_QUEUE'])
        for message in qp.poll():
            self._handle_message_from_queue(message)
            self.logger.debug("polling next iteration")
