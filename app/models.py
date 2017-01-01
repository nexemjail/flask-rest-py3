from app import db
from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base

base = declarative_base()


class User(base, UserMixin):

    __tablename__ = 'flask_user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))

    def __repr__(self):
        return '{}: {}'.format(self.id, self.username)
