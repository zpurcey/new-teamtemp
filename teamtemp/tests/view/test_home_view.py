from django.core.urlresolvers import reverse
from django.test import TestCase


class HomeViewTestCases(TestCase):
    def test_home_view(self):
        response = self.client.get(reverse('home'))
        self.assertTemplateUsed(response, 'index.html')
        self.assertEqual(response.status_code, 200)
