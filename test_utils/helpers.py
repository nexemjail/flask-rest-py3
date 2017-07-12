import json
from collections import Counter
from common import app
from flask import url_for

from common.utils import ResponseCodes
from test_utils.factories import fake_user_payload

JWT_KEY = app.config['JWT_KEY']

USER_AUTH_URL = '/auth/'

JSON_CONTENT_TYPE = dict(
    content_type='application/json',
    charset='utf-8'
)

with app.test_request_context():
    REGISTER_URL = url_for('users.register')


def get_auth_response(test_client, username, password):
    payload = json.dumps(dict(
        username=username,
        password=password
    ))
    return test_client.post(USER_AUTH_URL,
                  data=payload,
                  **JSON_CONTENT_TYPE)


def get_auth_header(token):
    return {'Authorization': '{key} {token}'.format(key=JWT_KEY,
                                                    token=str(token))}


def register_and_login_user(test_client, user_payload=None):
    if user_payload is None:
        user_payload = fake_user_payload()
    response = test_client.post(REGISTER_URL,
                      data=json.dumps(user_payload),
                      **JSON_CONTENT_TYPE)
    assert response.status_code == ResponseCodes.CREATED
    response = get_auth_response(test_client=test_client,
                                 username=user_payload['username'],
                                 password=user_payload['password'])
    token = json.loads(str(response.data, encoding='utf-8'))\
        .get('token')
    return user_payload, token


def dict_contains_subset(child, parent):
    for k, v in child.items():
        parent_value = parent.get(k)
        if parent_value is None:
            return False

        if isinstance(v, list):
            child_list = v
            if Counter(child_list) != Counter(parent_value):
                return False

        elif parent_value != v:
            return False
    return True
