from sqlalchemy.testing.assertions import in_

from common.database import decl_base, db, db_session
from sqlalchemy_utils.types import ChoiceType

from sqlalchemy.dialects.postgresql import INTERVAL


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

    status = db.Column(ChoiceType(EVENT_CHOICES))


LabelsEvents = db.Table(
    'labels_events',
    db.Column('label_id', db.Integer, db.ForeignKey('label.id')),
    db.Column('event_id', db.Integer, db.ForeignKey('event.id'))
)


class Label(db.Model, decl_base):
    __tablename__ = 'label'

    name = db.Column(db.String(100))
    events = db.relationship('Event', secondary=LabelsEvents)

    @classmethod
    def create_non_existing(cls, labels_list):

        existing_labels = db_session\
            .query(Label, Label.name)\
            .filter(in_(Label.name, labels_list))

        not_existing_labels = set(labels_list) - set(existing_labels.all())


        db_session.add_all((Label(name=name) for name in not_existing_labels))
        db_session.commit()

    @classmethod
    def create_all(cls, label_list):
        Label.create_non_existing(label_list)
        return db_session.query(Label).filter(in_(Label.name, label_list))


class Event(db.Model, decl_base):
    __tablename__ = 'event'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    description = db.Column(db.Text, nullable=True)
    start = db.Column(db.DateTime, nullable=False)
    end = db.Column(db.DateTime, nullable=False)

    periodic = db.Column(db.Boolean, default=False)
    # TODO: handle duration field
    period = db.Column(INTERVAL, nullable=True)

    next_notification = db.Column(db.DateTime, nullable=True)
    place = db.Column(db.String(500), nullable=True)
    status_id = db.ForeignKey('event_status.id', name='status')
    labels = db.relationship('Label', secondary=LabelsEvents)
    media = db.relationship('EventMedia')


class EventMedia(db.Model, decl_base):
    __tablename__ = 'event_media'

    event_id = db.Column(db.Integer, db.ForeignKey('event.id',
                                                   related_name='media'))
