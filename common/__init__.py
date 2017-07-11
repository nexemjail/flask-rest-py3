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
    # import is used to register /auth/ endpoint
    from . import jwt_functions
    from .views import app_bp as users_blueprint
    from .base import app_bp as base_bp
    from events import blueprint as events_blueprint

    app.register_blueprint(users_blueprint, )
    app.register_blueprint(events_blueprint)
    app.register_blueprint(base_bp)

config_mapping = {
    'CI': 'common.ci_config',
    'DEV': 'common.config',
    'TEST': 'common.test_config'
}

run_mode = os.environ.get('RUN_MODE')
if run_mode not in config_mapping:
    raise Exception('Invalid run mode specified')

config_file = config_mapping[run_mode]
app, db, api, ma = get_app(config_file)
register_blueprints(app)
