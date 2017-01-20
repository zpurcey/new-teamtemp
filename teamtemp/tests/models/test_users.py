from django.forms import ValidationError
from django.test import TestCase

from teamtemp.tests.factories import UserFactory


class UserTestCases(TestCase):
    def test_user_id(self):
        user = UserFactory()
        self.assertTrue(len(user.id) > 0)
        self.assertIsNotNone(user.creation_date)
        self.assertEqual(str(user), "%s: %s" % (user.id, user.creation_date))

    def test_uniq_user_ids(self):
        user1 = UserFactory()
        user2 = UserFactory()
        self.assertNotEqual(user1.id, user2.id)

    def test_duplicate_user_ids(self):
        with self.assertRaises(ValidationError):
            _ = UserFactory(id='bob')
            _ = UserFactory(id='bob')
