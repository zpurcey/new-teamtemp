from rest_framework import serializers
from models import User, TeamTemperature, TemperatureResponse, TeamResponseHistory, Teams, WordCloudImage


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('id',)


class WordCloudImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WordCloudImage
        fields = ('creation_date', 'word_list', 'image_url')


class TeamTemperatureSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TeamTemperature
        fields = ('id', 'creation_date', 'creator', 'archive_schedule',
                    'archive_date', 'survey_type', 'default_tz',
                    'max_word_count', 'dept_names', 'site_names',
		    'region_names', 'teams', 'team_response_histories',
		    'temperature_responses')


class TemperatureResponseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TemperatureResponse
        fields = ('request', 'responder', 'score', 'word', 'team_name',
                    'archived', 'response_date', 'archive_date')


class TeamSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Teams
        fields = ('request', 'team_name', 'dept_name', 'site_name',
                    'region_name')


class TeamResponseHistorySerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TeamResponseHistory
        fields = ('request', 'average_score', 'word_list', 'responder_count',
                    'team_name', 'archive_date')


