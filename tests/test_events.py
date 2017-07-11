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
from common.utils import ResponseCodes, get_json
from marshmallow import Schema, fields

from test_utils.helpers import get_auth_header, register_and_login_user, \
    JSON_CONTENT_TYPE, dict_contains_subset


DATETIME_FORMAT = app.config['DATETIME_FORMAT']


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
    periodic = False

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
    status = fields.Str(required=True)
    start = fields.DateTime(format=DATETIME_FORMAT)
    end = fields.DateTime(format=DATETIME_FORMAT)
    periodic = fields.Boolean(required=True)


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
        return fuzzy.FuzzyDateTime(start_datetime).fuzz()


@pytest.mark.usefixtures('clearer')
def test_create_event(test_client):
    user_payload, token = register_and_login_user(test_client)
    event_payload = EventPayloadFactory()
    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    response = test_client.post(CREATE_URL,
                                data=json.dumps(dumped_event_payload),
                                headers=dict(JSON_CONTENT_TYPE,
                                             **get_auth_header(token)))

    data = get_json(response)
    assert dict_contains_subset(dumped_event_payload, data)
    assert response.status_code == ResponseCodes.CREATED
