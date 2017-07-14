from flask import Blueprint, request
from flask_jwt import jwt_required, current_identity
from flask_restful import Api

from common.base import BaseResource
from common.database import db_session
from common.serializers import UserRegisterSchema
from common.utils import bytes_to_str
from .models import User
from .utils import ResponseCodes, template_response

app_bp = Blueprint('users', __name__)
api = Api(app_bp)


class Register(BaseResource):
    def post(self):
        data, errors = UserRegisterSchema().loads(bytes_to_str(request.data))
        if errors:
            return self._bad_request(errors)

        users_found = db_session.query(User)\
            .filter(User.username==data['username'])\
            .count()
        if users_found > 0:
            return template_response(code=ResponseCodes.BAD_REQUEST_400,
                                     status='Error',
                                     message='User already exists')

        user = User(**data)
        db_session.add(user)
        db_session.commit()

        return template_response(status='Success',
                                 code=ResponseCodes.CREATED,
                                 message='User created',
                                 data=user.to_json())

    def _bad_request(self, errors):
        return template_response(
            status='Errored',
            code=ResponseCodes.BAD_REQUEST_400,
            data=errors
        )

class UserDetail(BaseResource):
    @jwt_required()
    def get(self, user_id):
        user = User.query.filter_by(id=user_id).first()

        if not user or current_identity != user:
            return self._not_found()

        return template_response(status='OK',
                                 code=ResponseCodes.OK,
                                 data=user.to_json())


api.add_resource(Register, '/users/user/register/', endpoint='register')
api.add_resource(UserDetail, '/users/user/<int:user_id>/', endpoint='detail')
