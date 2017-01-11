import flask_login

from flask import Flask

from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object('app.config')
db = SQLAlchemy(app)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
api = Api(app)

from app import models, views

db.create_all(app=app)


