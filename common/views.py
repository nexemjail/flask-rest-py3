from flask import Blueprint
from flask_jwt import jwt_required, current_identity
from flask_restful import Api

from common.base import BaseResource
from common.database import db_session
from .models import User
from .parsers import registration_reqparser
from .utils import ResponseCodes, template_response

app_bp = Blueprint('users', __name__)
api = Api(app_bp)


class Register(BaseResource):
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


class UserDetail(BaseResource):
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

api.add_resource(Register, '/users/user/register/', endpoint='register')
api.add_resource(UserDetail, '/users/user/<int:user_id>/', endpoint='detail')
