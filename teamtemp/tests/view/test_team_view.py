from django.core.urlresolvers import reverse

from teamtemp.tests.view.admin_only_view_testcase import AdminOnlyViewTestCase


class AdminViewTestCases(AdminOnlyViewTestCase):
    def test_no_admin_existing_team_view(self):
        response = self.client.get(
            reverse('team', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}), follow=True)
        self.assertDoesAdminRedirect(response)

    def test_admin_existing_team_view(self):
        self.setUpAdmin()
        response = self.client.get(
            reverse('team', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}), follow=True)
        self.assertIsNotPasswordForm(response)
        self.assertTemplateUsed(response, 'team.html')