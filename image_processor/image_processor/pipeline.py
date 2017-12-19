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
    def _crop_img_into_id_imgs_dict(self, img, img_id):
        face_locations = face_recognition.face_locations(img)
        id_img = {}
        for count, face_location in enumerate(face_locations):
            top, right, bottom, left = face_location
            cropped_img = img[top:bottom, left:right]
            cropped_img_id = img_id + str(count)
            id_img[cropped_img_id] = cropped_img
        return id_img

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

    def begin_pipeline(self):
        db = DatabaseManager()
        img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
        output_img_base_path = os.path.join(img_dir, 'output')
        input_img_base_path = os.path.join(img_dir, 'input')
        qp = QueuePoll(os.environ['IMAGE_PROCESSOR_QUEUE'])

        for message in qp.poll():
            session = db.get_session()
            img_id = message.content

            #TODO: is_pending is not necessary
            self._add_entry_to_session(OriginalImage,
                                       session,
                                       img_id=img_id,
                                       is_pending=True)

            img = face_recognition.load_image_file("{input_img_base_path}/{img_id}.jpg".format(input_img_base_path=input_img_base_path,
                                                                                               img_id=img_id))
            #TODO: Get rid of all of these img_id_dicts and make them explicit for loops, then make each individual part a small function 
            cropped_imgs = self._crop_img_into_id_imgs_dict(img, img_id)
            for cropped_img_id, img in cropped_imgs.items():
                print("cropped_img_id", cropped_img_id)
                self._write_img_to_path(img, "{output_img_base_path}/{cropped_img_id}.jpg".format(output_img_base_path=output_img_base_path,cropped_img_id=cropped_img_id))

                self._add_entry_to_session(CroppedImage,
                                           session,
                                           img_id=cropped_img_id,
                                           original_img_id=img_id)

                features = face_recognition.face_encodings(img)
                if len(features):
                    features = features[0]

                    feature_str = base64.b64encode(features.dumps())
                    self._add_entry_to_session(FeatureMapping,
                                               session,
                                               cropped_img_id=cropped_img_id,
                                               features=feature_str)

                    cropped_img_ids, known_features = self._get_cropped_img_ids_and_features()
                    print(known_features)
                    face_distances = face_recognition.face_distance(known_features, features)
                    print(face_distances)
                    for count, face_distance in enumerate(face_distances):
                        if face_distance < 0.6 and cropped_img_id != cropped_img_ids[count]:
                            print("Facedistance, cropped_img_id:", face_distance, cropped_img_ids[count])
                            self._add_entry_to_session(Match,
                                                       session,
                                                       this_cropped_img_id=cropped_img_id,
                                                       that_cropped_img_id=cropped_img_ids[count],
                                                       distance_score=float(face_distance))

                            self._add_entry_to_session(Match,
                                                       session,
                                                       this_cropped_img_id=cropped_img_ids[count],
                                                       that_cropped_img_id=cropped_img_id,
                                                       distance_score=float(face_distance))

            db.safe_commit(session)

            print("Polling next iteration...")
