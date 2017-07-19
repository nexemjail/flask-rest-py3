from datetime import timedelta

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from flask_jwt import current_identity
from flask_marshmallow import Schema
from marshmallow import fields
from marshmallow.decorators import pre_dump, validates_schema
from marshmallow.exceptions import ValidationError
from marshmallow.fields import Field

from common import app
from common.database import db_session
from common.models import User
from common.utils import timedelta_to_hms
from events.models import EventStatus, Label
from .models import Event


DATETIME_FORMAT = app.config['DATETIME_FORMAT']


class PeriodField(Field):
    def _serialize(self, value, attr, obj):
        if not isinstance(value, timedelta):
            return None
        hour, minute, second = timedelta_to_hms(value)
        return '{d} {h}:{m}:{s}'.format(d=value.days,
                                        h=hour,
                                        m=minute,
                                        s=second)

    def _deserialize(self, value, attr, data):
        if not isinstance(value, str):
            return None
        parts = value.split(' ')
        days = int(parts[0]) if len(parts) > 1 else 0
        hms_values = parts[1] if len(parts) > 1 else parts[0]

        hours, minutes, seconds = list(
            map(int, hms_values.split(':'))
        )
        return timedelta(days=days,
                         hours=hours,
                         minutes=minutes,
                         seconds=seconds)


class EventStatusSchema(Schema):
    status = fields.Str()

    def make_model(self, data):
        return db_session.query(EventStatus)\
            .filter(EventStatus.status == data['status'])\
            .limit(1)\
            .first()

    @pre_dump
    def pre_dump(self, data):
        data.status = data.status.code
        return data


class DateTimeEventMixin(Schema):
    start = fields.DateTime(format=DATETIME_FORMAT)
    end = fields.DateTime(format=DATETIME_FORMAT)
    next_notification = fields.DateTime(format=DATETIME_FORMAT, required=False)


class UserSchema(Schema):
    username = fields.Str(required=True)
    email = fields.Str(required=True)
    first_name = fields.Str()
    last_name = fields.Str()


class EventLabelSchema(Schema):
    name = fields.Str()


class EventMediaSchema(Schema):
    pass


class EventSchema(DateTimeEventMixin):
    id = fields.Integer()
    user = fields.Nested(UserSchema)
    description = fields.Str()

    periodic = fields.Boolean(required=True, default=False)
    period = PeriodField()
    next_notification = fields.DateTime(format=DATETIME_FORMAT,
                                        required=False, default=None)
    place = fields.Str()
    status = fields.Method('dump_status')
    labels = fields.Method('dump_labels', required=False)
    media = fields.Nested(EventMediaSchema, many=True)

    def dump_labels(self, data):
        return [l.name for l in data.labels]

    def dump_status(self, data):
        return data.status.status.code


def raise_validation_error(message, field_names=None, container=None):
    error = ValidationError(message, field_names=field_names)
    if container is not None:
        container.append(error)
        return container
    raise error


def validate_event(data, error_container=None):
    if data.get('periodic') is False and data.get('period') is not None:
        error_container = raise_validation_error(
            'Either both of period and periodic should be specified or'
            ' none of them',
            field_names=['period', 'periodic'],
            container=error_container)
    if data.get('next_notification') is None:
        data['next_notification'] = data['start'] - \
                                    relativedelta(minutes=5)

    if data.get('end'):
        start, end = data['start'], data['end']

        if start > end:
            error_container = raise_validation_error(
                'Invalid event borders',
                field_names=['start', 'end'],
                container=error_container)

        if data['next_notification'] > end:
            error_container = raise_validation_error(
                'Next notification should be earlier than end of event',
                field_names=['next_notification'],
                container=error_container)

        period = data.get('period')
        if period:
            if period > end - start:
                error_container = raise_validation_error(
                    'Period must be smaller than start-end time period',
                    field_names=['period'],
                    container=error_container)
        return error_container


class EventCreateSchema(DateTimeEventMixin):
    user = fields.Nested(UserSchema)
    description = fields.Str()
    status = fields.Method('get_status', required=True)

    periodic = fields.Boolean(required=True, default=False)
    period = PeriodField()
    labels = fields.List(fields.Str)

    def make_model(self, data):
        status = data.pop('status')
        event = Event(**data)

        labels_list = data.pop('labels', [])
        if labels_list:
            labels = Label.create_all(labels_list).all()
        else:
            labels = []
        event.labels = labels

        user_id = db_session.query(User.id)\
            .filter(current_identity.username == User.username,
                    current_identity.email == User.email)\
            .first()
        if not user_id:
            raise Exception('no user found for JWT')
        event.user_id = user_id[0]

        event_status_id = db_session.query(EventStatus.id)\
            .filter(EventStatus.status == status)\
            .first()
        if not event_status_id:
            raise Exception('No status found for key {}'.format(status))

        event.status_id = event_status_id[0]

        return event

    def get_status(self, obj):
        if isinstance(obj, dict):
            return obj['status']
        elif isinstance(obj, Event):
            return obj.status.status.code

    @validates_schema
    def validate(self, data):
        validate_event(data)
        if data.get('end'):
            validate_borders(data['start'], data['end'])


def validate_borders(start, end, self_id=None, error_container=None):
    event_borders = db_session.query(Event.start, Event.end) \
        .filter(
        Event.user_id == current_identity.id,
        Event.end.isnot(None)
    )

    if self_id is not None:
        event_borders = event_borders.filter(Event.id != self_id)

    for event_start, event_end in event_borders.all():
        if max(event_start, start) <= min(event_end, end):
            error_container = raise_validation_error(
                'Event is overlapping with others',
                container=error_container)
    return error_container


def container_to_payload(error_container):
    errors = defaultdict(list)
    if not error_container:
        return
    for error in error_container:
        if error.field_names:
            for fn in error.field_names:
                errors[fn].append(*error.messages)
        else:
            errors['_schema'].append(*error.messages)
    return errors


# TODO: finish update schema!
# TODO: handle labels and statuses
class EventUpdateSchema(EventCreateSchema):
    def __init__(self, *args,
                 partial=False,
                 event_id=None,
                 raise_errors=True, **kwargs):
        super(EventCreateSchema, self).__init__(*args, **kwargs)
        self.event_id = event_id
        self.raise_errors = raise_errors
        self.partial = partial

    @validates_schema
    def validate(self, data):
        error_container = None if self.raise_errors else []
        if self.partial:
            return error_container

        error_container = validate_event(
            data, error_container=error_container)
        if data.get('end'):
            error_container = validate_borders(
                start=data['start'],
                end=data['end'],
                self_id=self.event_id,
                error_container=error_container)
        return container_to_payload(error_container)

    @staticmethod
    def load_object(event_id):
        return db_session.query(Event).filter(Event.id == event_id).first()

    def get_status_by_name(self, status_name):
        return db_session.query(EventStatus)\
            .filter(EventStatus.status == status_name)\
            .first()

    def get_labels(self, event):
        return [l.name for l in event.labels]

    def get_data(self, event, data):
        return {
            'start': data.get('start') or event.start,
            'end': data.get('end') or event.end,
            'period': data.get('period') or event.period,
            'periodic':
                data.get('periodic') if data.get('periodic') is not None
                else event.periodic,
            'next_notification': data.get('next_notification') or
                event.next_notification,
            'description': data.get('description') or event.description,
            'place': data.get('place') or event.place,
            'status': (self.get_status_by_name(data.get('status')) or
                       event.status).status.code,
            'labels': data.get('labels') or self.get_labels(event)
        }

    def update(self, event, data):
        event.start = data.get('start')
        event.end = data.get('end')
        event.period = data.get('period')
        event.periodic = data.get('periodic')
        event.next_notification = data.get('next_notification')
        event.description = data.get('description')
        event.place = data.get('place')
        event.status = self.get_status_by_name(data.get('status'))

        # Labels should be set in last moments, cause they are always valid
        label_names = data.get('labels')
        if label_names is None:
            label_names = [l.name for l in event.labels]
        event.labels = Label.create_all(label_names).all()
        db_session.commit()
        return event
