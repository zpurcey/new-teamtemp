import string

import factory
import factory.fuzzy

from django.contrib.auth.hashers import make_password
from django.utils import timezone

from teamtemp import utils
from teamtemp.responses.models import TeamResponseHistory, Teams, TeamTemperature, TemperatureResponse, User, WordCloudImage


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('id',)

    id = utils.random_string(32)


class TeamTemperatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamTemperature
        django_get_or_create = ('id', 'survey_type', 'creator')

    id = utils.random_string(8)
    creator = factory.SubFactory(UserFactory)
    password = make_password('testing')


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Teams
        django_get_or_create = ('team_name',)

    request = factory.SubFactory(TeamTemperatureFactory)
    name = factory.Sequence(lambda n: 'Tag-%d' % n)


class TemperatureResponse(factory.django.DjangoModelFactory):
    class Meta:
        model = TemperatureResponse

    request = factory.SubFactory(TeamTemperatureFactory)
    responder = factory.SubFactory(UserFactory)
    score = factory.FuzzyInteger(1, 10)
    word = factory.fuzzy.FuzzyText(length=32, chars=string.ascii_letters)
    response_date = factory.LazyFunction(timezone.now())
    team = factory.SubFactory(TeamsFactory)
    team_name = factory.LazyAttribute(lambda a: a.team.team_name)


class TeamResponseHistoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TeamResponseHistory

    request = factory.SubFactory(TeamTemperatureFactory)
    average_score = factory.FuzzyFloat(1, 10)
    responder_count = factory.FuzzyInt(1,25)
    word_list = factory.LazyAttribute(lambda a: (factory.fuzzy.FuzzyText(length=factory.FuzzyInt(2,32), chars=string.ascii_letters) for i in range(1, a.responder_count))
    name = factory.Sequence(lambda n: 'Team %d' % n)
    short_desc = 'Test Team Short Description'
