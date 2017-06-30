import pytest
from common import app as application
from common.database import db_session as session, decl_base, engine
from common.models import User


@pytest.yield_fixture(scope='session')
def db_session():
    decl_base.metadata.create_all()

    yield session

    decl_base.metadata.drop_all()
    session.remove()

@pytest.yield_fixture(scope='function')
def clearer(db_session):
    db_session.query(User).delete()
    yield
    db_session.query(User).delete()

@pytest.yield_fixture(scope='function')
def test_client(db_session, clearer):
    with db_session.begin(subtransactions=True) as t:
        yield application.test_client()
