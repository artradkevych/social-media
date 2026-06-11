from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from users.models import Profile

User = get_user_model()


def make_user(username="testuser", email="test@example.com", password="testpass123"):
    return User.objects.create_user(
        username=username, email=email, password=password
    )


def make_profile(user, **kwargs):
    defaults = {"first_name": "John", "last_name": "Doe"}
    defaults.update(kwargs)
    return Profile.objects.create(user=user, **defaults)


class UserManagerTest(TestCase):

    def test_create_user_sets_email(self):
        user = make_user()
        self.assertEqual(user.email, "test@example.com")

    def test_create_user_without_email_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email="", password="pass")

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            username="u2", email="Test@EXAMPLE.COM", password="pass"
        )
        self.assertEqual(user.email, "Test@example.com")

    def test_create_user_is_not_staff(self):
        user = make_user()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser_flags(self):
        su = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_superuser)

    def test_create_superuser_non_staff_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                username="x",
                email="x@x.com",
                password="pass",
                is_staff=False,
            )

    def test_create_superuser_non_superuser_raises(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                username="x",
                email="x@x.com",
                password="pass",
                is_superuser=False,
            )

    def test_user_str(self):
        user = make_user()
        self.assertEqual(str(user), "test@example.com")

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_required_fields_contains_username(self):
        self.assertIn("username", User.REQUIRED_FIELDS)


class ProfileModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.profile = make_profile(self.user)

    def test_profile_str(self):
        self.assertEqual(str(self.profile), "John Doe")

    def test_profile_links_to_user(self):
        self.assertEqual(self.profile.user, self.user)

    def test_birth_date_in_future_raises(self):
        self.profile.birth_date = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self.profile.full_clean()

    def test_birth_date_today_is_valid(self):
        self.profile.birth_date = date.today()
        try:
            self.profile.full_clean()
        except ValidationError:
            self.fail("full_clean() raised ValidationError for today's date")

    def test_birth_date_in_past_is_valid(self):
        self.profile.birth_date = date(1990, 1, 1)
        self.profile.full_clean()  # should not raise

    def test_bio_and_location_optional(self):
        p = Profile.objects.create(user=make_user("u2", "u2@x.com"), first_name="A", last_name="B")
        self.assertEqual(p.bio, "")
        self.assertEqual(p.location, "")

    def test_following_follow_and_unfollow(self):
        user2 = make_user("user2", "u2@x.com")
        profile2 = make_profile(user2, first_name="Jane", last_name="Smith")

        self.profile.following.add(profile2)
        self.assertIn(profile2, self.profile.following.all())
        self.assertIn(self.profile, profile2.followers.all())

        self.profile.following.remove(profile2)
        self.assertNotIn(profile2, self.profile.following.all())

    def test_following_is_not_symmetrical(self):
        user2 = make_user("user2", "u2@x.com")
        profile2 = make_profile(user2, first_name="Jane", last_name="Smith")

        self.profile.following.add(profile2)
        self.assertNotIn(self.profile, profile2.following.all())

    def test_deleting_user_cascades_to_profile(self):
        profile_id = self.profile.pk
        self.user.delete()
        self.assertFalse(Profile.objects.filter(pk=profile_id).exists())
