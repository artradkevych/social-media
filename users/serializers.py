from typing import Dict, Any

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from users.models import Profile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "password",
        )
        extra_kwargs = {
            "password": {
                "write_only": True,
                "min_length": 8,
                "style": {"input_type": "password"},
                "label": "Password",
            }
        }

    def create(self, validated_data: Dict[str, Any]) -> User:
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance: User, validated_data: Dict[str, Any]) -> User:
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
        )


class ProfileFollowSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")

    class Meta:
        model = Profile
        fields = ("id", "username")


class ProfileListSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    following_count = serializers.IntegerField(source="following.count", read_only=True)
    followers_count = serializers.IntegerField(source="followers.count", read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "user",
            "first_name",
            "last_name",
            "following_count",
            "followers_count",
        )


class ProfileDetailSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    following = ProfileFollowSerializer(many=True, read_only=True)
    followers = ProfileFollowSerializer(many=True, read_only=True)

    class Meta:
        model = Profile
        fields = (
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
        )


class ProfileWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = (
            "first_name",
            "last_name",
            "bio",
            "location",
            "birth_date",
            "image",
        )


class RegisterSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Profile
        fields = (
            "user",
            "first_name",
            "last_name",
            "bio",
            "location",
            "birth_date",
            "image",
        )

    def create(self, validated_data: Dict[str, Any]) -> Profile:
        user_data = validated_data.pop("user")
        with transaction.atomic():
            user_serializer = UserSerializer(data=user_data)
            user_serializer.is_valid(raise_exception=True)
            user = user_serializer.save()
            profile = Profile.objects.create(user=user, **validated_data)
        return profile
