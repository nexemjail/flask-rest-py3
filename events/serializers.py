from marshmallow.decorators import post_load

from common import ma
from .models import Event


class EventSchema(ma.ModelSchema):
    class Meta:
        model = Event


class EventCreateSchema(ma.ModelSchema):
    class Meta:
        model = Event

    @post_load
    def create_event(self, data):
        # TODO: add create logic here
        # return Event()
        pass