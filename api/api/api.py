import os
from flask import Flask, Request
from werkzeug.utils import secure_filename
from flask_restful import Resource, Api, reqparse
from .models.models import Match, OriginalImage, CroppedImage
from .models.database_manager import DatabaseManager
import werkzeug
from azure.storage.queue import QueueService
from .log import get_logger

app = Flask(__name__)
#app.config['UPLOAD_FOLDER'] = '/app/api/images/input'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.join(
                                           os.path.dirname(
                                           os.path.abspath(__file__)),
                                           'images'),
                                           'input')
api = Api(app)
queue_service = QueueService(account_name=os.environ['STORAGE_ACCOUNT_NAME'],
                             account_key=os.environ['STORAGE_ACCOUNT_KEY'])
queue_service.create_queue(os.environ['IMAGE_PROCESSOR_QUEUE'])
logger = get_logger(__name__,
                    'api.log',
                    os.environ['LOGGING_LEVEL'])

class ImgUpload(Resource):
    def post(self):
        logger.debug('uploading img')
        parser = reqparse.RequestParser()
        parser.add_argument('file',
                            type=werkzeug.datastructures.FileStorage,
                            location='files')
        args = parser.parse_args()
        file = args['file']
        if file and self._allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_id = file.filename[:-4]
            queue_service.put_message(os.environ['IMAGE_PROCESSOR_QUEUE'],
                                      img_id)
            logger.info('img successfully uploaded and id put on queue')
            return {'success': True}

    def get(self, img_id):
        logger.debug('checking if uploaded img has been processed')
        session = DatabaseManager().get_session()
        query = session.query(OriginalImage).filter(OriginalImage.img_id == img_id).all()
        session.close()
        if len(query):
            return {'finished_processing': True}
        else:
            return {'finished_processing': False}

    def _allowed_file(self, filename):
        allowed_extensions = ['jpg']
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

class CroppedImgMatchList(Resource):
    def get(self, img_id):
        logger.debug('getting cropped img match list')
        session = DatabaseManager().get_session()
        query = session.query(Match).filter(Match.this_cropped_img_id == img_id)
        imgs = []
        distances = []
        for match in query:
            imgs.append(match.that_cropped_img_id)
            distances.append(match.distance_score)
        session.close()
        return {'imgs': imgs,
                'distances': distances}

class CroppedImgListFromOriginalImgId(Resource):
    def get(self, img_id):
        logger.debug('getting cropped img list given original img id')
        session = DatabaseManager().get_session()
        query = session.query(CroppedImage).filter(CroppedImage.original_img_id == img_id)
        imgs = list(set(cropped_img.img_id for cropped_img in query))
        session.close()
        return {'imgs': imgs}

class OriginalImgList(Resource):
    def get(self):
        logger.debug('getting original img list')
        session = DatabaseManager().get_session()
        query = session.query(OriginalImage).all()
        imgs = list(set(f.img_id for f in query))
        session.close()
        return {'imgs': imgs}

class OriginalImgListFromCroppedImgId(Resource):
    def get(self, img_id):
        logger.debug('getting original img list given cropped img id')
        session = DatabaseManager().get_session()
        query = session.query(CroppedImage).filter(CroppedImage.img_id == img_id).first()
        imgs = [query.original_img_id]
        session.close()
        return {'imgs': imgs}

api.add_resource(ImgUpload, '/api/upload_image/', '/api/upload_image/<string:img_id>/')
api.add_resource(CroppedImgMatchList, '/api/cropped_image_matches/<string:img_id>/')
api.add_resource(OriginalImgList, '/api/original_images/')
api.add_resource(OriginalImgListFromCroppedImgId, '/api/original_images/<string:img_id>/')
api.add_resource(CroppedImgListFromOriginalImgId, '/api/cropped_images/<string:img_id>/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
