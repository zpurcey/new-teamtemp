from django.test import TestCase

from teamtemp.tests.factories import TeamTemperatureFactory, TemperatureResponseFactory, UserFactory


class TemperatureResponseTestCases(TestCase):
    def test_response(self):
        response = TemperatureResponseFactory()
        self.assertTrue(len(response.word) > 0)
        self.assertTrue(response.score > 0)
        self.assertTrue(len(response.team_name) > 0)
        self.assertIsNotNone(response.response_date)
        self.assertIsNotNone(response.request)

    def test_multiple_responses_for_user_and_survey(self):
        user = UserFactory()
        teamtemp1 = TeamTemperatureFactory()
        teamtemp2 = TeamTemperatureFactory()
        response1 = TemperatureResponseFactory(request=teamtemp1, responder=user)
        response2 = TemperatureResponseFactory(request=teamtemp2, responder=user)
        self.assertEqual(user.temperature_responses.count(), 2)
