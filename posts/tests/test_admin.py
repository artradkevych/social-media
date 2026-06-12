from django.contrib import admin
from django.test import TestCase

from posts.admin import TagAdmin, PostAdmin, CommentAdmin
from posts.models import Tag, Post, Comment


class AdminRegistrationTest(TestCase):

    def test_tag_registered(self):
        self.assertIsInstance(
            admin.site._registry[Tag],
            TagAdmin,
        )

    def test_post_registered(self):
        self.assertIsInstance(
            admin.site._registry[Post],
            PostAdmin,
        )

    def test_comment_registered(self):
        self.assertIsInstance(
            admin.site._registry[Comment],
            CommentAdmin,
        )


class AdminConfigTest(TestCase):

    def test_tag_admin_search_fields(self):
        self.assertEqual(
            TagAdmin.search_fields,
            ("name",),
        )

    def test_post_admin_list_display(self):
        self.assertIn("author", PostAdmin.list_display)
        self.assertIn("text_preview", PostAdmin.list_display)

    def test_comment_admin_list_display(self):
        self.assertIn("author", CommentAdmin.list_display)
        self.assertIn("post", CommentAdmin.list_display)
