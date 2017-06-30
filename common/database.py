from abc import ABCMeta
from sqlalchemy import Column, Integer
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy.sql.schema import MetaData

from common import app


engine = create_engine(app.config.get('SQLALCHEMY_DATABASE_URI'),
                       convert_unicode=True)


db_session = scoped_session(
    sessionmaker(
        autocommit=True,
        autoflush=False,
        bind=engine),
)

decl_base = declarative_base(bind=engine)


class Base(decl_base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)

decl_base.query = db_session.query_property()
