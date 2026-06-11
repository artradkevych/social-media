import os
import uuid
from datetime import date
from typing import Optional

from django.contrib.auth.models import (
    AbstractUser,
    BaseUserManager,
)
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields) -> User:
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, email: str, password: Optional[str] = None, **extra_fields
    ) -> User:
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str, **extra_fields) -> User:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self) -> str:
        return self.email


def create_custom_path(instance: Profile, filename: str) -> str:
    _, extension = os.path.splitext(filename)
    return os.path.join(
        "uploads",
        "profiles",
        f"user_{instance.user_id}-{uuid.uuid4()}{extension}",
    )


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    image = models.ImageField(blank=True, upload_to=create_custom_path)
    following = models.ManyToManyField(
        "self", symmetrical=False, related_name="followers", blank=True
    )

    def clean(self) -> None:
        if self.birth_date:
            if self.birth_date > date.today():
                raise ValidationError("Birth date cannot be in the future")

    def save(self, *args, **kwargs) -> Optional[None]:
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"
