from django.test import TestCase
from django.core.urlresolvers import reverse


class HealthcheckViewTestCases(TestCase):
    def test_healthcheck_view(self):

        response = self.client.get(reverse('healthcheck'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertTemplateNotUsed(response, 'index.html')
        self.assertEqual(response.content, 'ok')
