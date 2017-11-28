from PIL import Image
import imageio
import face_recognition
from .models.models import FaceImage
from .models.database_manager import DatabaseManager

class FeatureAnalyzer:
    def __init__(self):
        self.db = DatabaseManager()

    def crop_img_into_id_imgs_dict(self, img, img_id):
        face_locations = face_recognition.face_locations(img)
        id_img = {}
        for count, face_location in enumerate(face_locations):
            top, right, bottom, left = face_location
            cropped_img = img[top:bottom, left:right]
            cropped_img_id = img_id + str(count)
            id_img[cropped_img_id] = cropped_img
        return id_img

    def write_img_to_path(self, img, fpath):
        try:
            imageio.imwrite(fpath, img)
            print("Successfully wrote img to path")
        except Exception as e:
            print(e)

    def write_original_img_cropped_img_id_to_db(self, orig_img_id, cropped_img_id):
        session = self.db.get_session()
        face_img = FaceImage(original_img_id=orig_img_id,
                             cropped_img_id=cropped_img_id)
        session.add(face_img)
        self.db.safe_commit(session)
