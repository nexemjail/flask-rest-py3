import factory


class UserCreatePayloadFactory(factory.DictFactory):
    email = factory.Faker('email')
    username = factory.Sequence(lambda n: 'unique_user_{0:04}'.format(n))
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    password = factory.Faker('password')
    password2 = factory.SelfAttribute('password')


def fake_user_payload():
    return UserCreatePayloadFactory()
