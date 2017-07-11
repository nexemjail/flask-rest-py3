import json


class ResponseCodes(enumerate):
    OK = 200
    CREATED = 201
    REDIRECT = 300
    BAD_REQUEST_400 = 400
    UNAUTHORIZED_401 = 401
    FORBIDDEN_403 = 403
    NOT_FOUND_404 = 404
    UNPROCESSABLE_ENTITY_422 = 422
    SERVER_ERROR_500 = 500


def template_response(status=None,
                      code=None,
                      message=None,
                      data=None):
    return {
        'status': status,
        'code': code,
        'message': message,
        'data': data
    }


def detail_template(value):
    return dict(detail=str(value))


def get_json(response):
    return json.loads(str(response.data, encoding='utf-8'))
