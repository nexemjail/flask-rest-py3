from marshmallow.decorators import post_load

from common import ma
from .models import Event


class EventSchema(ma.ModelSchema):
    class Meta:
        model = Event


class EventCreateSchema(ma.ModelSchema):
    class Meta:
        model = Event
