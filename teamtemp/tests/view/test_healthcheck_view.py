from django.core.urlresolvers import reverse
from django.test import TestCase


class HealthcheckViewTestCases(TestCase):
    def test_health_check_view(self):
        response = self.client.get(reverse('healthcheck'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertTemplateNotUsed(response, 'index.html')
        self.assertEqual(response.content, 'ok')
