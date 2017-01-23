from django.core.urlresolvers import reverse
from django.test import TestCase

from teamtemp import responses
from teamtemp.tests.factories import TeamTemperatureFactory, TeamFactory


class AdminViewTestCases(TestCase):
    def setUp(self):
        self.teamtemp = TeamTemperatureFactory()
        self.team = TeamFactory(request=self.teamtemp)
        self.admin_url = reverse('admin', kwargs={'survey_id': self.teamtemp.id})

    def assertIsPasswordForm(self, response):
        self.assertContains(response, 'Enter the admin password')
        self.assertTemplateUsed(response, 'password.html')

    def assertDoesAdminRedirect(self, response):
        self.assertRedirects(response, self.admin_url)
        self.assertIsPasswordForm(response)

    def setUpAdmin(self):
        session = self.client.session
        session[responses.ADMIN_KEY] = [self.teamtemp.id]
        session.save()

    def test_no_admin_no_team_view(self):
        response = self.client.get(self.admin_url)
        self.assertIsPasswordForm(response)

    def test_admin_no_team_view(self):
        self.setUpAdmin()
        response = self.client.get(self.admin_url)
        self.assertContains(response, "Admin %s" % self.teamtemp.id)
        self.assertTemplateUsed(response, 'results.html')

    def test_no_admin_team_view(self):
        response = self.client.get(
            reverse('admin', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}))
        self.assertIsPasswordForm(response)

    def test_admin_team_view(self):
        self.setUpAdmin()
        response = self.client.get(
            reverse('admin', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}))
        self.assertContains(response, "Admin %s %s" % (self.teamtemp.id, self.team.team_name))
        self.assertTemplateUsed(response, 'results.html')

    def test_no_admin_per_survey_views(self):
        for view in ['set', 'reset', 'team']:
            response = self.client.get(reverse(view, kwargs={'survey_id': self.teamtemp.id}), follow=True)
            self.assertDoesAdminRedirect(response)

    def test_admin_per_survey_views(self):
        self.setUpAdmin()
        for view in ['set', 'team']:
            response = self.client.get(reverse(view, kwargs={'survey_id': self.teamtemp.id}), follow=True)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "%s.html" % view)

    def test_admin_reset_view(self):
        self.setUpAdmin()
        response = self.client.get(reverse('reset', kwargs={'survey_id': self.teamtemp.id}), follow=True)
        self.assertRedirects(response, self.admin_url)
        self.assertContains(response, "Admin %s" % self.teamtemp.id)
        self.assertTemplateUsed(response, 'results.html')

    def test_no_admin_existing_team_view(self):
        response = self.client.get(
            reverse('team', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}), follow=True)
        self.assertDoesAdminRedirect(response)

    def test_admin_existing_team_view(self):
        self.setUpAdmin()
        response = self.client.get(
            reverse('team', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'team.html')