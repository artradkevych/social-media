from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from users.models import Profile
from users.serializers import (
    CustomAuthTokenSerializer,
    UserSerializer,
    UserPublicSerializer,
    ProfileFollowSerializer,
    ProfileListSerializer,
    ProfileDetailSerializer,
    ProfileWriteSerializer,
    RegisterSerializer,
)

User = get_user_model()


def make_user(username="user", email="user@example.com", password="pass1234"):
    return User.objects.create_user(username=username, email=email, password=password)


def make_profile(user, **kwargs):
    defaults = {"first_name": "John", "last_name": "Doe"}
    defaults.update(kwargs)
    return Profile.objects.create(user=user, **defaults)


class CustomAuthTokenSerializerTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.factory = RequestFactory()

    def _context(self):
        return {"request": self.factory.post("/login/")}

    def test_valid_credentials(self):
        data = {"email": "user@example.com", "password": "pass1234"}
        s = CustomAuthTokenSerializer(data=data, context=self._context())
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["user"], self.user)

    def test_wrong_password(self):
        data = {"email": "user@example.com", "password": "wrong"}
        s = CustomAuthTokenSerializer(data=data, context=self._context())
        self.assertFalse(s.is_valid())

    def test_missing_email(self):
        s = CustomAuthTokenSerializer(
            data={"password": "pass1234"}, context=self._context()
        )
        self.assertFalse(s.is_valid())

    def test_missing_password(self):
        s = CustomAuthTokenSerializer(
            data={"email": "user@example.com"}, context=self._context()
        )
        self.assertFalse(s.is_valid())


class UserSerializerTest(TestCase):

    def test_create_user(self):
        data = {"username": "newuser", "email": "new@x.com", "password": "secure123"}
        s = UserSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        user = s.save()
        self.assertTrue(user.check_password("secure123"))
        self.assertEqual(user.email, "new@x.com")

    def test_password_write_only(self):
        user = make_user()
        s = UserSerializer(user)
        self.assertNotIn("password", s.data)

    def test_password_min_length_validation(self):
        data = {"username": "u", "email": "u@x.com", "password": "short"}
        s = UserSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("password", s.errors)

    def test_update_user_password(self):
        user = make_user()
        s = UserSerializer(user, data={"password": "newpassword1"}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        s.save()
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpassword1"))


class UserPublicSerializerTest(TestCase):

    def test_exposes_only_id_and_username(self):
        user = make_user()
        s = UserPublicSerializer(user)
        self.assertEqual(set(s.data.keys()), {"id", "username"})
        self.assertNotIn("email", s.data)


class ProfileFollowSerializerTest(TestCase):

    def test_exposes_username_from_user(self):
        user = make_user()
        profile = make_profile(user)
        s = ProfileFollowSerializer(profile)
        self.assertEqual(s.data["username"], user.username)
        self.assertEqual(set(s.data.keys()), {"id", "username"})


class ProfileListSerializerTest(TestCase):

    def test_fields_present(self):
        user = make_user()
        profile = make_profile(user)
        s = ProfileListSerializer(profile)
        expected = {
            "id",
            "user",
            "first_name",
            "last_name",
            "following_count",
            "followers_count",
        }
        self.assertEqual(set(s.data.keys()), expected)

    def test_following_count_zero(self):
        user = make_user()
        profile = make_profile(user)
        s = ProfileListSerializer(profile)
        self.assertEqual(s.data["following_count"], 0)
        self.assertEqual(s.data["followers_count"], 0)

    def test_following_count_after_follow(self):
        u1 = make_user()
        u2 = make_user("u2", "u2@x.com")
        p1 = make_profile(u1)
        p2 = make_profile(u2, first_name="Jane", last_name="Smith")
        p1.following.add(p2)
        s = ProfileListSerializer(p1)
        self.assertEqual(s.data["following_count"], 1)


class ProfileDetailSerializerTest(TestCase):

    def test_fields_present(self):
        user = make_user()
        profile = make_profile(user)
        s = ProfileDetailSerializer(profile)
        expected = {
            "id",
            "user",
            "first_name",
            "last_name",
            "bio",
            "location",
            "birth_date",
            "image",
            "following",
            "followers",
        }
        self.assertEqual(set(s.data.keys()), expected)

    def test_following_list(self):
        u1 = make_user()
        u2 = make_user("u2", "u2@x.com")
        p1 = make_profile(u1)
        p2 = make_profile(u2, first_name="Jane", last_name="Smith")
        p1.following.add(p2)
        s = ProfileDetailSerializer(p1)
        self.assertEqual(len(s.data["following"]), 1)
        self.assertEqual(s.data["following"][0]["username"], u2.username)


class ProfileWriteSerializerTest(TestCase):

    def test_valid_data(self):
        data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "bio": "Hello",
            "location": "Kyiv",
            "birth_date": "1990-05-15",
        }
        s = ProfileWriteSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_all_optional_except_names(self):
        s = ProfileWriteSerializer(data={"first_name": "A", "last_name": "B"})
        self.assertTrue(s.is_valid(), s.errors)


class RegisterSerializerTest(TestCase):

    def _valid_data(self, username="newuser", email="new@example.com"):
        return {
            "user": {
                "username": username,
                "email": email,
                "password": "securepass123",
            },
            "first_name": "John",
            "last_name": "Doe",
        }

    def test_creates_user_and_profile(self):
        s = RegisterSerializer(data=self._valid_data())
        self.assertTrue(s.is_valid(), s.errors)
        profile = s.save()
        self.assertIsInstance(profile, Profile)
        self.assertEqual(profile.user.email, "new@example.com")
        self.assertTrue(profile.user.check_password("securepass123"))

    def test_duplicate_email_fails(self):
        make_user(email="new@example.com")
        s = RegisterSerializer(data=self._valid_data())
        self.assertFalse(s.is_valid())

    def test_optional_profile_fields(self):
        data = self._valid_data()
        data["bio"] = "Hello world"
        data["location"] = "Lviv"
        s = RegisterSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        profile = s.save()
        self.assertEqual(profile.bio, "Hello world")
        self.assertEqual(profile.location, "Lviv")

    def test_future_birth_date_fails(self):
        data = self._valid_data()
        data["birth_date"] = str(date.today() + timedelta(days=10))
        s = RegisterSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        with self.assertRaises(Exception):
            s.save()
