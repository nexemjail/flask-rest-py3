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
    }, code


def detail_template(value):
    return dict(detail=str(value))


def get_json(response, inner_data=False):
    parsed_json = json.loads(str(response.data, encoding='utf-8'))
    return parsed_json.get('data') if inner_data else parsed_json


def timedelta_to_hms(t):
    seconds = t.seconds
    interval_values = []
    for interval_duration in (3600, 60, 1):
        interval_length = seconds // interval_duration
        seconds -= interval_length * interval_duration
        interval_values.append(interval_length)
    return interval_values
