from django.core.urlresolvers import reverse
from django.test import TestCase

from teamtemp.tests.factories import TeamTemperatureFactory

class BvcViewTestCases(TestCase):
    def test_bvc_view(self):
        teamtemp = TeamTemperatureFactory()
        response = self.client.get(reverse('bvc', kwargs={'survey_id': teamtemp.id}))
        self.assertTemplateUsed(response, 'bvc.html')
        self.assertEqual(response.status_code, 200)
