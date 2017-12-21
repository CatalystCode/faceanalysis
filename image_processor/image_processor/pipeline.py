import os
from PIL import Image
import imageio
import numpy as np
import face_recognition
from .queue_poll import QueuePoll
from .models.database_manager import DatabaseManager
from .models.models import OriginalImage, CroppedImage, FeatureMapping, Match
import base64
from .log import get_logger

class Pipeline:
    def __init__(self):
        self.db = DatabaseManager()
        dirname = os.path.dirname(os.path.abspath(__file__))
        self.img_dir = os.path.join(dirname, 'images')
        self.logger = get_logger(__name__,
                                 'image_processor.log',
                                 os.environ['LOGGING_LEVEL'])
        self.logger.debug('pipeline initialized')

    def _write_img_to_path(self, img, fpath):
        self.logger.debug('writing img to path')
        try:
            imageio.imwrite(fpath, img)
            self.logger.debug('Wrote image to path')
        except Exception as e:
            self.logger.error(e, exc_info=True)
    
    def _get_cropped_img_ids_and_features(self):
        self.logger.debug('getting all cropped img ids and respective features')
        session = self.db.get_session()
        known_features = []
        rows = session.query(FeatureMapping).all()
        session.close()
        cropped_img_ids = []
        for row in rows:
            cropped_img_ids.append(row.cropped_img_id)
            current_features = np.loads(base64.b64decode(row.features))
            known_features.append(current_features)
        return cropped_img_ids, known_features
    
    def _add_entry_to_session(self, cls, session, **kwargs):
        self.logger.debug('adding entry to session')
        row = cls(**kwargs)
        session.add(row)
        return row

    def _process_original_img(self, original_img_id, session):
        self.logger.debug('processing original img')
        self._add_entry_to_session(OriginalImage,
                                   session,
                                   img_id=original_img_id)
        input_img_base_path = os.path.join(self.img_dir, 'input')
        fpath = "{}/{}.jpg".format(input_img_base_path, original_img_id)
        original_img = face_recognition.load_image_file(fpath)
        return original_img

    def _process_cropped_img(self, face_location, original_img,
                             original_img_id, cropped_img_id, session):
        self.logger.debug('processing cropped img')
        top, right, bottom, left = face_location
        cropped_img = original_img[top:bottom, left:right]
        output_img_base_path = os.path.join(self.img_dir, 'output')
        fpath = "{}/{}.jpg".format(output_img_base_path, cropped_img_id)
        self._write_img_to_path(cropped_img, fpath)
        self._add_entry_to_session(CroppedImage,
                                   session,
                                   img_id=cropped_img_id,
                                   original_img_id=original_img_id)
        return cropped_img

    def _process_feature_mapping(self, features, cropped_img_id, session):
        self.logger.debug('processing feature mapping')
        feature_str = base64.b64encode(features.dumps())
        self._add_entry_to_session(FeatureMapping,
                                   session,
                                   cropped_img_id=cropped_img_id,
                                   features=feature_str)
        return features

    def _process_matches(self, this_cropped_img_id, that_cropped_img_id,
                         distance_score, session):
        self.logger.debug('processing matches')
        if distance_score < 0.6 and this_cropped_img_id != that_cropped_img_id:
            self._add_entry_to_session(Match,
                                       session,
                                       this_cropped_img_id=this_cropped_img_id,
                                       that_cropped_img_id=that_cropped_img_id,
                                       distance_score=distance_score)
            self._add_entry_to_session(Match,
                                       session,
                                       this_cropped_img_id=that_cropped_img_id,
                                       that_cropped_img_id=this_cropped_img_id,
                                       distance_score=distance_score)

    def _handle_message_from_queue(self, message):
        self.logger.debug("handling message from queue")
        session = self.db.get_session()
        original_img_id = message.content
        original_img = self._process_original_img(original_img_id, session)
        face_locations = face_recognition.face_locations(original_img)
        for count, face_location in enumerate(face_locations):
            cropped_img_id = original_img_id + str(count)
            cropped_img = self._process_cropped_img(face_location,
                                                    original_img,
                                                    original_img_id,
                                                    cropped_img_id,
                                                    session)
            features = face_recognition.face_encodings(cropped_img)
            if len(features):
                features = self._process_feature_mapping(features[0],
                                                         cropped_img_id,
                                                         session)
                cropped_img_ids, known_features = self._get_cropped_img_ids_and_features()
                face_distances = face_recognition.face_distance(known_features,
                                                                features)
                for count, face_distance in enumerate(face_distances):
                    self._process_matches(cropped_img_id,
                                          cropped_img_ids[count],
                                          float(face_distance),
                                          session)
        self.db.safe_commit(session)

    def begin_pipeline(self):
        self.logger.debug('pipeline began')
        qp = QueuePoll(os.environ['IMAGE_PROCESSOR_QUEUE'])
        for message in qp.poll():
            self._handle_message_from_queue(message)
            self.logger.debug("polling next iteration")
