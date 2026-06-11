import os
import uuid

from django.db import models

from users.models import Profile


def create_custom_path(instance, filename):
    _, extension = os.path.splitext(filename)
    return os.path.join(
        "uploads",
        "posts",
        f"post_{uuid.uuid4()}{extension}",
    )


class Tag(models.Model):
    name = models.CharField(max_length=75, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    PREVIEW_LENGTH = 50
    author = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="posts")
    text = models.TextField()
    tags = models.ManyToManyField(Tag, related_name="posts", blank=True)
    image = models.ImageField(null=True, upload_to=create_custom_path)
    liked_by = models.ManyToManyField(Profile, related_name="liked_posts", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text_preview

    @property
    def text_preview(self):
        if len(self.text) <= self.PREVIEW_LENGTH:
            return self.text

        return self.text[: self.PREVIEW_LENGTH] + "..."


class Comment(models.Model):
    PREVIEW_LENGTH = 50
    author = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")

    def __str__(self):
        return self.text_preview

    @property
    def text_preview(self):
        if len(self.text) <= self.PREVIEW_LENGTH:
            return self.text

        return self.text[: self.PREVIEW_LENGTH] + "..."
