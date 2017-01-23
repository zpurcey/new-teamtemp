from django.core.urlresolvers import reverse
from django.test import TestCase


class UserViewTestCases(TestCase):
    def test_user_page_view(self):
        response = self.client.get(reverse('user'))
        self.assertTemplateNotUsed(response, 'user.html')
        self.assertEqual(response.status_code, 404)
