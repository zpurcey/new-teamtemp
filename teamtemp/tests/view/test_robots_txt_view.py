from django.core.urlresolvers import reverse
from django.test import TestCase


class RobotsTxtViewTestCases(TestCase):
    def test_robots_txt_view(self):
        response = self.client.get(reverse('robots_txt'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertEqual(response['Cache-Control'], 'public, max-age=86400')
        self.assertTemplateNotUsed(response, 'index.html')
        self.assertEqual(response.content, '')
