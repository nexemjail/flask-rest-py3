import pytest
from common import app as application
from common.database import db_session as session, decl_base, engine


@pytest.fixture(scope='session')
def db_session():
    decl_base.metadata.create_all(engine)

    yield session

    decl_base.metadata.drop_all(engine)
    session.remove()


@pytest.fixture(scope='session')
def test_client(db_session):
    with db_session.begin(subtransactions=True) as transaction:
        yield application.test_client()
