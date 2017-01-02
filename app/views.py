from app import login_manager, db, api
from flask_restful import Resource, reqparse
from flask import request, session
import flask_login
from .models import User
from .utils import ResponseCodes


class Logout(Resource):
    @flask_login.login_required
    def get(self):
        flask_login.logout_user()
        session.update()
        return {'detail': 'you are logged out'}, ResponseCodes.OK


def _construct_reqparse():
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True,
                        location='json', help='Username not provided')
    parser.add_argument('password', type=str, required=True,
                        location='json', help='Password not provided')
    return parser


class Login(Resource):
    def __init__(self):
        self.reqparse = _construct_reqparse()
        super(Login, self).__init__()

    def post(self):
        data = self.reqparse.parse_args()

        user = User.query.filter_by(username=data['username'],
                                    password=data['password']).first()
        if not user:
            return {'error': 'invalid credentials'}, ResponseCodes.UNPROCESSABLE_ENTITY_422

        if not flask_login.login_user(user):
            return {'error': 'error while logging in'}, ResponseCodes.SERVER_ERROR_500

        return {'detail': 'you are logged in!'}, ResponseCodes.OK


class Register(Resource):
    def __init__(self):
        self.reqparse = _construct_reqparse()
        super(Register, self).__init__()

    def post(self):
        data = self.reqparse.parse_args()

        users_found = User.query.filter_by(username=data['username']).count()
        if users_found > 0:
            return {'error': 'user already exists'}, ResponseCodes.BAD_REQUEST_400

        user = User(username=data['username'],
                    password=data['password'])
        db.session.add(user)
        db.session.commit()

        return {'detail': 'user successfully created'}, ResponseCodes.OK


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()


class UserList(Resource):
    @flask_login.login_required
    def get(self, user_id):
        user = User.query.filter_by(id=user_id).first_or_404()
        return {'user': str(user)}, ResponseCodes.OK


api.add_resource(Register, '/register/')
api.add_resource(Login, '/login/')
api.add_resource(Logout, '/logout/')
api.add_resource(UserList, '/<int:user_id>/')
