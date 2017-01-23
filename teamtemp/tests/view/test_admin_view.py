from django.core.urlresolvers import reverse
from django.test import TestCase

from teamtemp.tests.factories import TeamTemperatureFactory, TeamFactory

# No admin auth yet, so all admin functions should render the password form

class AdminViewTestCases(TestCase):
    def setUp(self):
        self.teamtemp = TeamTemperatureFactory()
        self.team = TeamFactory(request=self.teamtemp)
        self.admin_url = reverse('admin', kwargs={'survey_id': self.teamtemp.id})

    def test_admin_view(self):
        response = self.client.get(self.admin_url)
        self.assertContains(response, 'Enter the admin password')
        self.assertTemplateUsed(response, 'password.html')

    def test_admin_team_view(self):
        response = self.client.get(reverse('admin', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}))
        self.assertContains(response, 'Enter the admin password')
        self.assertTemplateUsed(response, 'password.html')

    def test_admin_set_view(self):
        response = self.client.get(reverse('set', kwargs={'survey_id': self.teamtemp.id}), follow=True)
        self.assertRedirects(response, self.admin_url)
        self.assertContains(response, 'Enter the admin password')
        self.assertTemplateUsed(response, 'password.html')

    def test_admin_set_view(self):
        response = self.client.get(reverse('reset', kwargs={'survey_id': self.teamtemp.id}), follow=True)
        self.assertRedirects(response, self.admin_url)
        self.assertContains(response, 'Enter the admin password')
        self.assertTemplateUsed(response, 'password.html')

    def test_new_team_view(self):
        response = self.client.get(reverse('team', kwargs={'survey_id': self.teamtemp.id}), follow=True)
        self.assertRedirects(response, self.admin_url)
        self.assertContains(response, 'Enter the admin password')
        self.assertTemplateUsed(response, 'password.html')

    def test_team_view(self):
        response = self.client.get(reverse('team', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name}), follow=True)
        self.assertRedirects(response, self.admin_url)
        self.assertContains(response, 'Enter the admin password')
        self.assertTemplateUsed(response, 'password.html')
