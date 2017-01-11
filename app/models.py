from app import db
from flask_login import UserMixin
from sqlalchemy.ext.declarative import declarative_base

base = declarative_base()


class User(db.Model, base, UserMixin):

    __tablename__ = 'flask_user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(100))
    password = db.Column(db.String(50))

    def __repr__(self):
        return '{}: {}, {} {}'.format(self.id, self.email, self.first_name, self.last_name)

    def to_json(self):
        return dict(
            id=self.id,
            email=self.email,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name
        )
