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

    @validates_schema
    def validate(self, data, many=None, partial=None):
        super(EventUpdateSchema, self).validate(data, many, partial)

        if not db_session.query(Event).filter(Event.id == data['id']).exists():
            raise ValidationError('Event not exists', fields=['id'])

    def load_object(self, data):
        return db_session.query(Event).filter(Event.id == data['id']).first()

    def get_status(self, status_name):
        return db_session.query(Label)\
            .filter(Label.name == status_name)\
            .first()

    def update_object(self, data):

        event_data = {}

        event = self.load_object(data)

        event_data['start'] = data.get('start') or event.start
        event_data['end'] = data.get('end') or event.end
        event_data['period'] = data.get('period') or event.period
        event_data['periodic'] = data.get('periodic') or event.periodic
        event_data['next_notifications'] = data.get('next_notification') or \
            event.next_notification
        event_data['description'] = data.get('description') or\
            event.description
        event_data['place'] = data.get('place') or event.place
        event_data['status'] = (
            self.get_status(data.get('status')) or event.status)

        validate_event(event_data)
        event.start = data.get('start') or event.start
        event.end = data.get('end') or event.end
        event.period = data.get('period') or event.period
        event.periodic = data.get('periodic') or event.periodic

        event.next_notification = data.get('next_notification') or \
            event.next_notification

        event.description = data.get('description') or event.description

        # Labels should be set in last moments, cause they are always valid

        event.place = data.get('place') or event.place
        # TODO: change it!
        event.status = self.get_status(data.get('status')) or event.status

        label_names = [l.name for l in event.labels]
        event.labels = Label.create_all(data.get('labels') or label_names)


def validate_event(data):
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

        event_borders = db_session.query(Event.start, Event.end) \
            .filter(
            Event.user_id == current_identity.id,
            Event.end.isnot(None)) \
            .all()
        for event_start, event_end in event_borders:
            if max(event_start, start) <= min(event_end, end):
                raise ValidationError('Event is overlapping with others')
    return data
