import unittest

from app import get_app

from .models import User
from .utils import ResponseCodes


class FlaskTests(unittest.TestCase):
    BASE_URL = 'http://192.168.33.10'
    JWT_KEY = 'JWT '
    AUTH_URL = '/auth/'
    REGISTER_URL = '/register/'

    USER_PAYLOAD = {
        "email": "alex228@gmail.com",
        "username": "alex228@gmail.com",
        "first_name": "Alex",
        "last_name": "Sh",
        "password": "djangodjango",
        "password2": "djangodjango"
    }

    def get_auth_response(self):
        return self.client.post(self.AUTH_URL, {
            'username': self.USER_PAYLOAD['username'],
            'password': self.USER_PAYLOAD['password']
        })

    def setUp(self):
        import flask_login
        from flask_sqlalchemy import SQLAlchemy
        from flask_restful import Api

        self.app = get_app('app.test_config')
        self.db = SQLAlchemy(self.app)
        login_manager = flask_login.LoginManager()
        login_manager.init_app(self.app)
        self.api = Api(self.app)

        from app import models, views, jwt_functions

        self.db.create_all(app=self.app)
        self.client = self.app.test_client()
        self.app.run('0.0.0.0', 9000)

    def tearDown(self):
        self.db.drop_all()
        self.db.session.remove()

    def test_registration(self):

        response = self.client.post(self.REGISTER_URL, data=self.USER_PAYLOAD,
                                    headers={'Content-Type': 'application/json'})

        self.assertEqual(response.status_code, ResponseCodes.CREATED)

