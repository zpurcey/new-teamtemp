from django.test import TestCase


class MediaViewTestCases(TestCase):
    def test_media_view(self):
        response = self.client.get('/media/test.png')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertEqual(response['Cache-Control'], 'public, max-age=315360000')
        self.assertTemplateNotUsed(response, 'index.html')
        self.assertGreater(len(response.getvalue()), 0)
