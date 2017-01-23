from django.core.urlresolvers import reverse

from teamtemp.tests.view.admin_only_view_testcase import AdminOnlyViewTestCase


class AdminViewTestCases(AdminOnlyViewTestCase):
    def test_no_admin_no_team_view(self):
        response = self.client.get(self.admin_url())
        self.assertIsPasswordForm(response)

    def test_admin_no_team_view(self):
        self.setUpAdmin()
        response = self.client.get(self.admin_url())
        self.assertIsNotPasswordForm(response)
        self.assertIsAdminForm(response)

    def test_no_admin_team_view(self):
        response = self.client.get(self.admin_url(for_team=True))
        self.assertIsPasswordForm(response)

    def test_admin_team_view(self):
        self.setUpAdmin()
        response = self.client.get(self.admin_url(for_team=True))
        self.assertIsNotPasswordForm(response)
        self.assertIsAdminForm(response, for_team=True)