from http import HTTPStatus
from typing import Tuple
from typing import Union

from flask import Flask
from flask import g
from flask_httpauth import HTTPBasicAuth
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from flask_restful_swagger_2 import Api
from flask_restful_swagger_2 import Schema
from flask_restful_swagger_2 import swagger
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from faceanalysis import auth
from faceanalysis import domain
from faceanalysis.domain.errors import DuplicateImage
from faceanalysis.domain.errors import ImageAlreadyProcessed
from faceanalysis.domain.errors import ImageDoesNotExist
from faceanalysis.settings import ALLOWED_EXTENSIONS

JsonResponse = Union[dict, Tuple[dict, int]]

app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app, api_version='1', api_spec_url='/api/v1/swagger', title="ICRC face analysis API")
basic_auth = HTTPBasicAuth()

ERROR_USER_ALREADY_REGISTERED = 'User already registered'
ERROR_IMAGE_ALREADY_PROCESSED = 'Image previously placed on queue'
ERROR_IMAGE_DOES_NOT_EXIST = 'Image not yet uploaded'
ERROR_BAD_IMAGE_FORMAT = ('Image upload failed: please use one of the '
                          'following extensions --> {}'
                          .format(ALLOWED_EXTENSIONS))
ERROR_DUPLICATE_IMAGE = 'Image upload failed: image previously uploaded'


# pylint: disable=no-self-use
class AuthenticationToken(Resource):
    method_decorators = [basic_auth.login_required]

    def get(self) -> JsonResponse:
        token = auth.generate_auth_token(g.user)
        return {'token': token}


class RegisterUser(Resource):
    def post(self) -> JsonResponse:
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
            auth.register_user(username, password)
        except auth.DuplicateUser:
            return {'error_msg': ERROR_USER_ALREADY_REGISTERED},\
                   HTTPStatus.BAD_REQUEST.value

        return {'username': username}, HTTPStatus.CREATED.value


class ProcessImg(Resource):
    method_decorators = [basic_auth.login_required]

    @swagger.doc({
        'tags': ['process', ],
        'description': 'Process an uploaded image',
        'parameters': [
            {
                'name': 'img_id',
                'description': 'UUID of an uploaded image',
                'in': 'body',
                'schema': {'type': 'string', }
            }
        ],
        'responses': {
            '200': {
                'description': 'OK',
                'schema': {'type': 'string', },
                'examples': {
                    'text/plain': 'OK',
                }
            },
            '400': {
                'description': 'Image not uploaded or already in queue',
                'schema': {'type': 'string', }
            },
            '500': {
                'description': "Image can't be placed in queue",
                'schema': {'type': 'string', }
            }
        }
    })
    def post(self) -> JsonResponse:
        parser = RequestParser()
        parser.add_argument('img_id',
                            required=True,
                            help="img_id missing in the post body")
        args = parser.parse_args()
        img_id = args['img_id']

        try:
            domain.process_image(img_id)
        except ImageAlreadyProcessed:
            return {'error_msg': ERROR_IMAGE_ALREADY_PROCESSED},\
                    HTTPStatus.BAD_REQUEST.value
        except ImageDoesNotExist:
            return {'error_msg': ERROR_IMAGE_DOES_NOT_EXIST},\
                   HTTPStatus.BAD_REQUEST.value

        return {'img_id': img_id}


    class ProcessImgStatusModel(Schema):
        type = 'object'
        properties = {
            'status': {
                'type': 'string',
                'description': 'Image status',
                'oneOf': [status.name for status in ImageStatusEnum],
            },
            'error_msg': {
                'type': 'string',
                'description': 'Error message (can be null)'
            },
        }
    
    @swagger.doc({
        'tags': ['status', ],
        'description': 'Get an image status from its UUID',
        'parameters': [
            {
                'name': 'img_id',
                'required': True,
                'description': 'Image UUID',
                'in': 'path',
                'type': 'string'
            }
        ],
        'responses': {
            '200': {
                'description': 'Status of the image identified by its UUID',
                'schema': ProcessImgStatusModel,
            },
            '400': {
                'description': 'Image UUID invalid',
                'schema': {'type': 'string', }
            },
        }
    })
    def get(self, img_id: str) -> JsonResponse:
        try:
            status, error = domain.get_processing_status(img_id)
        except ImageDoesNotExist:
            return {'error_msg': ERROR_IMAGE_DOES_NOT_EXIST},\
                   HTTPStatus.BAD_REQUEST.value

        return {'status': status, 'error_msg': error}


class ImgUpload(Resource):
    method_decorators = [basic_auth.login_required]

    @swagger.doc({
        'tags': ['upload', ],
        'description': 'Upload an image',
        'parameters': [
            {
                'name': 'image',
                'description': 'Uploaded image',
                'in': 'body',
                'schema': {'type': 'binary', }
            }
        ],
        'responses': {
            '200': {
                'description': 'Uploaded image UUID',
                'schema': {'type': 'string', },
                'examples': {
                    'text/plain': '<Image UUID>',
                }
            },
            '400': {
                'description': 'Image already uploaded or mime type not allowed',
                'schema': {'type': 'string', }
            },
            '500': {
                'description': 'Something wrong happened when saving the image file or updating the status',
                'schema': {'type': 'string', }
            }
        }
    })
    def post(self) -> JsonResponse:
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
            return {'error_msg': ERROR_BAD_IMAGE_FORMAT},\
                   HTTPStatus.BAD_REQUEST.value

        try:
            img_id = domain.upload_image(image.stream, filename)
        except DuplicateImage:
            return {'error_msg': ERROR_DUPLICATE_IMAGE},\
                    HTTPStatus.BAD_REQUEST.value

        return {'img_id': img_id}


class ImgMatchList(Resource):
    method_decorators = [basic_auth.login_required]

    class ImgMatchListModel(Schema):
        type = 'object'
        properties = {
            'imgs': {
                'type': 'array',
                'description': 'List of image UUID that match input image',
                'items': {
                    'type': 'string'
                }
            },
            'distances': {
                'type': 'array',
                'description': 'List of image distances corresponding to imgs array',
                'items': {
                    'type': 'number',
                    'format': 'float',
                }
            },
        }

    @swagger.doc({
        'tags': ['match', ],
        'description': 'Get all UUID of matches from an image UUID',
        'parameters': [
            {
                'name': 'img_id',
                'required': True,
                'description': 'Image UUID',
                'in': 'path',
                'type': 'string'
            }
        ],
        'responses': {
            '200': {
                'description': 'Uploaded image UUID',
                'schema': ImgMatchListModel,
            },
        }
    })
    def get(self, img_id: str) -> JsonResponse:
        images, distances = domain.lookup_matching_images(img_id)
        return {'imgs': images, 'distances': distances}


class ImgList(Resource):
    method_decorators = [basic_auth.login_required]

    @swagger.doc({
        'tags': ['list', ],
        'description': 'Get all UUID of matches from an image UUID',
        'parameters': [
            {
                'name': 'img_id',
                'required': True,
                'description': 'Image UUID',
                'in': 'path',
                'type': 'string'
            }
        ],
        'responses': {
            '200': {
                'description': 'Uploaded image UUID',
                'schema': {
                    'type': 'array',
                    'items': 'string',
                },
            },
        }
    })
    def get(self) -> JsonResponse:
        images = domain.list_images()
        return {'imgs': images}
# pylint: enable=no-self-use


@basic_auth.verify_password
def verify_password(username_or_token: str, password: str) -> bool:
    try:
        user = auth.load_user_from_auth_token(username_or_token)
    except auth.InvalidAuthToken:
        try:
            user = auth.load_user(username_or_token, password)
        except auth.AuthError:
            return False

    g.user = user
    return True


api.add_resource(ImgUpload, '/api/v1/upload_image')
api.add_resource(ProcessImg, '/api/v1/process_image/',
                 '/api/v1/process_image/<string:img_id>')
api.add_resource(ImgMatchList, '/api/v1/image_matches/<string:img_id>')
api.add_resource(ImgList, '/api/v1/images')
api.add_resource(RegisterUser, '/api/v1/register_user')
api.add_resource(AuthenticationToken, '/api/v1/token')
