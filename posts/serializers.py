from rest_framework import serializers

from posts.models import Comment, Post, Tag
from users.serializers import ProfileListSerializer


class CreatableSlugRelatedField(serializers.SlugRelatedField):
    def to_internal_value(self, data):
        queryset = self.get_queryset()

        try:
            obj, _ = queryset.get_or_create(**{self.slug_field: data})
            return obj

        except (TypeError, ValueError):
            self.fail("invalid")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name")


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()

    class Meta:
        model = Comment
        fields = ("id", "author", "text", "created_at", "updated_at")


class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.user.username")
    tags = CreatableSlugRelatedField(
        many=True, queryset=Tag.objects.all(), slug_field="name"
    )

    class Meta:
        model = Post
        fields = ("id", "author", "text", "image", "tags", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class PostListSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    likes_count = serializers.IntegerField(source="liked_by.count", read_only=True)
    is_liked = serializers.SerializerMethodField()
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")

    class Meta:
        model = Post
        fields = (
            "id",
            "text_preview",
            "image",
            "created_at",
            "author",
            "tags",
            "likes_count",
            "is_liked",
        )

    def get_is_liked(self, obj):
        request = self.context.get("request")
        profile = getattr(request.user, "profile", None)
        if not profile:
            return False
        return obj.liked_by.filter(id=profile.id).exists()


class PostDetailSerializer(serializers.ModelSerializer):
    author = ProfileListSerializer(read_only=True)
    liked_by = ProfileListSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    likes_count = serializers.IntegerField(source="_likes_count", read_only=True)
    is_liked = serializers.BooleanField(source="_is_liked", read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "text",
            "image",
            "created_at",
            "author",
            "tags",
            "likes_count",
            "is_liked",
            "liked_by",
            "comments",
        )
