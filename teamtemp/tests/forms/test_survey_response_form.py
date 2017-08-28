from django.test import TestCase

from teamtemp.responses.forms import SurveyResponseForm
from teamtemp.tests.factories import TeamTemperatureFactory, TemperatureResponseFactory


class SurveyResponseFormTestCases(TestCase):
    def test_empty_survey_response_form(self):
        form = SurveyResponseForm(max_word_count=1)
        self.assertFalse(form.is_valid())

    def test_existing_survey_response_form(self):
        survey = TeamTemperatureFactory()
        response = TemperatureResponseFactory(request=survey)
        form_data = {
            'response_id': response.id,
            'survey_type_title': 'test',
            'temp_question_title': 'test',
            'word_question_title': 'test',
            'team_name': response.team_name,
            'pretty_team_name': response.pretty_team_name(),
            'id': survey.id,
            'word': response.word,
            'score': response.score,
        }
        form = SurveyResponseForm(data=form_data, max_word_count=1)
        self.assertTrue(form.is_valid())

    def test_invalid_word_survey_response_form(self):
        survey = TeamTemperatureFactory()
        form_data = {
            'response_id': None,
            'survey_type_title': 'test',
            'temp_question_title': 'test',
            'word_question_title': 'test',
            'team_name': 'test',
            'pretty_team_name': 'test',
            'id': survey.id,
            'word': 'bad!test',
            'score': 1,
        }
        form = SurveyResponseForm(data=form_data, max_word_count=1)
        self.assertFalse(form.is_valid())

    def test_invalid_score_survey_response_form(self):
        survey = TeamTemperatureFactory()
        form_data = {
            'response_id': None,
            'survey_type_title': 'test',
            'temp_question_title': 'test',
            'word_question_title': 'test',
            'team_name': 'test',
            'pretty_team_name': 'test',
            'id': survey.id,
            'word': 'test',
            'score': 11,
        }
        form = SurveyResponseForm(data=form_data, max_word_count=1)
        self.assertFalse(form.is_valid())

    def test_too_many_words_survey_response_form(self):
        survey = TeamTemperatureFactory()
        form_data = {
            'response_id': None,
            'survey_type_title': 'test',
            'temp_question_title': 'test',
            'word_question_title': 'test',
            'team_name': 'test',
            'pretty_team_name': 'test',
            'id': survey.id,
            'word': 'test one two three',
            'score': 1,
        }
        form = SurveyResponseForm(data=form_data, max_word_count=2)
        self.assertFalse(form.is_valid())
