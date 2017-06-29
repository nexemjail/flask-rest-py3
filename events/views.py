from flask.blueprints import Blueprint
from flask.ext.jwt import current_identity
from flask.ext.restful import Api

from flask_restful import Resource

from common.database import db_session
from events.serializers import EventSchema, EventCreateSchema

from .models import Event

from flask_jwt import jwt_required
from flask import request


api_bp = Blueprint('events', __name__)
api = Api(api_bp)

class EventDetail(Resource):
    @jwt_required()
    def get(self, event_id):
        event = db_session.query(EventDetail).filter(event_id=Event.id).first()
        return EventSchema().dump(event).data, 200

class EventList(Resource):
    @jwt_required()
    def get(self):
        query = db_session.query(Event).filter(
            Event.user_id==current_identity.id).all()
        data = EventSchema().dump(query,many=True).data
        return data, 200

class EventCreate(Resource):
    @jwt_required()
    def post(self):
        data = request.json
        # create an object instance
        event, errors = EventCreateSchema().load(data)
        if not errors:
            db_session.add(event)
            db_session.flush()


api.add_resource(EventDetail, '/events/event/<int:event_id>')
api.add_resource(EventCreate, '/events/event/')
api.add_resource(EventList, '/events/event/list/')
