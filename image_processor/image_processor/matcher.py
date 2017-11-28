import face_recognition
import numpy
import base64
from .models.database_manager import DatabaseManager
from .models.models import Feature, Match 

class Matcher:
    def __init__(self):
        self.db = DatabaseManager()

    def _get_img_features(self, cropped_img_id):
        session = self.db.get_session()
        img = session.query(Feature).filter(Feature.cropped_img_id == cropped_img_id).first()
        session.close()
        if img is not None:
            img_features = base64.b64decode(img.features)
            return numpy.loads(img_features)

    def _get_cropped_img_ids_and_features(self):
        session = self.db.get_session()
        known_features = []
        rows = session.query(Feature).all()
        session.close()
        cropped_img_ids = []
        for row in rows:
            cropped_img_ids.append(row.cropped_img_id)
            current_features = numpy.loads(base64.b64decode(row.features))
            known_features.append(current_features)
        return cropped_img_ids, known_features 
    
    def write_matches_to_db(self, cropped_img_id):
        curr_img_features = self._get_img_features(cropped_img_id)
        if curr_img_features is not None:
            cropped_img_ids, known_features = self._get_cropped_img_ids_and_features()
            print(known_features)
            face_distances = face_recognition.face_distance(known_features, curr_img_features)
            print(face_distances)
            session = self.db.get_session()
            for count, face_distance in enumerate(face_distances):
                if face_distance < 0.6 and cropped_img_id != cropped_img_ids[count]:
                    print("Facedistance, cropped_img_id:", face_distance, cropped_img_ids[count])
                    match = Match(cropped_img_id_1=cropped_img_id, cropped_img_id_2=cropped_img_ids[count], distance_score=float(face_distance))
                    session.add(match)
                    reverse_match = Match(cropped_img_id_1=cropped_img_ids[count], cropped_img_id_2=cropped_img_id, distance_score=float(face_distance))
                    session.add(reverse_match)
            self.db.safe_commit(session)
