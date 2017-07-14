from flask.blueprints import Blueprint
from flask_restful import Api

from common.database import db_session
from common.utils import ResponseCodes
from common.base import BaseResource
from events.serializers import EventSchema, EventCreateSchema

from .models import Event

from flask_jwt import jwt_required, current_identity
from flask import request


api_bp = Blueprint('events', __name__)
api = Api(api_bp)


class EventDetail(BaseResource):
    @jwt_required()
    def get(self, event_id):
        event = db_session.query(Event).filter(Event.id == event_id).first()
        if not event or event.user_id != current_identity.id:
            return {'error': 'Not found'}, 404
        return EventSchema().dump(event).data, 200


class EventUpdate(BaseResource):
    @jwt_required()
    def patch(self):
        pass

class EventList(BaseResource):
    @jwt_required()
    def get(self):
        query = db_session.query(Event).filter(
            Event.user_id == current_identity.id).all()
        data = EventSchema().dump(query,many=True).data
        return data, 200


class EventCreate(BaseResource):
    @jwt_required()
    def post(self):
        # create an object instance
        event, errors = EventCreateSchema().loads(str(request.data,
                                                      encoding='utf-8'))
        if not errors:
            db_session.add(event)
            db_session.commit()
            return EventSchema().dump(event).data, ResponseCodes.CREATED
        return errors, ResponseCodes.BAD_REQUEST_400


api.add_resource(EventDetail, '/events/event/<int:event_id>',
                 endpoint='detail')
api.add_resource(EventUpdate, '/events/event/<int:event_id>',
                 endpoint='update')
api.add_resource(EventCreate, '/events/event/', endpoint='create')
api.add_resource(EventList, '/events/event/list/', endpoint='list')
