# pylint: disable=no-self-use

import os
from http import HTTPStatus
import werkzeug
from werkzeug.utils import secure_filename
from flask_restful import Resource, Api, reqparse
from flask import Flask, g
from .models.models import Match, Image, User, ImageStatus
from .models.database_manager import get_database_manager
from .models.image_status_enum import ImageStatusEnum
from .log import get_logger
from .queue_poll import create_queue_service
from .auth import auth
from .settings import IMAGE_PROCESSOR_QUEUE, ALLOWED_EXTENSIONS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(
    os.path.dirname(
        os.path.abspath(__file__)),
    'images')
app.url_map.strict_slashes = False
api = Api(app)
queue_service = create_queue_service(IMAGE_PROCESSOR_QUEUE)
logger = get_logger(__name__)


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
        db = get_database_manager()
        session = db.get_session()
        query = session.query(User).filter(User.username == username).first()
        session.close()
        if query is not None:
            return 'User already registered', HTTPStatus.BAD_REQUEST.value
        user = User(username=username)
        user.hash_password(password)
        session = db.get_session()
        session.add(user)
        db.safe_commit(session)
        return {'username': username}, HTTPStatus.CREATED.value


class ProcessImg(Resource):
    method_decorators = [auth.login_required]

    # pylint: disable=broad-except
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('img_id',
                            required=True,
                            help="img_id missing in the post body")
        args = parser.parse_args()
        img_id = args['img_id']
        db = get_database_manager()
        session = db.get_session()
        img_status = session.query(ImageStatus).filter(
            ImageStatus.img_id == img_id).first()
        if img_status is not None:
            if img_status.status != ImageStatusEnum.uploaded.name:
                session.close()
                return ('Image previously placed on queue',
                        HTTPStatus.BAD_REQUEST.value)
            try:
                queue_service.put_message(IMAGE_PROCESSOR_QUEUE, img_id)
                img_status.status = ImageStatusEnum.on_queue.name
                db.safe_commit(session)
                logger.info('img successfully put on queue')
                return 'OK', HTTPStatus.OK.value
            except Exception:
                error_msg = "img_id could not be added to queue"
                img_status.status = ImageStatusEnum.uploaded.name
                img_status.error_msg = error_msg
                db.safe_commit(session)
                return error_msg, HTTPStatus.INTERNAL_SERVER_ERROR.value
        else:
            session.close()
            return 'Image not yet uploaded', HTTPStatus.BAD_REQUEST.value

    def get(self, img_id):
        logger.debug('checking if img has been processed')
        db = get_database_manager()
        session = db.get_session()
        img_status = session.query(ImageStatus).filter(
            ImageStatus.img_id == img_id).first()
        session.close()
        if img_status is not None:
            return {'status': img_status.status,
                    'error_msg': img_status.error_msg}
        return 'Image not yet uploaded', HTTPStatus.BAD_REQUEST.value


class ImgUpload(Resource):
    method_decorators = [auth.login_required]

    # pylint: disable=broad-except
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
        db = get_database_manager()
        if self._allowed_file(img.filename):
            filename = secure_filename(img.filename)
            img_id = filename[:filename.find('.')]
            session = db.get_session()
            prev_img_upload = session.query(ImageStatus).filter(
                ImageStatus.img_id == img_id).first()
            session.close()
            if prev_img_upload is not None:
                error_msg = "Image upload failed: image previously uploaded"
                return error_msg, HTTPStatus.BAD_REQUEST.value
            try:
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                img_status = ImageStatus(img_id=img_id,
                                         status=ImageStatusEnum.uploaded.name,
                                         error_msg=None)
                session = db.get_session()
                session.add(img_status)
                db.safe_commit(session)
                logger.info('img successfully uploaded')
                return 'OK', HTTPStatus.OK.value
            except Exception:
                return 'Server error', HTTPStatus.INTERNAL_SERVER_ERROR.value
        else:
            error_msg = ('Image upload failed: please use one of the '
                         'following extensions --> {}'
                         .format(ALLOWED_EXTENSIONS))
            return error_msg, HTTPStatus.BAD_REQUEST.value

    def _allowed_file(self, filename):
        return ('.' in filename and
                filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)


class ImgMatchList(Resource):
    method_decorators = [auth.login_required]

    # pylint: disable=assignment-from-no-return
    def get(self, img_id):
        logger.debug('getting img match list')
        db = get_database_manager()
        session = db.get_session()
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
        db = get_database_manager()
        session = db.get_session()
        query = session.query(Image).all()
        imgs = [f.img_id for f in query]
        session.close()
        return {'imgs': imgs}


api.add_resource(ImgUpload, '/api/v1/upload_image')
api.add_resource(ProcessImg, '/api/v1/process_image/',
                 '/api/v1/process_image/<string:img_id>')
api.add_resource(ImgMatchList, '/api/v1/image_matches/<string:img_id>')
api.add_resource(ImgList, '/api/v1/images')
api.add_resource(RegisterUser, '/api/v1/register_user')
api.add_resource(AuthenticationToken, '/api/v1/token')

# pylint: enable=no-self-use
