import flask_login

from flask import Flask

from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy


def get_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    db = SQLAlchemy(app)
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)
    api = Api(app)

    return app, db, api

app, db, api = get_app('common.config')

from . import models, views, jwt_functions

db.create_all(app=app)

from events import app as events_app
app.register_blueprint(events_app)

