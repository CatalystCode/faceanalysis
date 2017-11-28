import face_recognition
from .models.database_manager import DatabaseManager
from .models.models import Feature
import base64

class Featurizer:
    def __init__(self):
        self.db = DatabaseManager()

    def _get_features(self, img):
        features = face_recognition.face_encodings(img)
        if len(features):
            return face_recognition.face_encodings(img)[0]

    def write_features_to_db(self, cropped_img_id, img):
        features = self._get_features(img)
        if features is not None:
            feature_str = base64.b64encode(features.dumps())
            feature = Feature(cropped_img_id=cropped_img_id, features=feature_str)
            session = self.db.get_session()
            session.add(feature)
            self.db.safe_commit(session)
