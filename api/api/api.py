import os
from flask import Flask, Request, abort, g
from werkzeug.utils import secure_filename
from flask_restful import Resource, Api, reqparse
from .models.models import Match, OriginalImage, User
from .models.database_manager import DatabaseManager
import werkzeug
from azure.storage.queue import QueueService
from .log import get_logger
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
#app.config['UPLOAD_FOLDER'] = '/app/api/images/input'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.join(
                                           os.path.dirname(
                                           os.path.abspath(__file__)),
                                           'images'),
                                           'input')
app.url_map.strict_slashes = False
api = Api(app)
queue_service = QueueService(account_name=os.environ['STORAGE_ACCOUNT_NAME'],
                             account_key=os.environ['STORAGE_ACCOUNT_KEY'])
queue_service.create_queue(os.environ['IMAGE_PROCESSOR_QUEUE'])
logger = get_logger(__name__,
                    'api.log',
                    os.environ['LOGGING_LEVEL'])

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username_or_token, password):
    # first try to authenticate by token
    user = User.verify_auth_token(username_or_token)
    session = DatabaseManager().get_session()
    if not user:
        # try to authenticate with username/password
        user = session.query(User).filter(User.username == username_or_token).first()
        if not user or not user.verify_password(password):
            session.close()
            return False
    g.user = user
    session.close()
    return True

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
            return 'User already registered', 400
        user = User(username=username)
        user.hash_password(password)
        session = db.get_session()
        session.add(user)
        db.safe_commit(session)
        return {'username': username}, 201

class ProcessImg(Resource):
    method_decorators = [auth.login_required]

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('img_id',
                            required=True,
                            help="img_id missing in the post body")
        args = parser.parse_args()
        img_id = args['img_id']
        lol = queue_service.put_message(os.environ['IMAGE_PROCESSOR_QUEUE'],
                                  img_id)
        logger.debug(lol)
        logger.info('img successfully uploaded and id put on queue')
        return '', 200

    def get(self, img_id):
        logger.debug('checking if img has been processed')
        session = DatabaseManager().get_session()
        query = session.query(OriginalImage).filter(OriginalImage.img_id == img_id).first()
        session.close()
        if query is not None:
            return {'finished_processing': True}
        else:
            return {'finished_processing': False}

class ImgUpload(Resource):
    method_decorators = [auth.login_required]

    def post(self):
        logger.debug('uploading img')
        parser = reqparse.RequestParser()
        parser.add_argument('file',
                            type=werkzeug.datastructures.FileStorage,
                            location='files')
        args = parser.parse_args()
        file = args['file']
        logger.debug("FILE RECEIVED")
        logger.debug(file.filename)
        if file and self._allowed_file(file.filename):
            filename = secure_filename(file.filename)
            saved = file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            logger.info('img successfully uploaded and id put on queue')
            logger.debug(saved)
            return '', 200

    def _allowed_file(self, filename):
        allowed_extensions = ['jpg']
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

class OriginalImgMatchList(Resource):
    method_decorators = [auth.login_required]

    def get(self, img_id):
        logger.debug('getting original img match list')
        session = DatabaseManager().get_session()
        query = session.query(Match).filter(Match.this_original_img_id == img_id)
        imgs = []
        distances = []
        for match in query:
            imgs.append(match.that_original_img_id)
            distances.append(match.distance_score)
        session.close()
        return {'imgs': imgs,
                'distances': distances}

class OriginalImgList(Resource):
    method_decorators = [auth.login_required]

    def get(self):
        logger.debug('getting original img list')
        session = DatabaseManager().get_session()
        query = session.query(OriginalImage).all()
        imgs = list(set(f.img_id for f in query))
        session.close()
        return {'imgs': imgs}

api.add_resource(ImgUpload, '/api/upload_image')
api.add_resource(ProcessImg, '/api/process_image/', '/api/process_image/<string:img_id>')
api.add_resource(OriginalImgMatchList, '/api/original_image_matches/<string:img_id>')
api.add_resource(OriginalImgList, '/api/original_images')
api.add_resource(RegisterUser, '/api/register_user')
api.add_resource(AuthenticationToken, '/api/token')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
