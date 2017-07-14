import pytest
from common import app as application
from common.database import db_session as session, decl_base, sessionmaker
from common.models import User
from events.models import EVENT_STATUSES, EventStatus, Event, Label, \
    LabelsEvents


@pytest.yield_fixture(scope='session')
def db_session():
    decl_base.metadata.create_all()

    yield session
    sessionmaker.close_all()
    decl_base.metadata.drop_all()
    session.remove()


def setup(db_session):
    statuses = (EventStatus(status=s) for s in EVENT_STATUSES)
    db_session.add_all(statuses)
    db_session.commit()


def clean(db_session):
    db_session.query(LabelsEvents).delete(synchronize_session=False)
    db_session.query(Label).delete(synchronize_session=False)
    db_session.query(Event).delete(synchronize_session=False)
    db_session.query(EventStatus).delete(synchronize_session=False)
    db_session.query(User).delete(synchronize_session=False)


@pytest.yield_fixture(scope='function')
def transaction(db_session):
    setup(db_session)
    yield db_session.begin_nested()
    db_session.rollback()
    clean(db_session)

@pytest.yield_fixture(scope='function')
def test_client():
    yield application.test_client()
