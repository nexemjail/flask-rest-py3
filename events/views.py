from common import db, api
from flask_restful import Resource

from common.database import db_session
from events.serializers import EventSchema

from .models import Event

from flask_jwt import jwt_required


class Events(Resource):

    @jwt_required()
    def get(self, event_id):
        event = db_session.query(Events).filter(event_id=Event.id).first()
        return EventSchema().dump(event).data, 200

# TODO: register endpoints
