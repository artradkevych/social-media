from django.contrib.admin.sites import AdminSite
from django.test import TestCase, RequestFactory

from django.contrib.auth import get_user_model

from users.admin import UserAdmin, ProfileAdmin
from users.models import Profile

User = get_user_model()


def make_superuser():
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass"
    )


def make_user(username="user", email="user@example.com"):
    return User.objects.create_user(username=username, email=email, password="pass123")


def make_profile(user, **kwargs):
    defaults = {"first_name": "John", "last_name": "Doe", "location": "Kyiv"}
    defaults.update(kwargs)
    return Profile.objects.create(user=user, **defaults)


class UserAdminTest(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin = UserAdmin(User, self.site)
        self.superuser = make_superuser()
        self.factory = RequestFactory()

    def test_list_display(self):
        self.assertIn("email", self.admin.list_display)
        self.assertIn("is_staff", self.admin.list_display)

    def test_search_fields(self):
        self.assertIn("email", self.admin.search_fields)

    def test_ordering_by_email(self):
        self.assertEqual(self.admin.ordering, ("email",))

    def test_fieldsets_contain_email(self):
        fieldset_fields = [
            field
            for _, opts in self.admin.fieldsets
            for field in opts.get("fields", [])
        ]
        self.assertIn("email", fieldset_fields)

    def test_fieldsets_contain_username(self):
        fieldset_fields = [
            field
            for _, opts in self.admin.fieldsets
            for field in opts.get("fields", [])
        ]
        self.assertIn("username", fieldset_fields)

    def test_add_fieldsets_contain_email(self):
        add_fields = [
            field
            for _, opts in self.admin.add_fieldsets
            for field in opts.get("fields", [])
        ]
        self.assertIn("email", add_fields)

    def test_get_queryset_returns_users(self):
        request = self.factory.get("/admin/users/user/")
        request.user = self.superuser
        qs = self.admin.get_queryset(request)
        self.assertIn(self.superuser, qs)

    def test_changelist_view_accessible(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/users/user/")
        self.assertEqual(response.status_code, 200)

    def test_changeform_view_accessible(self):
        self.client.force_login(self.superuser)
        response = self.client.get(f"/admin/users/user/{self.superuser.pk}/change/")
        self.assertEqual(response.status_code, 200)


class ProfileAdminTest(TestCase):

    def setUp(self):
        self.site = AdminSite()
        self.admin = ProfileAdmin(Profile, self.site)
        self.superuser = make_superuser()
        self.user = make_user()
        self.profile = make_profile(self.user)
        self.factory = RequestFactory()

    def test_list_display(self):
        for field in ("id", "user", "first_name", "last_name", "location"):
            self.assertIn(field, self.admin.list_display)

    def test_search_fields(self):
        for field in ("first_name", "last_name", "user__username", "user__email", "location"):
            self.assertIn(field, self.admin.search_fields)

    def test_list_filter(self):
        self.assertIn("location", self.admin.list_filter)

    def test_ordering(self):
        self.assertEqual(self.admin.ordering, ("-id",))

    def test_filter_horizontal_following(self):
        self.assertIn("following", self.admin.filter_horizontal)

    def test_list_select_related(self):
        self.assertIn("user", self.admin.list_select_related)

    def test_changelist_view_accessible(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/users/profile/")
        self.assertEqual(response.status_code, 200)

    def test_changeform_view_accessible(self):
        self.client.force_login(self.superuser)
        response = self.client.get(f"/admin/users/profile/{self.profile.pk}/change/")
        self.assertEqual(response.status_code, 200)

    def test_search_by_first_name(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/admin/users/profile/?q=John")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John")

    def test_get_queryset_contains_profile(self):
        request = self.factory.get("/admin/users/profile/")
        request.user = self.superuser
        qs = self.admin.get_queryset(request)
        self.assertIn(self.profile, qs)
