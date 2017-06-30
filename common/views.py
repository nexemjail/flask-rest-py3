from flask.ext.jwt import current_identity

from common import db
from flask_restful import Resource, Api

from .models import User
from .parsers import login_reqparser, registration_reqparser
from .utils import ResponseCodes, template_response

from flask_jwt import jwt_required
from flask import Blueprint, jsonify
from common.database import db_session

app_bp = Blueprint('users', __name__)
api = Api(app_bp)

class Register(Resource):
    def __init__(self):
        self.reqparse = registration_reqparser()
        super(Register, self).__init__()

    def post(self):
        data = self.reqparse.parse_args()

        users_found = db_session.query(User)\
            .filter(User.username==data['username'])\
            .count()
        if users_found > 0:
            return template_response(code=ResponseCodes.BAD_REQUEST_400,
                                     status='Error',
                                     message='User already exists'),\
                   ResponseCodes.BAD_REQUEST_400

        user = User(**data)
        db_session.add(user)
        db_session.flush()

        return template_response(status='Success',
                                 code=ResponseCodes.CREATED,
                                 message='User created',
                                 data=user.to_json()),\
            ResponseCodes.CREATED


class UserDetail(Resource):
    @jwt_required()
    def get(self, user_id):
        user = User.query.filter_by(id=user_id).first()
        if not user or current_identity != user:
            return template_response(status='Error',
                                     code=ResponseCodes.NOT_FOUND_404,
                                     message='Not found'), \
                ResponseCodes.NOT_FOUND_404

        return template_response(status='OK',
                                 code=ResponseCodes.OK,
                                 data=user.to_json()),\
            ResponseCodes.OK

api.add_resource(Register, '/users/user/register/')
api.add_resource(UserDetail, '/users/user/<int:user_id>/')


# from flask_jwt import JWTError
# from jwt.exceptions import InvalidTokenError


@app_bp.errorhandler(Exception)
def handle_invalid_token_error(error):
    response = jsonify({'error': 'Invalid token'})
    response.status_code = ResponseCodes.UNAUTHORIZED_401
    return response

# app_bp.register_error_handler(JWTError, handle_invalid_token_error)
# app_bp.register_error_handler(InvalidTokenError, handle_invalid_token_error)
