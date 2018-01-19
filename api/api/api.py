import os
import werkzeug
from werkzeug.utils import secure_filename
from requests import codes
from azure.storage.queue import QueueService
from flask_restful import Resource, Api, reqparse
from flask import Flask, g
from .models.models import Match, Image, User, ImageStatus
from .models.database_manager import DatabaseManager
from .models.image_status_enum import ImageStatusEnum
from .log import get_logger
from .auth import auth

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    'images')
app.url_map.strict_slashes = False
api = Api(app)
queue_service = QueueService(account_name=os.environ['STORAGE_ACCOUNT_NAME'],
                             account_key=os.environ['STORAGE_ACCOUNT_KEY'])
queue_service.create_queue(os.environ['IMAGE_PROCESSOR_QUEUE'])
logger = get_logger(__name__, os.environ['LOGGING_LEVEL'])


class AuthenticationToken(Resource):
    method_decorators = [auth.login_required]

    def get(self):
        token = g.user.generate_auth_token()
        return {'token': token.decode('ascii')}


class RegisterUser(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username',
                            required=True,
                            help='username parameter missing in post body')
        parser.add_argument('password',
                            required=True,
                            help='password parameter missing in post body')
        args = parser.parse_args()
        username = args['username']
        password = args['password']
        db = DatabaseManager()
        session = db.get_session()
        query = session.query(User).filter(User.username == username).first()
        session.close()
        if query is not None:
            return 'User already registered', codes.BAD_REQUEST
        user = User(username=username)
        user.hash_password(password)
        session = db.get_session()
        session.add(user)
        db.safe_commit(session)
        return {'username': username}, codes.CREATED


class ProcessImg(Resource):
    method_decorators = [auth.login_required]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('img_id',
                            required=True,
                            help="img_id missing in the post body")
        args = parser.parse_args()
        img_id = args['img_id']
        db = DatabaseManager()
        session = db.get_session()
        try:
            queue_service.put_message(os.environ['IMAGE_PROCESSOR_QUEUE'],
                                      img_id)
            session.query(ImageStatus).filter(ImageStatus.img_id == img_id).update(
                {'status': ImageStatusEnum.on_queue.name})
            db.safe_commit(session)
            logger.info('img successfully put on queue')
        except:
            error_msg = "img_id could not be added to queue"
            session.query(ImageStatus).filter(ImageStatus.img_id == img_id).update(
                {'status': ImageStatusEnum.uploaded.name, 'error_msg': error_msg})
            db.safe_commit(session)
            return error_msg, codes.INTERNAL_SERVER_ERROR
        return 'OK', codes.OK

    def get(self, img_id):
        logger.debug('checking if img has been processed')
        session = DatabaseManager().get_session()
        img_status = session.query(ImageStatus).filter(
            ImageStatus.img_id == img_id).first()
        session.close()
        if img_status is not None:
            return {'status': img_status.status,
                    'error_msg': img_status.error_msg}
        else:
            return 'User already registered', codes.BAD_REQUEST


class ImgUpload(Resource):
    method_decorators = [auth.login_required]
    env_extensions = os.environ['ALLOWED_IMAGE_FILE_EXTENSIONS']
    allowed_extensions = env_extensions.lower().split('_')

    def post(self):
        logger.debug('uploading img')
        parser = reqparse.RequestParser()
        parser.add_argument('image',
                            type=werkzeug.datastructures.FileStorage,
                            required=True,
                            help="image missing in post body",
                            location='files')
        args = parser.parse_args()
        img = args['image']
        if self._allowed_file(img.filename):
            filename = secure_filename(img.filename)
            try:
                img_id = filename[:filename.find('.')]
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                img_status = ImageStatus(img_id=img_id,
                                         status=ImageStatusEnum.uploaded.name,
                                         error_msg=None)
                db = DatabaseManager()
                session = db.get_session()
                session.add(img_status)
                db.safe_commit(session)
            except:
                return 'Server error', codes.INTERNAL_SERVER_ERROR
            logger.info('img successfully uploaded')
            return 'OK', codes.OK
        else:
            error_msg = '''Image upload failed: please use one of the following 
extensions --> {}'''.format(self.allowed_extensions)
            return error_msg, codes.BAD_REQUEST

    def _allowed_file(self, filename):
        return ('.' in filename and
                filename.rsplit('.', 1)[1].lower() in self.allowed_extensions)


class ImgMatchList(Resource):
    method_decorators = [auth.login_required]

    def get(self, img_id):
        logger.debug('getting img match list')
        session = DatabaseManager().get_session()
        query = session.query(Match).filter(Match.this_img_id == img_id)
        imgs = []
        distances = []
        for match in query:
            imgs.append(match.that_img_id)
            distances.append(match.distance_score)
        session.close()
        return {'imgs': imgs,
                'distances': distances}


class ImgList(Resource):
    method_decorators = [auth.login_required]

    def get(self):
        logger.debug('getting img list')
        session = DatabaseManager().get_session()
        query = session.query(Image).all()
        imgs = [f.img_id for f in query]
        session.close()
        return {'imgs': imgs}


api.add_resource(ImgUpload, '/api/upload_image')
api.add_resource(ProcessImg, '/api/process_image/',
                 '/api/process_image/<string:img_id>')
api.add_resource(ImgMatchList, '/api/image_matches/<string:img_id>')
api.add_resource(ImgList, '/api/images')
api.add_resource(RegisterUser, '/api/register_user')
api.add_resource(AuthenticationToken, '/api/token')
