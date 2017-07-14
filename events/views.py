from flask.blueprints import Blueprint
from flask_restful import Api

from common.database import db_session
from common.utils import ResponseCodes, template_response, bytes_to_str
from common.base import BaseResource
from events.serializers import EventSchema, EventCreateSchema, EventUpdateSchema

from .models import Event

from flask_jwt import jwt_required, current_identity
from flask import request


api_bp = Blueprint('events', __name__)
api = Api(api_bp)


class EventBase(BaseResource):
    def _bad_request(self, errors):
        return template_response(
            status='Error',
            code=ResponseCodes.BAD_REQUEST_400,
            data=errors
        )



class EventDetail(EventBase):
    @jwt_required()
    def get(self, event_id):
        event = db_session.query(Event).filter(Event.id == event_id).first()
        if not event or event.user_id != current_identity.id:
            return self._not_found()
        return template_response(
            status='OK',
            code=ResponseCodes.OK,
            data=EventSchema().dump(event).data
        )


class EventUpdate(EventBase):
    @jwt_required()
    def patch(self):
        schema = EventUpdateSchema(partial=True)
        data, errors = schema.loads(bytes_to_str(request.data))
        if errors:
            return self._bad_request(errors)

        #TODO: handle logic here!

        db_session.query(Event).filter(data.id)

        if errors:
            return self._bad_request(errors)


class EventList(EventBase):
    @jwt_required()
    def get(self):
        query = db_session.query(Event).filter(
            Event.user_id == current_identity.id).all()
        return template_response(
            status='OK',
            code=ResponseCodes.OK,
            data=EventSchema().dump(query,many=True).data
        )


class EventCreate(EventBase):
    @jwt_required()
    def post(self):
        # create an object instance
        schema = EventCreateSchema()
        event_data, errors = schema.loads(bytes_to_str(request.data))

        if errors:
            return self._bad_request(errors)

        event = schema.make_model(event_data)
        db_session.add(event)
        db_session.commit()

        return template_response(
                status='OK',
                message='Created',
                data=EventSchema().dump(event).data,
                code=ResponseCodes.CREATED
        )


api.add_resource(EventDetail, '/events/event/<int:event_id>',
                 endpoint='detail')
api.add_resource(EventUpdate, '/events/event/<int:event_id>',
                 endpoint='update')
api.add_resource(EventCreate, '/events/event/', endpoint='create')
api.add_resource(EventList, '/events/event/list/', endpoint='list')
