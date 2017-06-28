"""empty message

Revision ID: 034a611d5a31
Revises: 
Create Date: 2017-06-27 14:50:56.909212

"""
from sqlalchemy.dialects.postgresql.base import INTERVAL
from sqlalchemy_utils.types.choice import ChoiceType

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '034a611d5a31'
down_revision = None
branch_labels = None
depends_on = None

EVENT_CHOICES = (
    ('W', 'Waiting'),
    ('C', 'Cancelled'),
    ('P', 'Passed'),
)


def upgrade():

    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(50), unique=True),
        sa.Column('email', sa.String(100), unique=True),
        sa.Column('first_name', sa.String(50)),
        sa.Column('last_name', sa.String(50)),
        sa.Column('password', sa.String(50)),
    )

    op.create_table(
        'event_statuses',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('status', ChoiceType(EVENT_CHOICES))
    )

    op.create_table(
        'labels',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(100)),
    )

    op.create_table(
        'events',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id',
                                                       name='user_id')),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('start', sa.DateTime, nullable=False),
        sa.Column('end', sa.DateTime, nullable=True),
        sa.Column('periodic', sa.Boolean, default=False),
        sa.Column('period', INTERVAL, nullable=True),
        sa.Column('next_notification', sa.DateTime, nullable=True),
        sa.Column('place', sa.Text, nullable=True),
        sa.Column('status_id', sa.Integer, sa.ForeignKey('event_statuses.id',
                                                         name='status'))
    )

    op.create_table(
        'labels_events',
        sa.Column('label_id', sa.Integer, sa.ForeignKey('labels.id')),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('events.id'))
    )

    op.create_table(
        'events_media',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('events.id',
                                                        related_name='media'))
    )


def downgrade():
    op.drop_table('events_media')
    op.drop_table('labels_events')
    op.drop_table('events')
    op.drop_table('event_statuses')
    op.drop_table('labels')
    op.drop_table('users')
