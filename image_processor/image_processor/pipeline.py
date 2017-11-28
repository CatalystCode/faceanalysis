import os
import face_recognition
from .queue_poll import QueuePoll
from .feature_analyzer import FeatureAnalyzer
from .matcher import Matcher
from .featurizer import Featurizer
from .models.database_manager import DatabaseManager
from .models.models import PendingFaceImage

class Pipeline:
    def __init__(self):
        img_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
        self.output_img_base_path = os.path.join(img_dir, 'output')
        self.input_img_base_path = os.path.join(img_dir, 'input')
        self.fanalyzer = FeatureAnalyzer()
        self.qp = QueuePoll(os.environ['IMAGE_PROCESSOR_QUEUE'])

    def _add_pending_face_img(self, img_id):
        print("adding pending face image: ", img_id)
        db = DatabaseManager()
        session = db.get_session()
        query = session.query(PendingFaceImage).filter(PendingFaceImage.original_img_id == img_id).all()
        session.close()
        if len(query) == 0:
            session = db.get_session()
            pfi = PendingFaceImage(original_img_id=img_id)
            session.add(pfi)
            db.safe_commit(session)

    def _remove_pending_face_img(self, img_id):
        print("removing pending face image: ", img_id)
        db = DatabaseManager()
        session = db.get_session()
        query = session.query(PendingFaceImage).filter(PendingFaceImage.original_img_id == img_id).all()
        session.close()
        if len(query):
            session = db.get_session()
            for pfi in query:
                session.delete(pfi)
            db.safe_commit(session)

    def begin_pipeline(self):
        for message in self.qp.poll():
            img_id = message.content
            self._add_pending_face_img(img_id)
            img = face_recognition.load_image_file("{input_img_base_path}/{img_id}.jpg".format(input_img_base_path=self.input_img_base_path,
                                                                                               img_id=img_id))
            featurizer = Featurizer()
            matcher = Matcher()
            cropped_imgs = self.fanalyzer.crop_img_into_id_imgs_dict(img, img_id)
            for cropped_img_id, img in cropped_imgs.items():
                print("cropped_img_id", cropped_img_id)
                self.fanalyzer.write_img_to_path(img, "{output_img_base_path}/{cropped_img_id}.jpg".format(output_img_base_path=self.output_img_base_path,cropped_img_id=cropped_img_id))
                self.fanalyzer.write_original_img_cropped_img_id_to_db(img_id, cropped_img_id)
                featurizer.write_features_to_db(cropped_img_id, img)

                matcher.write_matches_to_db(cropped_img_id)
            self._remove_pending_face_img(img_id)
            print("Polling next iteration...")
