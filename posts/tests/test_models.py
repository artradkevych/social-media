from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Tag, Post, Comment
from users.models import Profile

User = get_user_model()


def make_user(username="user", email="user@test.com"):
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


class TagModelTest(TestCase):

    def test_tag_str(self):
        tag = Tag.objects.create(name="django")
        self.assertEqual(str(tag), "django")


class PostModelTest(TestCase):

    def setUp(self):
        self.profile = make_profile(make_user())

    def test_post_str_short_text(self):
        post = Post.objects.create(
            author=self.profile,
            text="Hello world",
        )

        self.assertEqual(str(post), "Hello world")

    def test_post_text_preview_long_text(self):
        text = "a" * 100

        post = Post.objects.create(
            author=self.profile,
            text=text,
        )

        self.assertEqual(
            post.text_preview,
            text[:50] + "...",
        )

    def test_post_author_relation(self):
        post = Post.objects.create(
            author=self.profile,
            text="test",
        )

        self.assertEqual(post.author, self.profile)


class CommentModelTest(TestCase):

    def setUp(self):
        self.profile = make_profile(make_user())

        self.post = Post.objects.create(
            author=self.profile,
            text="post text",
        )

    def test_comment_str(self):
        comment = Comment.objects.create(
            author=self.profile,
            post=self.post,
            text="comment",
        )

        self.assertEqual(str(comment), "comment")

    def test_comment_text_preview_long_text(self):
        text = "b" * 100

        comment = Comment.objects.create(
            author=self.profile,
            post=self.post,
            text=text,
        )

        self.assertEqual(
            comment.text_preview,
            text[:50] + "...",
        )

    def test_comment_belongs_to_post(self):
        comment = Comment.objects.create(
            author=self.profile,
            post=self.post,
            text="comment",
        )

        self.assertEqual(comment.post, self.post)
