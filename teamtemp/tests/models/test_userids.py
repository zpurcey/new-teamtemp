from django.forms import ValidationError
from django.test import TestCase, RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware

from teamtemp import responses


class UserIdTestCases(TestCase):
    def setUp(self):
        # Every test needs access to the request factory.
        self.request = RequestFactory().get('/test')

        """Annotate a request object with a session"""
        middleware = SessionMiddleware()
        middleware.process_request(self.request)
        self.request.session.save()


    def test_get_user_id(self):
        user_id = 'kjhsdafA'

        self.request.session = { 'user_id': user_id }

        self.assertEqual(responses.get_userid(self.request), user_id )

    def test_set_user_id(self):
        user_id = 'Aasdfa'

        self.assertEqual(responses.set_userid(self.request, user_id), user_id)
        self.assertEqual(responses.get_userid(self.request), user_id)

    def test_create_user_id(self):
        user_id = responses.create_userid(self.request)

        self.assertEqual(user_id, responses.get_userid(self.request))
