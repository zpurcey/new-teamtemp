from django.core.urlresolvers import reverse
from django.test import TestCase

from teamtemp import responses
from teamtemp.tests.factories import TeamTemperatureFactory, TeamFactory


class AdminOnlyViewTestCase(TestCase):
    def setUp(self):
        self.teamtemp = TeamTemperatureFactory()
        self.team = TeamFactory(request=self.teamtemp)

    def admin_url(self, for_team=False):
        if for_team:
            return reverse('admin', kwargs={'survey_id': self.teamtemp.id, 'team_name': self.team.team_name})
        else:
            return reverse('admin', kwargs={'survey_id': self.teamtemp.id})

    def assertIsPasswordForm(self, response):
        self.assertContains(response, 'Enter the admin password')
        self.assertTemplateUsed(response, 'password.html')

    def assertIsNotPasswordForm(self, response):
        self.assertNotContains(response, 'Enter the admin password')
        self.assertTemplateNotUsed(response, 'password.html')

    def assertIsAdminForm(self, response, for_team=False):
        if for_team:
            self.assertContains(response, "Admin %s %s" % (self.teamtemp.id, self.team.team_name))
        else:
            self.assertContains(response, "Admin %s" % self.teamtemp.id)
        self.assertTemplateUsed(response, 'results.html')

    def assertDoesAdminRedirect(self, response):
        self.assertRedirects(response, self.admin_url())
        self.assertIsPasswordForm(response)

    def setUpAdmin(self):
        session = self.client.session
        session[responses.ADMIN_KEY] = [self.teamtemp.id]
        session.save()