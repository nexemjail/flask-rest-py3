import unittest

import json
from wsgiref.headers import Headers

from app import get_app
from app.models import User
from app.utils import ResponseCodes


class FlaskTests(unittest.TestCase):
    JWT_KEY = 'JWT '
    AUTH_URL = '/auth/'
    REGISTER_URL = '/register/'
    JSON_CONTENT_TYPE = dict(
        content_type='application/json'
    )

    USER_PAYLOAD = dict(
        email="alex228@gmail.com",
        username="alex228@gmail.com",
        first_name="Alex",
        last_name="Sh",
        password="djangodjango",
        password2="djangodjango"
    )

    def get_auth_response(self):
        with self.app.test_client() as c:
            payload = json.dumps(dict(
                username=self.USER_PAYLOAD['username'],
                password=self.USER_PAYLOAD['password']
            ))
            return c.post(self.AUTH_URL, data=payload, **self.JSON_CONTENT_TYPE)

    def setUp(self):
        from app import app, db, api
        from app import models, views, jwt_functions

        self.app = app
        self.app.config.from_object('app.test_config')
        self.db = db
        self.api = api

        self.db.create_all(app=self.app)

    def tearDown(self):
        self.db.session.remove()
        self.db.drop_all()

    def test_registration(self):
        with self.app.test_client() as c:
            response = c.post(self.REGISTER_URL, data=json.dumps(self.USER_PAYLOAD),
                              **self.JSON_CONTENT_TYPE)
            self.assertEqual(response.status_code, ResponseCodes.CREATED)

    def test_user_already_exists(self):
        with self.app.test_client() as c:
            payload = json.dumps(self.USER_PAYLOAD)
            c.post(self.REGISTER_URL, data=payload, **self.JSON_CONTENT_TYPE)
            response = c.post(self.REGISTER_URL, data=payload, **self.JSON_CONTENT_TYPE)
            self.assertEqual(response.status_code, ResponseCodes.BAD_REQUEST_400)

    def test_login_successful(self):
        with self.app.test_client() as c:
            payload = json.dumps(self.USER_PAYLOAD)
            c.post(self.REGISTER_URL, data=payload, **self.JSON_CONTENT_TYPE)
            response = self.get_auth_response()
            self.assertEqual(response.status_code, ResponseCodes.OK)
            self.assertTrue('token' in json.loads(str(response.data, encoding='utf8')))

    def test_get_info(self):
        with self.app.test_client() as c:

            response = c.post(self.REGISTER_URL, data=json.dumps(self.USER_PAYLOAD), **self.JSON_CONTENT_TYPE)
            user = json.loads(str(response.data, encoding='utf-8')).get('data')
            user_id = user.get('id')

            response = self.get_auth_response()
            token = json.loads(str(response.data, encoding='utf-8')).get('token')

            h = Headers()
            h.add_header('Authorization', self.JWT_KEY + token)

            response = c.get('/{}/'.format(user_id), headers=h)

            response_data = json.loads(str(response.data))

            self.assertEqual(response_data['username'], self.USER_PAYLOAD['username'])

    # def test_invalid_token(self):
    #     self.client.post('/register/', self.sample_user_payload)
    #     response = self._get_auth_response()
    #     token = response.data['token']
    #
    #     user_id = User.objects.get(username=self.sample_user_payload['username']).id
    #
    #     response = self.client.get('/{}/'.format(user_id), HTTP_AUTHORIZATION=self.JWT_KEY + token + 'seed')
    #
    #     self.assertEqual(response.status_code, HTTP_403_FORBIDDEN)
    #
    # def test_expiration(self):
    #
    #     now = datetime.now()
    #     self.client.post('/register/', self.sample_user_payload)
    #     response = self._get_auth_response()
    #     token = response.data['token']
    #
    #     with freeze_time(now + timedelta(seconds=320)):
    #         user_id = User.objects.get(username=self.sample_user_payload['username']).id
    #
    #         response = self.client.get('/{}/'.format(user_id), HTTP_AUTHORIZATION=self.JWT_KEY + token)
    #
    #         self.assertEqual(response.status_code, 403)


if __name__ == '__main__':
    unittest.main()