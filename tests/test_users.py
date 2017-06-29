import json
from common.utils import ResponseCodes

from datetime import datetime, timedelta
from freezegun import freeze_time

JWT_KEY = 'JWT '
AUTH_URL = '/auth/'
REGISTER_URL = '/users/user/register/'
USER_INFO_URL = '/users/user/{}/'
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


def get_auth_response(test_client):
    payload = json.dumps(dict(
        username=USER_PAYLOAD['username'],
        password=USER_PAYLOAD['password']
    ))
    return test_client.post(AUTH_URL,
                  data=payload,
                  **JSON_CONTENT_TYPE)


def test_registration(test_client):
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(USER_PAYLOAD),
                      **JSON_CONTENT_TYPE)
    assert response.status_code == ResponseCodes.CREATED


def test_user_already_exists(test_client):
    payload = json.dumps(USER_PAYLOAD)
    test_client.post(REGISTER_URL,
           data=payload,
           **JSON_CONTENT_TYPE)
    response = test_client.post(REGISTER_URL,
                      data=payload,
                      **JSON_CONTENT_TYPE)
    assert response.status_code == ResponseCodes.BAD_REQUEST_400


def test_login_successful(test_client):
    payload = json.dumps(USER_PAYLOAD)
    test_client.post(REGISTER_URL, data=payload, **JSON_CONTENT_TYPE)
    response = get_auth_response(test_client)
    assert response.status_code == ResponseCodes.OK
    assert 'token' in json.loads(str(response.data, encoding='utf8'))


def test_login_unsuccessful(test_client):
    payload = USER_PAYLOAD.copy()
    payload['username'] = 'seed'
    payload = json.dumps(payload)
    test_client.post(REGISTER_URL, data=payload, **JSON_CONTENT_TYPE)
    response = get_auth_response(test_client)
    assert response.status_code == ResponseCodes.UNAUTHORIZED_401

def test_get_info(test_client):
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(USER_PAYLOAD),
                      **JSON_CONTENT_TYPE)
    user = json.loads(str(response.data, encoding='utf-8')).get('data')
    user_id = user.get('id')

    response = get_auth_response(test_client)
    token = json.loads(str(response.data, encoding='utf-8'))\
        .get('token')

    response = test_client.get(USER_INFO_URL.format(user_id), headers={
        'Authorization': JWT_KEY + token})

    response_data = json.loads(str(response.data, encoding='utf-8'))\
        .get('data')

    assert response_data['username'] == USER_PAYLOAD['username']

def test_invalid_token(test_client):
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(USER_PAYLOAD),
                      **JSON_CONTENT_TYPE)
    user = json.loads(str(response.data, encoding='utf-8')).get('data')
    user_id = user.get('id')

    response = get_auth_response(test_client)
    token = json.loads(str(response.data, encoding='utf-8'))\
        .get('token')

    response = test_client.get(USER_INFO_URL.format(user_id), headers={
        'Authorization': JWT_KEY + token + 'feed'})

    assert response.status_code == ResponseCodes.UNAUTHORIZED_401

def test_expired_token(test_client):
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(USER_PAYLOAD),
                      **JSON_CONTENT_TYPE)
    user = json.loads(str(response.data, encoding='utf-8')).get('data')
    user_id = user.get('id')

    response = get_auth_response(test_client)
    token = json.loads(str(response.data, encoding='utf-8'))\
        .get('token')

    with freeze_time(datetime.now() + timedelta(seconds=320)):
        response = test_client.get(USER_INFO_URL.format(user_id), headers={
            'Authorization': JWT_KEY + token})

        assert response.status_code ==ResponseCodes.UNAUTHORIZED_401
