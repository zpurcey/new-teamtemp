from django.core.urlresolvers import reverse
from django.test import TestCase

from teamtemp.tests.factories import TeamTemperatureFactory, TeamFactory

# No admin auth yet, so all admin functions should render the password form

class AdminViewTestCases(TestCase):
    def setUp(self):
        self.teamtemp = TeamTemperatureFactory()
        self.team = TeamFactory(request=self.teamtemp)
        self.admin_url = reverse('admin', kwargs={'survey_id': self.teamtemp.id})

    def _assert_password_form(self, response)
        self.assertContains(response, 'Enter the admin password')
        self.assertTemplateUsed(response, 'password.html')

    def _assert_redirects(self, response)
        self.assertRedirects(response, self.admin_url)
        self._assert_password_form(response)

    def test_admin_no_team_view(self):
        response = self.client.get(self.admin_url)
        self._assert_password_form(response)

    def test_admin_team_view(self):
        response = self.client.get(reverse('admin', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}))
        self._assert_password_form(response)

    def test_admin_set_view(self):
        response = self.client.get(reverse('set', kwargs={'survey_id': self.teamtemp.id}), follow=True)
        self._assert_redirects(response)

    def test_admin_reset_view(self):
        response = self.client.get(reverse('reset', kwargs={'survey_id': self.teamtemp.id}), follow=True)
        self._assert_redirects(response)

    def test_admin_new_team_view(self):
        response = self.client.get(reverse('team', kwargs={'survey_id': self.teamtemp.id}), follow=True)
        self._assert_redirects(response)

    def test_admin_existing_team_view(self):
        response = self.client.get(reverse('team', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}), follow=True)
        self._assert_redirects(response)
