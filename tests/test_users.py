import json
import factory

import jwt
from flask import url_for
from common import app

from common.utils import ResponseCodes

from datetime import datetime, timedelta
from freezegun import freeze_time

JWT_KEY = 'JWT '
AUTH_URL = '/auth/'

with app.test_request_context():
    REGISTER_URL = url_for('users.register')

JSON_CONTENT_TYPE = dict(
    content_type='application/json'
)


def user_detail_url(user_id):
    with app.test_request_context():
        return url_for(endpoint='users.detail', user_id=user_id)

class UserFactory(factory.DictFactory):
    email = factory.Faker('email')
    username = factory.Sequence(lambda n: 'unique_user_{0:04}'.format(n))
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.Faker('password')
    password2 = factory.SelfAttribute('password')


def fake_user_payload():
    return UserFactory()


def get_auth_response(test_client, username, password):
    payload = json.dumps(dict(
        username=username,
        password=password
    ))
    return test_client.post(AUTH_URL,
                  data=payload,
                  **JSON_CONTENT_TYPE)


def test_registration(test_client):
    user_payload = fake_user_payload()
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(user_payload),
                      **JSON_CONTENT_TYPE)
    assert response.status_code == ResponseCodes.CREATED


def test_user_already_exists(test_client):
    user_paylaod = fake_user_payload()
    payload = json.dumps(user_paylaod)
    test_client.post(REGISTER_URL,
           data=payload,
           **JSON_CONTENT_TYPE)
    response = test_client.post(REGISTER_URL,
                      data=payload,
                      **JSON_CONTENT_TYPE)
    assert response.status_code == ResponseCodes.BAD_REQUEST_400


def test_login_successful(test_client):
    user_payload = fake_user_payload()
    payload = json.dumps(user_payload)
    test_client.post(REGISTER_URL, data=payload, **JSON_CONTENT_TYPE)
    response = get_auth_response(test_client,
                                 username=user_payload['username'],
                                 password=user_payload['password'])
    assert response.status_code == ResponseCodes.OK
    assert 'token' in json.loads(str(response.data, encoding='utf8'))


def test_login_unsuccessful(test_client):
    user_payload = fake_user_payload()
    payload = user_payload.copy()
    payload['username'] = 'seed'
    payload = json.dumps(payload)
    test_client.post(REGISTER_URL, data=payload, **JSON_CONTENT_TYPE)
    response = get_auth_response(test_client,
                                 username=user_payload['username'],
                                 password=user_payload['password'])
    assert response.status_code == ResponseCodes.UNAUTHORIZED_401

def test_get_info(test_client):
    user_payload = fake_user_payload()
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(user_payload),
                      **JSON_CONTENT_TYPE)
    user = json.loads(str(response.data, encoding='utf-8')).get('data')
    user_id = user.get('id')

    response = get_auth_response(test_client,
                                 username=user_payload['username'],
                                 password=user_payload['password'])
    token = json.loads(str(response.data, encoding='utf-8'))\
        .get('token')

    response = test_client.get(user_detail_url(user_id=user_id),
                               headers={'Authorization': JWT_KEY + token})

    response_data = json.loads(str(response.data, encoding='utf-8'))\
        .get('data')

    assert response_data['username'] == user_payload['username']

def test_invalid_token(test_client):
    user_payload = fake_user_payload()
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(user_payload),
                      **JSON_CONTENT_TYPE)
    user = json.loads(str(response.data, encoding='utf-8')).get('data')
    user_id = user.get('id')

    response = get_auth_response(test_client,
                                 username=user_payload['username'],
                                 password=user_payload['password'])
    assert response.status_code == 200

    invalid_token = jwt.encode(payload={}, key='invalid_key')
    response = test_client.get(user_detail_url(user_id=user_id),
                               headers={'Authorization':
                                            JWT_KEY + str(invalid_token)})

    assert response.status_code == ResponseCodes.UNAUTHORIZED_401

def test_expired_token(test_client):
    user_payload = fake_user_payload()
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(user_payload),
                      **JSON_CONTENT_TYPE)
    user = json.loads(str(response.data, encoding='utf-8')).get('data')
    user_id = user.get('id')

    response = get_auth_response(test_client,
                                 username=user_payload['username'],
                                 password=user_payload['password'])
    token = json.loads(str(response.data, encoding='utf-8'))\
        .get('token')

    with freeze_time(datetime.now() + timedelta(seconds=320)):
        response = test_client.get(user_detail_url(user_id=user_id),
                                   headers={'Authorization': JWT_KEY + token})

        assert response.status_code == ResponseCodes.UNAUTHORIZED_401
