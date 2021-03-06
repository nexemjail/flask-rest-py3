from sqlalchemy import Column, Integer
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker

from common import app


engine = create_engine(app.config.get('SQLALCHEMY_DATABASE_URI'),
                       convert_unicode=True)


db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False)
)

decl_base = declarative_base(bind=engine)
decl_base.query = db_session.query_property()


class Base(decl_base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
