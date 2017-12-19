import os
from PIL import Image
import imageio
import numpy as np
import face_recognition
from .queue_poll import QueuePoll
from .models.database_manager import DatabaseManager
from .models.models import OriginalImage, CroppedImage, FeatureMapping, Match
import base64

class Pipeline:
    def __init__(self):
        self.img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')

    def _write_img_to_path(self, img, fpath):
        try:
            imageio.imwrite(fpath, img)
            print("Successfully wrote img to path")
        except Exception as e:
            print(e)
    
    def _get_cropped_img_ids_and_features(self):
        db = DatabaseManager()
        session = db.get_session()
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
        row = cls(**kwargs)
        session.add(row)
        return row

    def _process_original_img(self, original_img_id, session):
        self._add_entry_to_session(OriginalImage,
                                   session,
                                   img_id=original_img_id)

        input_img_base_path = os.path.join(self.img_dir, 'input')
        fpath = "{input_img_base_path}/{img_id}.jpg".format(input_img_base_path=input_img_base_path,
                                                            img_id=original_img_id)
        original_img = face_recognition.load_image_file(fpath)
        return original_img

    def _process_cropped_img(self, face_location, original_img, original_img_id, cropped_img_id, session):
        top, right, bottom, left = face_location
        cropped_img = original_img[top:bottom, left:right]
        print("cropped_img_id", cropped_img_id)
        output_img_base_path = os.path.join(self.img_dir, 'output')
        fpath = "{output_img_base_path}/{cropped_img_id}.jpg".format(output_img_base_path=output_img_base_path,
                                                                     cropped_img_id=cropped_img_id)
        self._write_img_to_path(cropped_img, fpath)

        self._add_entry_to_session(CroppedImage,
                                   session,
                                   img_id=cropped_img_id,
                                   original_img_id=original_img_id)
        return cropped_img

    def _process_feature_mapping(self, features, cropped_img_id, session):
        feature_str = base64.b64encode(features.dumps())
        self._add_entry_to_session(FeatureMapping,
                                   session,
                                   cropped_img_id=cropped_img_id,
                                   features=feature_str)
        return features

    def _process_matches(self, this_cropped_img_id, that_cropped_img_id, distance_score, session):
        if distance_score < 0.6 and this_cropped_img_id != that_cropped_img_id:
            print("Facedistance, cropped_img_id:", distance_score, that_cropped_img_id)
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


    def begin_pipeline(self):
        db = DatabaseManager()
        qp = QueuePoll(os.environ['IMAGE_PROCESSOR_QUEUE'])

        for message in qp.poll():
            session = db.get_session()
            original_img_id = message.content
            original_img = self._process_original_img(original_img_id, session)
            face_locations = face_recognition.face_locations(original_img)
            for count, face_location in enumerate(face_locations):
                cropped_img_id = original_img_id + str(count)
                cropped_img = self._process_cropped_img(face_location, original_img, original_img_id, cropped_img_id, session)
                features = face_recognition.face_encodings(cropped_img)
                if len(features):
                    features = self._process_feature_mapping(features[0], cropped_img_id, session)

                    cropped_img_ids, known_features = self._get_cropped_img_ids_and_features()
                    print(known_features)
                    face_distances = face_recognition.face_distance(known_features, features)
                    print(face_distances)
                    for count, face_distance in enumerate(face_distances):
                        self._process_matches(cropped_img_id, cropped_img_ids[count], float(face_distance), session)
            db.safe_commit(session)

            print("Polling next iteration...")
