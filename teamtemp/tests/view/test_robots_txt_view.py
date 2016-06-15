from django.test import TestCase
from django.core.urlresolvers import reverse


class RobotsTxtViewTestCases(TestCase):
    def test_robots_txt_view(self):

        response = self.client.get(reverse('robots_txt'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertTemplateNotUsed(response, 'index.html')
        self.assertEqual(response.content, '')
