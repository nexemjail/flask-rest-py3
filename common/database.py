from sqlalchemy.engine import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.scoping import scoped_session
from sqlalchemy.orm.session import sessionmaker

from common.config import SQLALCHEMY_DATABASE_URI

decl_base = declarative_base()

engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True)

db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=True,
        bind=engine),
)

decl_base.query = db_session.query_property()
