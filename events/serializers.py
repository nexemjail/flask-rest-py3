from common import ma
from    .models import Event


class EventSchema(ma.ModelSchema):
    class Meta:
        model = Event
