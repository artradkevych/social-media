from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from users.models import Profile

User = get_user_model()


def make_user(username="user", email="user@example.com", password="pass1234"):
    return User.objects.create_user(username=username, email=email, password=password)


def make_profile(user, **kwargs):
    defaults = {"first_name": "John", "last_name": "Doe"}
    defaults.update(kwargs)
    return Profile.objects.create(user=user, **defaults)


def auth_client(user):
    token, _ = Token.objects.get_or_create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


class RegisterViewTest(TestCase):

    def test_register_creates_user_and_profile(self):
        data = {
            "user": {
                "username": "newuser",
                "email": "new@x.com",
                "password": "pass1234",
            },
            "first_name": "John",
            "last_name": "Doe",
        }
        response = self.client.post(
            reverse("users:register"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(email="new@x.com").exists())

    def test_register_duplicate_email_fails(self):
        make_user()
        data = {
            "user": {
                "username": "another",
                "email": "user@example.com",
                "password": "pass1234",
            },
            "first_name": "A",
            "last_name": "B",
        }
        response = self.client.post(
            reverse("users:register"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_register_no_auth_required(self):
        data = {
            "user": {"username": "u2", "email": "u2@x.com", "password": "pass1234"},
            "first_name": "A",
            "last_name": "B",
        }
        response = self.client.post(
            reverse("users:register"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 201)


class LoginViewTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_login_returns_token(self):
        data = {"email": "user@example.com", "password": "pass1234"}
        response = self.client.post(
            reverse("users:login"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)

    def test_login_wrong_password(self):
        data = {"email": "user@example.com", "password": "wrong"}
        response = self.client.post(
            reverse("users:login"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)

    def test_login_nonexistent_user(self):
        data = {"email": "nobody@x.com", "password": "pass1234"}
        response = self.client.post(
            reverse("users:login"), data, content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)


class LogoutViewTest(TestCase):

    def setUp(self):
        self.user = make_user()
        make_profile(self.user)

    def test_logout_deletes_token(self):
        client = auth_client(self.user)
        response = client.post(reverse("users:logout"))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Token.objects.filter(user=self.user).exists())

    def test_logout_requires_auth(self):
        response = self.client.post(reverse("users:logout"))
        self.assertEqual(response.status_code, 401)


def get_results(response):
    data = response.data
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


class ProfileViewSetListTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.profile = make_profile(self.user)

    def test_list_profiles_unauthenticated(self):
        response = self.client.get(reverse("users:profile-list"))
        self.assertEqual(response.status_code, 200)

    def test_list_returns_all_profiles(self):
        baseline = len(get_results(self.client.get(reverse("users:profile-list"))))
        u2 = make_user("u2", "u2@x.com")
        make_profile(u2, first_name="Jane", last_name="Smith")
        response = self.client.get(reverse("users:profile-list"))
        self.assertEqual(len(get_results(response)), baseline + 1)

    def test_search_by_username(self):
        # Use a unique username guaranteed to match only setUp user
        response = self.client.get(
            reverse("users:profile-list"), {"search": self.user.username}
        )
        self.assertEqual(response.status_code, 200)
        results = get_results(response)
        usernames = [r["user"]["username"] for r in results]
        self.assertIn(self.user.username, usernames)
        for r in results:
            self.assertIn(self.user.username.lower(), r["user"]["username"].lower())

    def test_search_no_results(self):
        unique_nonsense = "zzznobody_xyz_12345"
        response = self.client.get(
            reverse("users:profile-list"), {"search": unique_nonsense}
        )
        self.assertEqual(len(get_results(response)), 0)


class ProfileViewSetRetrieveTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.profile = make_profile(self.user)

    def test_retrieve_profile(self):
        response = self.client.get(
            reverse("users:profile-detail", kwargs={"pk": self.profile.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "John")

    def test_retrieve_includes_following_and_followers(self):
        response = self.client.get(
            reverse("users:profile-detail", kwargs={"pk": self.profile.pk})
        )
        self.assertIn("following", response.data)
        self.assertIn("followers", response.data)


class ProfileViewSetUpdateTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.profile = make_profile(self.user)
        self.client = auth_client(self.user)

    def test_partial_update_own_profile(self):
        response = self.client.patch(
            reverse("users:profile-detail", kwargs={"pk": self.profile.pk}),
            {"first_name": "Updated"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.first_name, "Updated")

    def test_update_other_profile_forbidden(self):
        u2 = make_user("u2", "u2@x.com")
        p2 = make_profile(u2, first_name="Jane", last_name="Smith")
        response = self.client.patch(
            reverse("users:profile-detail", kwargs={"pk": p2.pk}),
            {"first_name": "Hacked"},
            content_type="application/json",
        )
        self.assertIn(response.status_code, [403, 404])

    def test_update_requires_auth(self):
        anon = APIClient()
        response = anon.patch(
            reverse("users:profile-detail", kwargs={"pk": self.profile.pk}),
            {"first_name": "X"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)


class ProfileViewSetDestroyTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.profile = make_profile(self.user)

    def test_delete_own_profile_deletes_user(self):
        client = auth_client(self.user)
        user_pk = self.user.pk
        response = client.delete(
            reverse("users:profile-detail", kwargs={"pk": self.profile.pk})
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(User.objects.filter(pk=user_pk).exists())

    def test_delete_other_profile_forbidden(self):
        u2 = make_user("u2", "u2@x.com")
        p2 = make_profile(u2, first_name="Jane", last_name="Smith")
        client = auth_client(self.user)
        response = client.delete(reverse("users:profile-detail", kwargs={"pk": p2.pk}))
        self.assertIn(response.status_code, [403, 404])

    def test_delete_requires_auth(self):
        anon = APIClient()
        response = anon.delete(
            reverse("users:profile-detail", kwargs={"pk": self.profile.pk})
        )
        self.assertEqual(response.status_code, 401)


class ProfileFollowActionTest(TestCase):

    def setUp(self):
        self.user1 = make_user()
        self.user2 = make_user("u2", "u2@x.com")
        self.profile1 = make_profile(self.user1)
        self.profile2 = make_profile(self.user2, first_name="Jane", last_name="Smith")
        self.client = auth_client(self.user1)

    def test_follow_another_user(self):
        response = self.client.post(
            reverse("users:profile-follow", kwargs={"pk": self.profile2.pk})
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn(self.profile2, self.profile1.following.all())

    def test_unfollow_already_followed(self):
        self.profile1.following.add(self.profile2)
        response = self.client.post(
            reverse("users:profile-follow", kwargs={"pk": self.profile2.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.profile2, self.profile1.following.all())

    def test_cannot_follow_yourself(self):
        response = self.client.post(
            reverse("users:profile-follow", kwargs={"pk": self.profile1.pk})
        )
        self.assertEqual(response.status_code, 400)

    def test_follow_requires_auth(self):
        anon = APIClient()
        response = anon.post(
            reverse("users:profile-follow", kwargs={"pk": self.profile2.pk})
        )
        self.assertEqual(response.status_code, 401)
