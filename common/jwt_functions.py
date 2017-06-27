from common import app
from flask import jsonify
from flask_jwt import JWT
from werkzeug.security import safe_str_cmp

from .models import User


def auth_response_handler(access_token, identity):
    return jsonify({'token': access_token.decode('utf-8')})


def authenticate(username, password):
    user = User.query.filter_by(username=username).first()
    if user and safe_str_cmp(user.password.encode('utf-8'),
                             password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return User.query.get(user_id)

jwt = JWT(app, authenticate, identity)
jwt.auth_response_handler(auth_response_handler)
