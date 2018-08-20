from base64 import b64encode
from datetime import timedelta
from http import HTTPStatus
from io import BytesIO
from os.path import abspath
from os.path import dirname
from os.path import join
from time import sleep
from unittest import TestCase
from unittest import skipIf

from faceanalysis.api import app
from faceanalysis.models import ImageStatusEnum
from faceanalysis.models import delete_models
from faceanalysis.models import init_models
from faceanalysis.settings import ALLOWED_EXTENSIONS
from faceanalysis.settings import FACE_VECTORIZE_ALGORITHM
from faceanalysis.tasks import celery

TEST_IMAGES_ROOT = join(abspath(dirname(__file__)), 'images')
API_VERSION = '/api/v1'


class ApiTestCase(TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        init_models()
        username = 'username'
        password = 'password'
        self._register_default_user(username, password)
        token = self._get_token(username, password).get_json()['token']
        self.headers = _get_basic_auth_headers(token, 'any value')

    def tearDown(self):
        delete_models()

    @classmethod
    def tearDownClass(cls):
        celery.control.purge()

    def _register_default_user(self, username, password,
                               expected_status_code=HTTPStatus.CREATED):
        data = {'username': username, 'password': password}
        response = self.app.post(API_VERSION + '/register_user', data=data)
        self.assertEqual(response.status_code, expected_status_code.value)
        ApiTestCase.has_registered_user = True
        return response

    def _get_token(self, username, password):
        headers = _get_basic_auth_headers(username, password)
        response = self.app.get(API_VERSION + '/token',
                                headers=headers)
        self.assertEqual(response.status_code, HTTPStatus.OK.value)
        return response

    def _upload_img(self, fname, expected_status_code=HTTPStatus.OK):
        data = {'image': _load_test_image(fname)}
        response = self.app.post(API_VERSION + '/upload_image',
                                 content_type='multipart/form-data',
                                 data=data,
                                 headers=self.headers)
        self.assertEqual(response.status_code, expected_status_code.value)

        return response.get_json().get('img_id')

    def _process_img(self, img_id, expected_status_code=HTTPStatus.OK):
        data = {'img_id': img_id}
        response = self.app.post(API_VERSION + '/process_image',
                                 data=data,
                                 headers=self.headers)
        self.assertEqual(response.status_code, expected_status_code.value)
        return response

    def _get_imgs(self, expected_status_code=HTTPStatus.OK):
        response = self.app.get(API_VERSION + '/images/',
                                headers=self.headers)
        self.assertEqual(response.status_code, expected_status_code.value)
        return response

    def _get_matches(self, img_id, expected_status_code=HTTPStatus.OK):
        response = self.app.get(API_VERSION + '/image_matches/' + img_id,
                                headers=self.headers)
        self.assertEqual(response.status_code, expected_status_code.value)
        return response

    def _wait_for_img_to_finish_processing(
            self, img_id, expected_status_code=HTTPStatus.OK,
            wait_time=timedelta(minutes=1),
            polling_interval=timedelta(seconds=5)):

        while wait_time.seconds > 0:
            response = self.app.get(API_VERSION + '/process_image/' + img_id,
                                    headers=self.headers)
            self.assertEqual(response.status_code, expected_status_code.value)
            if expected_status_code == HTTPStatus.BAD_REQUEST:
                return response
            status = response.get_json()['status']
            if status == ImageStatusEnum.finished_processing.name:
                return response

            sleep(polling_interval.seconds)
            wait_time -= polling_interval

        self.fail('Waited too long for image {}'.format(img_id))

    def _test_end_to_end_with_matching_imgs(self, fnames):
        img_ids = set()
        for fname in fnames:
            img_id = self._upload_img(fname)
            img_ids.add(img_id)
            self._process_img(img_id)
            self._wait_for_img_to_finish_processing(img_id)

        imgs = self._get_imgs().get_json()['imgs']
        self.assertTrue(img_ids.issubset(set(imgs)))

        for img_id in img_ids:
            imgs = self._get_matches(img_id).get_json()['imgs']
            should_be_matches = img_ids - {img_id}
            self.assertTrue(should_be_matches.issubset(set(imgs)))
            self.assertNotIn(img_id, imgs)

    def test_end_to_end_with_one_face_per_img_that_match(self):
        fnames = {'1.jpg', '2.jpg'}
        self._test_end_to_end_with_matching_imgs(fnames)

    @skipIf(FACE_VECTORIZE_ALGORITHM == 'FaceApi',
            reason='FaceApi does not implement multiple matches')
    def test_end_to_end_with_multiple_faces_per_img_that_match(self):
        fnames = {'7.jpg', '8.jpg'}
        self._test_end_to_end_with_matching_imgs(fnames)

    @skipIf(FACE_VECTORIZE_ALGORITHM == 'FaceApi',
            reason='FaceApi does not implement multiple matches')
    def test_end_to_end_with_one_to_multiple_faces_per_img_that_match(self):
        fnames = {'3.jpg', '6.jpg'}
        self._test_end_to_end_with_matching_imgs(fnames)

    def test_upload_and_process_img_without_face(self):
        fname = '9.jpg'
        img_id = self._upload_img(fname)
        self._process_img(img_id)
        self._wait_for_img_to_finish_processing(img_id)

        imgs = self._get_imgs().get_json()['imgs']
        self.assertIn(img_id, imgs)

    def test_processing_img_that_has_not_yet_been_uploaded(self):
        img_id_not_yet_uploaded = '100'
        self._process_img(img_id_not_yet_uploaded,
                          expected_status_code=HTTPStatus.BAD_REQUEST)

    def test_upload_twice(self):
        fname = '4.jpg'
        self._upload_img(fname)
        self._upload_img(fname, expected_status_code=HTTPStatus.BAD_REQUEST)

    @skipIf(FACE_VECTORIZE_ALGORITHM == 'FaceApi',
            reason='FaceApi can process multiple times')
    def test_upload_and_process_twice(self):
        fname = '5.jpg'

        img_id = self._upload_img(fname)
        for i, fname in enumerate([fname, fname]):
            if i == 1:
                self._process_img(img_id,
                                  expected_status_code=HTTPStatus.BAD_REQUEST)
            else:
                self._process_img(img_id)
            self._wait_for_img_to_finish_processing(img_id)
            imgs = self._get_imgs().get_json()['imgs']
            self.assertIn(img_id, imgs)

    def test_end_to_end_with_different_file_formats(self):
        # test jpg && png
        self.assertIn('jpg', ALLOWED_EXTENSIONS)
        self.assertIn('png', ALLOWED_EXTENSIONS)
        fnames = {'11.jpg', '12.png'}
        self._test_end_to_end_with_matching_imgs(fnames)

    def test_network_outages(self):
        self.skipTest('Not implemented')

    def test_queue_failures(self):
        self.skipTest('Not implemented')

    def test_upload_file_not_allowed(self):
        fname = '0.txt'
        self._upload_img(fname, expected_status_code=HTTPStatus.BAD_REQUEST)

    def test_upload_arbitrarily_large_file(self):
        self.skipTest('Not implemented')


def _get_basic_auth_headers(username_or_token, password):
    encoding = username_or_token + ':' + password
    auth_encoding = b64encode(encoding.encode()).decode('ascii')
    headers = {'Authorization': 'Basic ' + auth_encoding}
    return headers


def _load_test_image(fname):
    img_path = join(TEST_IMAGES_ROOT, fname)
    with open(img_path, 'rb') as img:
        image_content = BytesIO(img.read())
        return image_content, fname
