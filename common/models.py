from flask_login import UserMixin
from sqlalchemy.orm import relationship

from .database import Base
from sqlalchemy import Column, String


class User(Base, UserMixin):
    __tablename__ = 'users'

    username = Column(String(50), unique=True)
    email = Column(String(100), unique=True)
    first_name = Column(String(50))
    last_name = Column(String(100))
    password = Column(String(50))
    events = relationship('Event', backref='user', lazy='dynamic')

    def __repr__(self):
        return '{id}: {email}, {first_name} {last_name}'\
            .format(id=self.id,
                    email=self.email,
                    first_name=self.first_name,
                    last_name=self.last_name)

    def to_json(self):
        return dict(
            id=self.id,
            email=self.email,
            username=self.username,
            first_name=self.first_name,
            last_name=self.last_name
        )
