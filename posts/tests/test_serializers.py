from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from posts.models import Tag, Post
from posts.serializers import (
    TagSerializer,
    PostSerializer,
    PostListSerializer,
)
from users.models import Profile

User = get_user_model()


def make_profile():
    user = User.objects.create_user(
        username="user",
        email="user@test.com",
        password="pass12345",
    )

    return Profile.objects.create(
        user=user,
        first_name="John",
        last_name="Doe",
    )


class TagSerializerTest(TestCase):

    def test_serializer_fields(self):
        tag = Tag.objects.create(name="django")

        data = TagSerializer(tag).data

        self.assertEqual(data["name"], "django")
        self.assertIn("id", data)


class PostSerializerTest(TestCase):

    def setUp(self):
        self.profile = make_profile()

    def test_create_post_serializer(self):
        tag = Tag.objects.create(name="python")

        serializer = PostSerializer(
            data={
                "text": "test post",
                "tags": ["python"],
            }
        )

        self.assertTrue(serializer.is_valid())

    def test_post_list_serializer_contains_preview(self):
        post = Post.objects.create(
            author=self.profile,
            text="hello world",
        )

        data = PostListSerializer(post).data

        self.assertIn("text_preview", data)

    def test_creatable_slug_field_creates_tag(self):
        serializer = PostSerializer(
            data={
                "text": "post",
                "tags": ["newtag"],
            }
        )

        self.assertTrue(serializer.is_valid())

        serializer.save(author=self.profile)

        self.assertTrue(Tag.objects.filter(name="newtag").exists())
