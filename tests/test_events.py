import json
import factory
import pytest
import pytz
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from factory import fuzzy
from flask.helpers import url_for
from random import randint

from common import app
from common.utils import ResponseCodes
from marshmallow import Schema, fields

from test_utils.helpers import get_auth_header, register_and_login_user, \
    JSON_CONTENT_TYPE

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_timezone_aware_time():
    return datetime.now(pytz.utc)

with app.test_request_context():
    CREATE_URL = url_for('events.create')
    LIST_URL = url_for('events.list')



def get_detail_url(event_id):
    with app.test_request_context():
        return url_for('events.detail', event_id=event_id)


class EventPayloadFactory(factory.DictFactory):
    description = factory.Faker('word')
    # TODO: handle C(cancelled) too
    status = fuzzy.FuzzyChoice(['W', 'P'])

    @factory.lazy_attribute
    def start(self):
        start_dt = get_timezone_aware_time()
        return fuzzy.FuzzyDateTime(start_dt=get_timezone_aware_time(),
                                   end_dt=start_dt + relativedelta(years=100))\
            .fuzz()

    @factory.lazy_attribute
    def end(self):
        return fuzzy.FuzzyDateTime(start_dt=self.start +
                                            relativedelta(hours=1),
                                   end_dt=self.start + relativedelta(
                                       years=100)).fuzz()

class EventPayloadSchema(Schema):
    description = fields.Str()
    status = fields.Str()
    start = fields.DateTime(format=DATETIME_FORMAT)
    end = fields.DateTime(format=DATETIME_FORMAT)


class NonPeriodicEventFactory(EventPayloadFactory):
    periodic = False


class PeriodicEventPayloadFactory(EventPayloadFactory):
    periodic = True

    @factory.lazy_attribute
    def period(self):
        return relativedelta(day=randint(0, 365),
                             hour=randint(0,59),
                             minute=randint(0,59),
                             second=randint(1,59))

    @factory.lazy_attribute
    def end(self):
        start_datetime = self.start + relativedelta(hours=1) +self.period
        return fuzzy.FuzzyDateTime(start_datetime).fuzz()\
            .strftime(DATETIME_FORMAT)


@pytest.mark.usefixtures('clearer')
def test_create_event(test_client):
    user_payload, token = register_and_login_user(test_client)
    event_payload = EventPayloadFactory()
    dumped_event_payload = EventPayloadSchema().dumps(event_payload)
    response = test_client.post(CREATE_URL,
                     data=dumped_event_payload.data,
                      headers=dict(JSON_CONTENT_TYPE, **get_auth_header(
                          token)))
    # TODO: provide more asserts!
    assert response.status_code == ResponseCodes.CREATED
