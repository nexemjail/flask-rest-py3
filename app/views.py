import flask_login

from app import login_manager, db, api
from flask import session
from flask_restful import Resource, reqparse

from .models import User
from .parsers import login_reqparser, registration_reqparser
from .utils import ResponseCodes, template_response

from flask_jwt import jwt_required


class Logout(Resource):
    @jwt_required
    def get(self):
        flask_login.logout_user()
        session.update()
        return {'detail': 'you are logged out'}, ResponseCodes.OK


class Login(Resource):
    def __init__(self):
        self.reqparse = login_reqparser()
        super(Login, self).__init__()

    def post(self):
        data = self.reqparse.parse_args()

        user = User.query.filter_by(email=data.get('username')).first()
        if not user:
            return template_response(status='Error',
                                     code=ResponseCodes.UNPROCESSABLE_ENTITY_422,
                                     message='Invalid credentials'),\
                   ResponseCodes.UNPROCESSABLE_ENTITY_422

        if not flask_login.login_user(user):
            return template_response(code=ResponseCodes.SERVER_ERROR_500,
                                     message='Error while logging in',
                                     status='Error'),\
                   ResponseCodes.SERVER_ERROR_500

        return template_response(status='Success',
                                 code=ResponseCodes.OK,
                                 message='Login successful'),\
            ResponseCodes.OK


class Register(Resource):
    def __init__(self):
        self.reqparse = registration_reqparser()
        super(Register, self).__init__()

    def post(self):
        data = self.reqparse.parse_args()

        users_found = User.query.filter_by(username=data['username']).count()
        if users_found > 0:
            return template_response(code=ResponseCodes.BAD_REQUEST_400,
                                     status='Error',
                                     message='User already exists'),\
                   ResponseCodes.BAD_REQUEST_400

        user = User(**data)
        db.session.add(user)
        db.session.commit()

        return template_response(status='Success',
                                 code=ResponseCodes.CREATED,
                                 message='User created',
                                 data=user.to_json()),\
            ResponseCodes.CREATED


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


class UserList(Resource):
    @jwt_required
    def get(self, user_id):
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return template_response(status='Error',
                                     code=ResponseCodes.NOT_FOUND_404,
                                     message='Not found'), \
                ResponseCodes.NOT_FOUND_404

        return template_response(status='OK',
                                 code=ResponseCodes.OK,
                                 data=user.to_json()),\
            ResponseCodes.OK

api.add_resource(Register, '/register/')
api.add_resource(Login, '/login/')
api.add_resource(Logout, '/logout/')
api.add_resource(UserList, '/<int:user_id>/')
