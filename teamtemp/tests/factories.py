import string

import factory
import factory.fuzzy

from django.contrib.auth.hashers import make_password

from teamtemp import utils
from teamtemp.responses.models import TeamResponseHistory, Teams, TeamTemperature, TemperatureResponse, User, WordCloudImage

# request.session[USER_ID_KEY] = utils.random_string(32)

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
    responder = factory.SubFactory(UserFactory)
    score = factory.Sequence(lambda n: n%10 + 1)
    word = factory.fuzzy.FuzzyText(length=32, chars=string.ascii_letters)
    response_date = 
    team_name = factory.SubFactory(TeamsFactory).team_name


class TemperatureResponse(factory.django.DjangoModelFactory):
    class Meta:
        model = TemperatureResponse

    request = factory.SubFactory(TeamTemperatureFactory)
    name = factory.Sequence(lambda n: 'Tag-%d' % n)


class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: 'Team %d' % n)
    short_desc = 'Test Team Short Description'

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # A list of groups were passed in, use them
            for tag in extracted:
                self.tags.add(tag)


class AssessmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Assessment

    template = factory.SubFactory(TemplateFactory)
    team = factory.SubFactory(TeamFactory)

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            # A list of groups were passed in, use them
            for tag in extracted:
                self.tags.add(tag)


class RatingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Rating

    attribute = factory.SubFactory(AttributeFactory)
    name = factory.Sequence(lambda n: 'Rating %d' % n)
    desc = "This is a really good description."
    rank = factory.Sequence(lambda n: n)


class MeasurementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Measurement

    assessment = factory.SubFactory(AssessmentFactory)
    rating = factory.SubFactory(RatingFactory)
    observations = factory.fuzzy.FuzzyText(length=256, chars=string.ascii_letters)


class AnnouncementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Announcement

    title = factory.Sequence(lambda n: 'Announcement-%d' % n)
    content = "This is the really good content for %s\n" % title

