from common.database import decl_base, db
from sqlalchemy import Enum, Enum
from sqlalchemy_utils.types import ChoiceType

from common.models import User

EVENT_STATUSES = ('W', 'P', 'C')
EVENT_CHOICES = (
    ('W', 'Waiting'),
    ('C', 'Cancelled'),
    ('P', 'Passed'),
)
EVENT_CREATE_CHOICES = (
    ('W', 'Waiting'),
    ('P', 'Passed'),
)


class EventStatus(db.Model, decl_base):

    __tablename__ = 'event_status'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(ChoiceType(EVENT_CHOICES))


class Label(db.Model, decl_base):

    __tablename__ = 'label'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))

    @classmethod
    def create_non_existing(cls, labels_list):
        existing_labels = Label.objects.filter(name__in=labels_list)\
            .values_list('name', flat=True)
        not_existing_labels = set(labels_list) - set(existing_labels)

        Label.objects.bulk_create((Label(name=name) for name
                                   in not_existing_labels))

    @classmethod
    def create_all(cls, label_list):
        Label.create_non_existing(label_list)
        return Label.objects.filter(name__in=label_list)

labels_secondary = db.Table('labels',
    db.Column('label_id', db.Integer, db.ForeignKey(Label.id)),
    db.Column('user_id', db.Integer, db.ForeignKey(User.id))
)


class Event(db.Model, decl_base):

    __tablename__ = 'event'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id))
    description = db.Column(db.Text, nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)

    periodic = db.Column(db.Boolean, default=False)
    # TODO: handle duration field
    # period = db.Column(s)
    # period = models.DurationField(null=True)

    next_notification = db.Column(db.DateTime, nullable=True)
    place = db.Column(db.String(500), nullable=True)
    # place = models.CharField(max_length=500, null=True)
    # status = models.ForeignKey(EventStatus)
    status_id = db.ForeignKey(EventStatus.id, name='status')
    labels = db.relationship(Label, secondary=labels_secondary,
                             backref=db.backref('events', lazy='dynamic'))


class EventMedia(db.Model, decl_base):

    __tablename__ = 'event_media'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    event_id = db.ForeignKey(Event.id, related_name='media')

    # media = db.File.FileField(null=True)
