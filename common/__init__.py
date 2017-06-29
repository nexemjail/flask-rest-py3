import os
import flask_login

from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow


def get_app(config):
    app = Flask(__name__)
    app.config.from_object(config)

    db = SQLAlchemy(app)
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)
    api = Api(app)
    ma = Marshmallow(app)

    return app, db, api, ma


def create_all(app, db):
    from . import models, views, jwt_functions
    db.create_all(app=app)
    db.session.commit()


def register_blueprints(app):
    from .views import api_bp as users_blueprint
    app.register_blueprint(users_blueprint)

    from events import blueprint as events_blueprint
    app.register_blueprint(events_blueprint)

config_file = 'common.test_config' if os.environ.get('APP_TESTING') else \
    'common.config'
app, db, api, ma = get_app(config_file)
register_blueprints(app)