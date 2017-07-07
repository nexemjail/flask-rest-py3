import datetime

import factory
import pytest
from dateutil.relativedelta import relativedelta

from factory import fuzzy

from common.database import db_session
from common.models import User
from events.models import Label, EventStatus, EVENT_CHOICES, Event, EventMedia


@pytest.fixture
def label_factory(db_session):
    class EventLabelFactory(factory.alchemy.SQLAlchemyModelFactory):
        class Meta:
            model = Label
            sqlalchemy_session = db_session

        name = factory.Faker('word')

    return EventLabelFactory


@pytest.fixture
def event_status_factory(db_session):
    class EventStatusFactory(factory.alchemy.SQLAlchemyModelFactory):
        class Meta:
            model = EventStatus
            sqlalchemy_session = db_session

        status = fuzzy.FuzzyChoice(EVENT_CHOICES)

    return EventStatusFactory


@pytest.fixture
def user_factory(db_session):
    class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
        class Meta:
            model = User
            sqlalchemy_session = db_session

        username = factory.Sequence(lambda n: 'unique_user_{0:04}'.format(n))
        email = factory.Sequence(lambda n: 'unique_email_{0:04}'
                                              '@mail.com'.format(n))

        first_name = factory.Faker('name')
        last_name = factory.Faker('name')
        password = factory.Faker('password')

    return UserFactory


@pytest.fixture
def event_factory(db_session):
    class EventFactory(factory.alchemy.SQLAlchemyModelFactory):
        class Meta:
            model = Event
            sqlalchemy_session = db_session

        user = factory.SubFactory(user_factory())
        description = factory.Faker('text')
        start = fuzzy.FuzzyDateTime(datetime.datetime.now())
        @factory.lazy_attribute
        def end(self):
            return factory.LazyAttribute(
                lambda x: self.start + relativedelta(seconds=1)
            ).fuzz()

        # TODO: handle periods
        periodic = False
        period = None
        next_notification = None

        place = factory.Faker('word')
        status = factory.SubFactory(event_status_factory(db_session))
    return EventFactory


@pytest.fixture
def media_factory():
    class MediaFactory(factory.alchemy.SQLAlchemyModelFactory):
        class Meta:
            model = EventMedia
            sqlalchemy_session = db_session

        # TODO: add file here!
        event_id = factory.SubFactory(event_factory(db_session))
    return MediaFactory