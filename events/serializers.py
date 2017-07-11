from flask.ext.jwt import current_identity
from flask.ext.marshmallow.schema import Schema
from marshmallow import fields
from marshmallow.decorators import post_dump, post_load, pre_load, pre_dump
from marshmallow.exceptions import ValidationError
from marshmallow_sqlalchemy import ModelSchema
from marshmallow_sqlalchemy.schema import ModelSchemaOpts

from common import ma, app
from common.database import db_session
from common.models import User
from events.models import EventStatus
from .models import Event


DATETIME_FORMAT = app.config['DATETIME_FORMAT']


class EventStatusSchema(Schema):
    status = fields.Str()

    @post_load
    def make_model(self, data):
        return db_session.query(EventStatus)\
            .filter(EventStatus.status==data['status'])\
            .limit(1)\
            .first()

    @pre_dump
    def pre_dump(self, data):
        data.status = data.status.code
        return data


class DateTimeEventMixin(Schema):
    start = fields.DateTime(format=DATETIME_FORMAT)
    end = fields.DateTime(format=DATETIME_FORMAT)


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
    user = fields.Nested(UserSchema)
    description = fields.Str()

    periodic = fields.Boolean(required=True, default=False)
    # TODO: handle duration field

    next_notification = fields.DateTime(format=DATETIME_FORMAT,
                                        required=False, default=None)
    place = fields.Str()
    status = fields.Str()
    labels = fields.Nested(EventLabelSchema, many=True, required=False)
    media = fields.Nested(EventMediaSchema, many=True)

    @pre_dump
    def pre_dump(self, data):
        status = db_session.query(EventStatus).filter(
            EventStatus.id==data.status_id).first()

        if not status:
            raise Exception('Status not found')

        data.status = status.status.code
        return data



class EventCreateSchema(DateTimeEventMixin):
    user = fields.Nested(UserSchema)
    description = fields.Str()
    status = fields.Str(required=True)

    periodic = fields.Boolean(required=True, default=False)

    @post_load
    def make_model(self, data):
        status = data.pop('status')
        event = Event(**data)

        user_id = db_session.query(User.id)\
            .filter(current_identity.username==User.username)\
            .first()
        if not user_id:
            raise Exception('no user found for JWT')
        event.user_id = user_id[0]

        event_status_id = db_session.query(EventStatus.id)\
            .filter(EventStatus.status==status)\
            .first()
        if not event_status_id:
            raise Exception('No status found for key {}'.format(status))

        event.status_id = event_status_id[0]

        return event

    @pre_dump()
    def pre_dump(self, data):
        data.status = data.status.code
        return data
