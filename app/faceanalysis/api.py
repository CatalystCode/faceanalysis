from http import HTTPStatus

from flask import Flask
from flask import g
from flask_restful import Api
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from faceanalysis import auth
from faceanalysis import domain
from faceanalysis.settings import ALLOWED_EXTENSIONS

app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app)


# pylint: disable=no-self-use
class AuthenticationToken(Resource):
    method_decorators = [auth.login_required]

    def get(self):
        token = g.user.generate_auth_token()
        return {'token': token.decode('ascii')}


class RegisterUser(Resource):
    def post(self):
        parser = RequestParser()
        parser.add_argument('username',
                            required=True,
                            help='username parameter missing in post body')
        parser.add_argument('password',
                            required=True,
                            help='password parameter missing in post body')
        args = parser.parse_args()
        username = args['username']
        password = args['password']

        try:
            username = auth.register_user(username, password)
        except auth.DuplicateUser:
            return 'User already registered', HTTPStatus.BAD_REQUEST.value

        return {'username': username}, HTTPStatus.CREATED.value


class ProcessImg(Resource):
    method_decorators = [auth.login_required]

    def post(self):
        parser = RequestParser()
        parser.add_argument('img_id',
                            required=True,
                            help="img_id missing in the post body")
        args = parser.parse_args()
        img_id = args['img_id']

        try:
            domain.process_image(img_id)
        except domain.ImageAlreadyProcessed:
            return ('Image previously placed on queue',
                    HTTPStatus.BAD_REQUEST.value)
        except domain.ImageDoesNotExist:
            return 'Image not yet uploaded', HTTPStatus.BAD_REQUEST.value

        return 'OK', HTTPStatus.OK.value

    def get(self, img_id):
        try:
            status, error = domain.get_processing_status(img_id)
        except domain.ImageDoesNotExist:
            return 'Image not yet uploaded', HTTPStatus.BAD_REQUEST.value

        return {'status': status, 'error_msg': error}


class ImgUpload(Resource):
    method_decorators = [auth.login_required]

    def post(self):
        parser = RequestParser()
        parser.add_argument('image',
                            type=FileStorage,
                            required=True,
                            help="image missing in post body",
                            location='files')
        args = parser.parse_args()
        image = args['image']
        filename = secure_filename(image.filename)

        if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            return ('Image upload failed: please use one of the '
                    'following extensions --> {}'
                    .format(ALLOWED_EXTENSIONS)), HTTPStatus.BAD_REQUEST.value

        try:
            domain.upload_image(image.stream, filename)
        except domain.DuplicateImage:
            return ('Image upload failed: image previously uploaded',
                    HTTPStatus.BAD_REQUEST.value)

        return 'OK', HTTPStatus.OK.value


class ImgMatchList(Resource):
    method_decorators = [auth.login_required]

    def get(self, img_id):
        images, distances = domain.lookup_matching_images(img_id)
        return {'imgs': images, 'distances': distances}


class ImgList(Resource):
    method_decorators = [auth.login_required]

    def get(self):
        images = domain.list_images()
        return {'imgs': images}
# pylint: enable=no-self-use


api.add_resource(ImgUpload, '/api/v1/upload_image')
api.add_resource(ProcessImg, '/api/v1/process_image/',
                 '/api/v1/process_image/<string:img_id>')
api.add_resource(ImgMatchList, '/api/v1/image_matches/<string:img_id>')
api.add_resource(ImgList, '/api/v1/images')
api.add_resource(RegisterUser, '/api/v1/register_user')
api.add_resource(AuthenticationToken, '/api/v1/token')
