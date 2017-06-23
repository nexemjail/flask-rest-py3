from sqlalchemy.ext.declarative import declarative_base
from common import db


class Base(object):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


decl_base = declarative_base(cls=Base)
