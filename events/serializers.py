from datetime import timedelta

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
        return obj.status.status.code

    @validates_schema
    def validate(self, data, many=None, partial=None):
        if data.get('periodic') is False and data.get('period') is not None:
            raise ValidationError('Either both of period and periodic '
                                  'should be specified or none of them',
                                  field_names=['period', 'periodic'])
        if data.get('next_notification') is None:
            data['next_notification'] = data['start'] - \
                                        relativedelta(minutes=5)

        if data.get('end'):
            start, end = data['start'], data['end']

            if start > end:
                raise ValidationError('Invalid event borders',
                                      field_names=['start', 'end'])

            event_borders = db_session.query(Event.start, Event.end)\
                .filter(
                    Event.user_id == current_identity.id,
                    Event.end.isnot(None))\
                .all()
            for event_start, event_end in event_borders:
                if max(event_start, start) <= min(event_end, end):
                    raise ValidationError('Event is overlapping with others')


# TODO: finish update schema!
class EventUpdateSchema(EventCreateSchema):
    id = fields.Integer(required=True)

    def load_object(self, data):
        return db_session.query(Event).filter(Event.id == data['id']).first()
