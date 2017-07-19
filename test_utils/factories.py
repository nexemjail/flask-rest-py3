from datetime import timedelta

import factory
from dateutil.relativedelta import relativedelta
from factory import fuzzy
from random import randint

from test_utils.helpers import get_timezone_aware_time


class UserCreatePayloadFactory(factory.DictFactory):
    email = factory.Faker('email')
    username = factory.Sequence(lambda n: 'unique_user_{0:04}'.format(n))
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.Faker('password')
    password2 = factory.SelfAttribute('password')


def fake_user_payload():
    return UserCreatePayloadFactory()


class EventPayloadFactory(factory.DictFactory):
    description = factory.Faker('word')
    # TODO: handle C(cancelled) too
    status = fuzzy.FuzzyChoice(['W', 'P'])
    periodic = False

    @factory.lazy_attribute
    def labels(self):
        words = randint(0, 7)
        return list(set(factory.Faker('words').generate(
            extra_kwargs={'nb': words}))
        )

    @factory.lazy_attribute
    def start(self):
        start_dt = get_timezone_aware_time()
        return fuzzy.FuzzyDateTime(start_dt=get_timezone_aware_time(),
                                   end_dt=start_dt + relativedelta(years=100))\
            .fuzz()

    @factory.lazy_attribute
    def end(self):
        return fuzzy.FuzzyDateTime(
            start_dt=self.start + relativedelta(hours=1),
            end_dt=self.start + relativedelta(years=100))\
            .fuzz()


class NonPeriodicEventFactory(EventPayloadFactory):
    periodic = False


class PeriodicEventPayloadFactory(EventPayloadFactory):
    periodic = True

    @factory.lazy_attribute
    def period(self):
        return timedelta(days=randint(0, 365),
                         hours=randint(0, 59),
                         minutes=randint(0, 59),
                         seconds=randint(1, 59))

    @factory.lazy_attribute
    def end(self):
        start_datetime = self.start + relativedelta(hours=1) + self.period
        return fuzzy.FuzzyDateTime(
            start_dt=start_datetime,
            end_dt=start_datetime + relativedelta(years=100))\
            .fuzz()

    @factory.lazy_attribute
    def next_notification(self):
        return self.start + self.period
