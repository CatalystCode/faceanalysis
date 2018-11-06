from http import HTTPStatus
from typing import Tuple
from typing import Union

from flask import Flask
from flask_restful import Api
from flask_restful import Resource
from flask_restful.reqparse import RequestParser
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from faceanalysis import domain
from faceanalysis.domain.errors import DuplicateImage
from faceanalysis.domain.errors import ImageAlreadyProcessed
from faceanalysis.domain.errors import ImageDoesNotExist
from faceanalysis.settings import ALLOWED_MIMETYPES

JsonResponse = Union[dict, Tuple[dict, int]]

app = Flask(__name__)
app.url_map.strict_slashes = False
api = Api(app)

ERROR_USER_ALREADY_REGISTERED = 'User already registered'
ERROR_IMAGE_ALREADY_PROCESSED = 'Image previously placed on queue'
ERROR_IMAGE_DOES_NOT_EXIST = 'Image not yet uploaded'
ERROR_BAD_IMAGE_FORMAT = ('Image upload failed: please use one of the '
                          'following MIME types --> {}'
                          .format(ALLOWED_MIMETYPES))
ERROR_DUPLICATE_IMAGE = 'Image upload failed: image previously uploaded'


# pylint: disable=no-self-use
class ProcessImg(Resource):
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

    def get(self, img_id: str) -> JsonResponse:
        try:
            status, error = domain.get_processing_status(img_id)
        except ImageDoesNotExist:
            return {'error_msg': ERROR_IMAGE_DOES_NOT_EXIST},\
                   HTTPStatus.BAD_REQUEST.value

        return {'status': status, 'error_msg': error}


class ImgUpload(Resource):
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

        if image.mimetype not in ALLOWED_MIMETYPES:
            return {'error_msg': ERROR_BAD_IMAGE_FORMAT},\
                   HTTPStatus.BAD_REQUEST.value

        try:
            img_id = domain.upload_image(image.stream, filename)
        except DuplicateImage:
            return {'error_msg': ERROR_DUPLICATE_IMAGE},\
                    HTTPStatus.BAD_REQUEST.value

        return {'img_id': img_id}


class ImgMatchList(Resource):
    def get(self, img_id: str) -> JsonResponse:
        images, distances = domain.lookup_matching_images(img_id)
        return {'imgs': images, 'distances': distances}


class ImgList(Resource):
    def get(self) -> JsonResponse:
        images = domain.list_images()
        return {'imgs': images}
# pylint: enable=no-self-use


api.add_resource(ImgUpload, '/api/v1/upload_image')
api.add_resource(ProcessImg, '/api/v1/process_image/',
                 '/api/v1/process_image/<string:img_id>')
api.add_resource(ImgMatchList, '/api/v1/image_matches/<string:img_id>')
api.add_resource(ImgList, '/api/v1/images')
