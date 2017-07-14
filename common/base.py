from flask import Blueprint
from flask_jwt import JWTError
from flask_restful import Resource, abort

from common.utils import ResponseCodes, template_response

app_bp = Blueprint('base', __name__)


class BaseResource(Resource):

    def dispatch_request(self, *args, **kwargs):
        try:
            return super(Resource, self).dispatch_request(*args, **kwargs)
        except JWTError:
            abort(ResponseCodes.UNAUTHORIZED_401, error='Invalid JWT token')

    def _not_found(self):
        return template_response(status='Error',
                                 code=ResponseCodes.NOT_FOUND_404,
                                 message='Not found'), \
               ResponseCodes.NOT_FOUND_404
