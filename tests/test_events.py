import json
import factory
import pytz
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from factory import fuzzy
from flask.helpers import url_for
from random import randint

from common import app
from common.utils import ResponseCodes, get_json
from marshmallow import Schema, fields

from events.serializers import PeriodField
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


def get_update_url(event_id):
    with app.test_request_context():
        return url_for('events.update', event_id=event_id)


def get_delete_url(event_id):
    with app.test_request_context():
        return url_for('events.update', event_id=event_id)


class EventPayloadFactory(factory.DictFactory):
    description = factory.Faker('word')
    # TODO: handle C(cancelled) too
    status = fuzzy.FuzzyChoice(['W', 'P'])
    periodic = False

    @factory.lazy_attribute
    def labels(self):
        words = randint(0, 7)
        return list(set(factory.Faker('words').generate(
            extra_kwargs={'nb': words}))
        )

    @factory.lazy_attribute
    def start(self):
        start_dt = get_timezone_aware_time()
        return fuzzy.FuzzyDateTime(start_dt=get_timezone_aware_time(),
                                   end_dt=start_dt + relativedelta(years=100))\
            .fuzz()

    @factory.lazy_attribute
    def end(self):
        return fuzzy.FuzzyDateTime(
            start_dt=self.start + relativedelta(hours=1),
            end_dt=self.start + relativedelta(years=100))\
            .fuzz()


class EventPayloadSchema(Schema):
    description = fields.Str()
    status = fields.Str(required=True)
    start = fields.DateTime(format=DATETIME_FORMAT)
    end = fields.DateTime(format=DATETIME_FORMAT)
    periodic = fields.Boolean(required=True)
    labels = fields.List(fields.Str)
    period = PeriodField()
    next_notification = fields.DateTime(format=DATETIME_FORMAT)


class NonPeriodicEventFactory(EventPayloadFactory):
    periodic = False


class PeriodicEventPayloadFactory(EventPayloadFactory):
    periodic = True

    @factory.lazy_attribute
    def period(self):
        return timedelta(days=randint(0, 365),
                         hours=randint(0, 59),
                         minutes=randint(0, 59),
                         seconds=randint(1, 59))

    @factory.lazy_attribute
    def end(self):
        start_datetime = self.start + relativedelta(hours=1) + self.period
        return fuzzy.FuzzyDateTime(
            start_dt=start_datetime,
            end_dt=start_datetime + relativedelta(years=100))\
            .fuzz()

    @factory.lazy_attribute
    def next_notification(self):
        return self.start + self.period


def create_event(test_client, token,
                 event_payload=None,
                 event_payload_factory=PeriodicEventPayloadFactory,
                 return_dumped_payload=True):
    if event_payload is None:
        event_payload = event_payload_factory()
    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    response = test_client.post(CREATE_URL,
                                data=json.dumps(dumped_event_payload),
                                headers=dict(JSON_CONTENT_TYPE,
                                             **get_auth_header(token)))

    data = get_json(response, inner_data=True)
    assert response.status_code == ResponseCodes.CREATED
    return (dumped_event_payload, data) \
        if return_dumped_payload else (event_payload, data)


def test_create_event(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)
    dumped_event_payload, data = create_event(
        test_client, token, event_payload_factory=EventPayloadFactory)

    assert dict_contains_subset(dumped_event_payload, data)


def test_create_periodic_event(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    dumped_event_payload, data = create_event(
        test_client, token, event_payload_factory=PeriodicEventPayloadFactory)

    assert dict_contains_subset(dumped_event_payload, data)


def test_event_detail(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    dumped_event_payload, data = create_event(
        test_client, token, event_payload_factory=PeriodicEventPayloadFactory)

    response = test_client.get(get_detail_url(data['id']),
                               headers=dict(JSON_CONTENT_TYPE,
                                            **get_auth_header(token)))

    assert response.status_code == ResponseCodes.OK
    data = get_json(response, inner_data=True)
    assert dict_contains_subset(dumped_event_payload, data)


def test_invalid_start_end(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = PeriodicEventPayloadFactory()
    event_payload['end'] = event_payload['start'] - relativedelta(minutes=5)

    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    response = test_client.post(CREATE_URL,
                                data=json.dumps(dumped_event_payload),
                                headers=dict(JSON_CONTENT_TYPE,
                                             **get_auth_header(token)))

    assert response.status_code == ResponseCodes.BAD_REQUEST_400
    data = get_json(response, inner_data=True)
    assert 'start' in data
    assert 'end' in data


def test_invalid_period_and_periodic_flag(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = NonPeriodicEventFactory()
    event_payload['period'] = PeriodicEventPayloadFactory()['period']

    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    response = test_client.post(CREATE_URL,
                                data=json.dumps(dumped_event_payload),
                                headers=dict(JSON_CONTENT_TYPE,
                                             **get_auth_header(token)))

    assert response.status_code == ResponseCodes.BAD_REQUEST_400
    data = get_json(response, inner_data=True)
    assert 'period' in data
    assert 'periodic' in data


def test_create_overlapping_events(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = PeriodicEventPayloadFactory()
    event2_payload = PeriodicEventPayloadFactory(start=event_payload['start'],
                                                 end=event_payload['end'])

    create_event(test_client, token, event_payload=event_payload)

    dumped_event_payload = EventPayloadSchema().dump(event2_payload).data
    response = test_client.post(CREATE_URL,
                                data=json.dumps(dumped_event_payload),
                                headers=dict(JSON_CONTENT_TYPE,
                                             **get_auth_header(token)))

    assert response.status_code == ResponseCodes.BAD_REQUEST_400
    data = get_json(response, inner_data=True)
    # Schema level error
    assert '_schema' in data


def test_create_event_with_too_big_period(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = PeriodicEventPayloadFactory()
    event_payload['period'] = event_payload['end'] - event_payload['start'] +\
        timedelta(hours=5)

    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    response = test_client.post(CREATE_URL,
                                data=json.dumps(dumped_event_payload),
                                headers=dict(JSON_CONTENT_TYPE,
                                             **get_auth_header(token)))

    assert response.status_code == ResponseCodes.BAD_REQUEST_400
    data = get_json(response, inner_data=True)
    assert 'period' in data


def test_create_event_with_next_notification_too_far(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = PeriodicEventPayloadFactory()
    event_payload['next_notification'] = event_payload['end'] + \
        relativedelta(days=10)

    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    response = test_client.post(CREATE_URL,
                                data=json.dumps(dumped_event_payload),
                                headers=dict(JSON_CONTENT_TYPE,
                                             **get_auth_header(token)))

    assert response.status_code == ResponseCodes.BAD_REQUEST_400
    data = get_json(response, inner_data=True)
    assert 'next_notification' in data


def test_fully_update_event(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = PeriodicEventPayloadFactory()
    dumped_payload, data = create_event(test_client, token,
                                        event_payload=event_payload,
                                        return_dumped_payload=False)
    event_id = data['id']

    event_payload = PeriodicEventPayloadFactory()
    dumped_event_payload = EventPayloadSchema().dump(event_payload).data

    response = test_client.patch(get_update_url(event_id),
                                 data=json.dumps(dumped_event_payload),
                                 headers=dict(JSON_CONTENT_TYPE,
                                              **get_auth_header(token)))
    assert dict_contains_subset(dumped_event_payload,
                                get_json(response, inner_data=True))


def test_partially_update_event(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = PeriodicEventPayloadFactory()
    dumped_payload, data = create_event(test_client, token,
                                        event_payload=event_payload,
                                        return_dumped_payload=False)
    event_id = data['id']

    event_payload = PeriodicEventPayloadFactory()
    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    del dumped_payload['period']
    del dumped_event_payload['labels']
    del dumped_event_payload['end']
    del dumped_event_payload['start']
    del dumped_event_payload['next_notification']

    response = test_client.patch(get_update_url(event_id),
                                 data=json.dumps(dumped_event_payload),
                                 headers=dict(JSON_CONTENT_TYPE,
                                              **get_auth_header(token)))
    assert dict_contains_subset(dumped_event_payload,
                                get_json(response, inner_data=True))


def test_invalid_event_update(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = PeriodicEventPayloadFactory()
    dumped_payload, data = create_event(test_client, token,
                                        event_payload=event_payload,
                                        return_dumped_payload=False)
    event_id = data['id']

    event_payload = PeriodicEventPayloadFactory()
    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    dumped_event_payload['periodic'] = False

    response = test_client.patch(get_update_url(event_id),
                                 data=json.dumps(dumped_event_payload),
                                 headers=dict(JSON_CONTENT_TYPE,
                                              **get_auth_header(token)))
    assert response.status_code == 400
    data = get_json(response, inner_data=True)
    assert 'period' in data
    assert 'periodic' in data


def test_delete_event(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = PeriodicEventPayloadFactory()

    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    response = test_client.post(CREATE_URL,
                                data=json.dumps(dumped_event_payload),
                                headers=dict(JSON_CONTENT_TYPE,
                                             **get_auth_header(token)))

    assert response.status_code == ResponseCodes.CREATED
    data = get_json(response, inner_data=True)
    response = test_client.delete(get_delete_url(data['id']),
                                  headers=dict(JSON_CONTENT_TYPE,
                                               **get_auth_header(token)))

    assert response.status_code == ResponseCodes.NO_CONTENT


def test_delete_event_with_invalid_id(test_client, transaction):
    user_payload, token = register_and_login_user(test_client)

    event_payload = PeriodicEventPayloadFactory()

    dumped_event_payload = EventPayloadSchema().dump(event_payload).data
    response = test_client.post(CREATE_URL,
                                data=json.dumps(dumped_event_payload),
                                headers=dict(JSON_CONTENT_TYPE,
                                             **get_auth_header(token)))

    assert response.status_code == ResponseCodes.CREATED
    response = test_client.delete(get_delete_url(0),
                                  headers=dict(JSON_CONTENT_TYPE,
                                               **get_auth_header(token)))

    assert response.status_code == ResponseCodes.NOT_FOUND_404
