import os
import json
import unittest
from base64 import b64encode
from io import BytesIO
from time import sleep
from requests import codes
from .. import api
from ..models.database_manager import DatabaseManager
from ..models.models import init_models


class ApiTestCase(unittest.TestCase):
    has_registered_user = False

    def setUp(self):
        api.app.testing = True
        self.app = api.app.test_client()
        self.db = DatabaseManager()
        init_models(self.db.engine)

        if not ApiTestCase.has_registered_user:
            self._register_default_user()

        token_response = self._get_token()
        self.token = json.loads(token_response.get_data(as_text=True))['token']

    def _register_default_user(self, expected_status_code=codes.CREATED):
        data = {'username': 'username',
                'password': 'password'}
        response = self.app.post('/api/register_user', data=data)
        self.assertEqual(response.status_code, expected_status_code)
        ApiTestCase.has_registered_user = True
        return response

    def _get_token(self):
        headers = self._get_basic_auth_headers()
        response = self.app.get('/api/token', headers=headers)
        self.assertEqual(response.status_code, codes.OK)
        return response

    def _upload_img(self, fname, expected_status_code=codes.OK):
        headers = self._get_basic_auth_headers()
        img_path = self._get_img_path(fname)
        img = self._get_img(img_path, fname)
        data = {'image': img}
        response = self.app.post('/api/upload_image',
                                 content_type='multipart/form-data',
                                 data=data,
                                 headers=headers)
        self.assertEqual(response.status_code, expected_status_code)
        return response

    def _process_img(self, img_id, expected_status_code=codes.OK):
        headers = self._get_basic_auth_headers()
        data = {'img_id': img_id}
        response = self.app.post('/api/process_image',
                                 data=data,
                                 headers=headers)
        self.assertEqual(response.status_code, expected_status_code)
        return response

    def _get_imgs(self, expected_status_code=codes.OK):
        headers = self._get_basic_auth_headers()
        response = self.app.get('/api/images/',
                                headers=headers)
        self.assertEqual(response.status_code, expected_status_code)
        return response

    def _get_matches(self, img_id, expected_status_code=codes.OK):
        headers = self._get_basic_auth_headers()
        response = self.app.get('/api/image_matches/' + img_id,
                                headers=headers)
        self.assertEqual(response.status_code, expected_status_code)
        return response

    def _wait_for_img_to_finish_processing(self,
                                           img_id,
                                           expected_status_code=codes.OK):
        headers = self._get_basic_auth_headers()
        while True:
            response = self.app.get('/api/process_image/' + img_id,
                                    headers=headers)
            self.assertEqual(response.status_code, expected_status_code)
            data = json.loads(response.get_data(as_text=True))
            if data['finished_processing']:
                return response
            sleep(3)

    def _test_end_to_end_with_matching_imgs(self, fnames):
        img_ids = set()
        for fname in fnames:
            index_of_period = fname.find('.')
            img_id = fname[:index_of_period]
            img_ids.add(img_id)
            self._upload_img(fname)
            self._process_img(img_id)
            self._wait_for_img_to_finish_processing(img_id)

        imgs_response = self._get_imgs()
        imgs_data = json.loads(imgs_response.get_data(as_text=True))
        self.assertTrue(img_ids.issubset(set(imgs_data['imgs'])))

        for img_id in img_ids:
            matches_response = self._get_matches(img_id)
            matches_data = json.loads(matches_response.get_data(as_text=True))
            should_be_matches = img_ids - set([img_id])
            self.assertTrue(should_be_matches.issubset(
                set(matches_data['imgs'])))
            self.assertNotIn(img_id, matches_data['imgs'])

    def test_end_to_end_with_one_face_per_img_that_match(self):
        fnames = {'1.jpg', '2.jpg'}
        self._test_end_to_end_with_matching_imgs(fnames)

    def test_end_to_end_with_multiple_faces_per_img_that_match(self):
        fnames = {'7.jpg', '8.jpg'}
        self._test_end_to_end_with_matching_imgs(fnames)

    def test_end_to_end_with_one_to_multiple_faces_per_img_that_match(self):
        fnames = {'3.jpg', '6.jpg'}  # CANNOT REUSE PHOTOS
        # self._test_end_to_end_with_matching_imgs(fnames)
        pass

    def test_upload_and_process_img_without_face(self):
        fname = '9.jpg'
        img_id = fname[0]
        self._upload_img(fname)
        self._process_img(img_id)
        self._wait_for_img_to_finish_processing(img_id)

        imgs_response = self._get_imgs()
        imgs_data = json.loads(imgs_response.get_data(as_text=True))
        self.assertIn(img_id, imgs_data['imgs'])

    @unittest.skip("INFINITE LOOP")
    def test_processing_img_that_has_not_yet_been_uploaded(self):
        pass

    def test_upload_twice(self):
        fname = '4.jpg'
        self._upload_img(fname)

    def test_upload_and_process_twice(self):
        fname = '5.jpg'
        img_id = fname[0]

        self._upload_img(fname)
        for fname in [fname, fname]:
            self._process_img(img_id)
            self._wait_for_img_to_finish_processing(img_id)

            imgs_response = self._get_imgs()
            imgs_data = json.loads(imgs_response.get_data(as_text=True))
            self.assertIn(img_id, imgs_data['imgs'])

    def test_end_to_end_with_different_file_formats(self):
        # test jpg && png
        file_extensions = os.environ['ALLOWED_IMAGE_FILE_EXTENSIONS'].lower()
        allowed_file_extensions = file_extensions.split('_')
        self.assertIn('jpg', allowed_file_extensions)
        self.assertIn('png', allowed_file_extensions)
        fnames = {'11.jpg', '12.png'}
        self._test_end_to_end_with_matching_imgs(fnames)

    def test_network_outages(self):
        pass

    def test_queue_failures(self):
        pass

    def test_upload_file_not_allowed(self):
        fname = '0.txt'
        self._upload_img(fname, codes.BAD_REQUEST)

    def test_upload_arbitrarily_large_file(self):
        pass

    # hlper utility methods
    def _get_basic_auth_headers(self):
        # auth_encoding = b64encode(b"%s:%s" % (self.username.encode(),
        #                                      self.password.encode()))
        auth_encoding = b64encode(b'username:password').decode('ascii')
        headers = {'Authorization': 'Basic ' + auth_encoding}
        return headers

    def _get_img(self, img_path, fname):
        with open(img_path, 'rb') as img:
            image = (BytesIO(img.read()), fname)
            return image

    def _get_img_path(self, fname):
        dirname = os.path.dirname(os.path.abspath(__file__))
        img_path = os.path.join(os.path.join(dirname, 'images'), fname)
        return img_path
