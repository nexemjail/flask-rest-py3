import json

import jwt
from flask import url_for
from common import app

from common.utils import ResponseCodes

from datetime import datetime, timedelta
from freezegun import freeze_time

from test_utils.factories import fake_user_payload
from test_utils.helpers import REGISTER_URL, JSON_CONTENT_TYPE, \
    get_auth_response, get_auth_header

JWT_KEY = app.config['JWT_KEY']
AUTH_URL = app.config['JWT_AUTH_URL_RULE']


def user_detail_url(user_id):
    with app.test_request_context():
        return url_for(endpoint='users.detail', user_id=user_id)


def test_registration(test_client):
    user_payload = fake_user_payload()
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(user_payload),
                      **JSON_CONTENT_TYPE)
    assert response.status_code == ResponseCodes.CREATED


def test_user_already_exists(test_client):
    user_payload = fake_user_payload()
    payload = json.dumps(user_payload)
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
                               headers=get_auth_header(token))
    assert response.status_code == ResponseCodes.OK

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
                               headers=get_auth_header(invalid_token))

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
                                   headers=get_auth_header(token))

        assert response.status_code == ResponseCodes.UNAUTHORIZED_401
