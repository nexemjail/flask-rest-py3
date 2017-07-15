from sqlalchemy.testing.assertions import in_

from common.database import db_session, Base, decl_base
from sqlalchemy_utils.types import ChoiceType
from sqlalchemy import (
    Column, Integer, String, Text, Table,
    ForeignKey, DateTime, Boolean
)
from sqlalchemy.orm import relationship

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


class EventStatus(Base):
    __tablename__ = 'event_statuses'

    status = Column(ChoiceType(EVENT_CHOICES))


LabelsEvents = Table(
    'labels_events',
    decl_base.metadata,
    Column('label_id', Integer, ForeignKey('labels.id')),
    Column('event_id', Integer, ForeignKey('events.id'))
)


class Label(Base):
    __tablename__ = 'labels'

    name = Column(String(100))
    events = relationship('Event', secondary=LabelsEvents)

    @classmethod
    def create_non_existing(cls, labels_list):
        existing_labels = db_session\
            .query(Label.name)\
            .filter(Label.name.in_(labels_list))

        not_existing_labels = set(labels_list) - set(existing_labels.all())

        db_session.add_all((Label(name=name) for name in not_existing_labels))
        db_session.commit()

    @classmethod
    def create_all(cls, label_list):
        Label.create_non_existing(label_list)
        return db_session.query(Label).filter(Label.name.in_(label_list))


class Event(Base):
    __tablename__ = 'events'

    user_id = Column(Integer, ForeignKey('users.id'))
    description = Column(Text, nullable=True)
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)

    periodic = Column(Boolean, default=False)
    period = Column(INTERVAL, nullable=True)

    next_notification = Column(DateTime(timezone=True), nullable=True)
    place = Column(Text, nullable=True)
    status_id = Column(Integer, ForeignKey(EventStatus.id))
    status = relationship('EventStatus')
    labels = relationship('Label', secondary=LabelsEvents)
    media = relationship('EventMedia')


class EventMedia(Base):
    __tablename__ = 'events_media'
    # TODO: add file here!
    event_id = Column(Integer, ForeignKey('events.id', related_name='media'))
