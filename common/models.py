from flask_login import UserMixin
from .database import decl_base, db


class User(db.Model, decl_base, UserMixin):

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(100))
    password = db.Column(db.String(50))
    events = db.relationship('Event', backref='user', lazy='dynamic')

    def __repr__(self):
        return '{id}: {email}, {first_name} {last_name}'\
            .format(id=self.id,email=self.email,
                    first_name=self.first_name, last_name=self.last_name)

    def to_json(self):
        return dict(
            id=self.id,
            email=self.email,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name
        )
