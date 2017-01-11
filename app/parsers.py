from flask_restful import reqparse


def registration_reqparser():
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True,
                        location='json', help='Username not provided')
    parser.add_argument('password', type=str, required=True,
                        location='json', help='Password not provided')
    parser.add_argument('email', type=str, required=True,
                        location='json', help='Email not provided')
    parser.add_argument('first_name', type=str, required=True,
                        location='json', help='First name not provided')
    parser.add_argument('last_name', type=str, required=True,
                        location='json', help='Last name not provided')

    return parser


def login_reqparser():
    parser = reqparse.RequestParser()
    parser.add_argument('username', type=str, required=True,
                        location='json', help='Username not provided')
    parser.add_argument('password', type=str, required=True,
                        location='json', help='Password not provided')
    return parser
