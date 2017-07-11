import pytest
from common import app as application
from common.database import db_session as session, decl_base, engine
from common.models import User
from events.models import EVENT_STATUSES, EventStatus, Event


@pytest.yield_fixture(scope='session')
def db_session():
    decl_base.metadata.create_all()

    yield session

    decl_base.metadata.drop_all()
    session.remove()


@pytest.yield_fixture(scope='function', autouse=True)
def clearer(db_session):
    statuses = (EventStatus(status=s) for s in EVENT_STATUSES)
    db_session.add_all(statuses)
    db_session.flush()
    yield
    db_session.query(Event).delete()
    db_session.query(EventStatus).delete()
    db_session.query(User).delete()


@pytest.yield_fixture(scope='function')
def test_client(db_session):
    with db_session.begin(subtransactions=True) as t:
        yield application.test_client()
