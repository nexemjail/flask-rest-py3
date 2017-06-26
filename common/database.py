from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker

from common import db
from common.config import SQLALCHEMY_DATABASE_URI


class Base(object):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


decl_base = declarative_base(cls=Base)


engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True)

db_session = scoped_session(
    sessionmaker(
        autocommit=True,
        autoflush=True,
        bind=engine)
)

decl_base.query = db_session.query_property()
