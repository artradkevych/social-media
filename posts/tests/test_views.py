from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from posts.models import Post
from users.models import Profile

User = get_user_model()


def make_user(username, email):
    return User.objects.create_user(
        username=username,
        email=email,
        password="pass12345",
    )


def make_profile(user):
    return Profile.objects.create(
        user=user,
        first_name="John",
        last_name="Doe",
    )


class PostViewSetTest(APITestCase):

    def setUp(self):
        self.user = make_user("user1", "u1@test.com")
        self.profile = make_profile(self.user)

        self.post = Post.objects.create(
            author=self.profile,
            text="test post",
        )

    def test_post_list(self):
        url = reverse("posts:post-list")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

    def test_authenticated_user_can_create_post(self):
        self.client.force_authenticate(self.user)

        url = reverse("posts:post-list")

        response = self.client.post(
            url,
            {
                "text": "new post",
                "tags": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

    def test_anonymous_cannot_create_post(self):
        url = reverse("posts:post-list")

        response = self.client.post(
            url,
            {
                "text": "new post",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )


class LikeViewTest(APITestCase):

    def setUp(self):
        self.user = make_user("user1", "u1@test.com")
        self.profile = make_profile(self.user)

        self.user2 = make_user("user2", "u2@test.com")
        self.profile2 = make_profile(self.user2)

        self.post = Post.objects.create(
            author=self.profile2,
            text="post",
        )

        self.client.force_authenticate(self.user)

    def test_like_post(self):
        url = reverse(
            "posts:post-like",
            kwargs={"post_pk": self.post.pk},
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(self.post.liked_by.filter(id=self.profile.id).exists())

    def test_unlike_post(self):
        self.post.liked_by.add(self.profile)

        url = reverse(
            "posts:post-like",
            kwargs={"post_pk": self.post.pk},
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(self.post.liked_by.filter(id=self.profile.id).exists())

    def test_cannot_like_own_post(self):
        own_post = Post.objects.create(
            author=self.profile,
            text="mine",
        )

        url = reverse(
            "posts:post-like",
            kwargs={"post_pk": own_post.pk},
        )

        response = self.client.post(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
