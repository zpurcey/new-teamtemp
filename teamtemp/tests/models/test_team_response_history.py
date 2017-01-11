from django.test import TestCase

from teamtemp.tests.factories import TeamTemperatureFactory, TeamFactory, TeamResponseHistoryFactory


class TeamResponseHistoryTestCases(TestCase):
    def test_response_history(self):
        response_history = TeamResponseHistoryFactory()
        self.assertTrue(len(response_history.word_list) > 0)
        self.assertTrue(response_history.average_score > 0)
        self.assertTrue(response_history.responder_count > 0)
        self.assertTrue(len(response_history.team_name) > 0)
        self.assertIsNotNone(response_history.archive_date)
        self.assertIsNotNone(response_history.request)

    def test_multiple_response_histories(self):
        teamtemp = TeamTemperatureFactory()
        team = TeamFactory(request=teamtemp)
        response_history1 = TeamResponseHistoryFactory(request=teamtemp, team_name=team.team_name)
        response_history2 = TeamResponseHistoryFactory(request=teamtemp, team_name=team.team_name)
        self.assertEqual(teamtemp.team_response_histories.count(), 2)
