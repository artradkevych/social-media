from typing import Type

from django.db import models
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets, status, filters, mixins, serializers
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from posts.models import Post, Comment
from posts.serializers import (
    PostSerializer,
    PostListSerializer,
    PostDetailSerializer,
    CommentSerializer,
)
from users.permissions import IsOwnerOrReadOnly


@extend_schema_view(
    list=extend_schema(
        summary="List posts",
        description="Returns a list of all posts. Use `?feed=true` to get posts from followed users only. Use `?search=` to filter by text or hashtag.",
        parameters=[
            OpenApiParameter(
                name="feed",
                description="Filter to followed users' posts",
                required=False,
                type=bool,
            ),
            OpenApiParameter(
                name="search",
                description="Search by text or tag",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="liked",
                description="Show posts liked by current user",
                required=False,
                type=bool,
            ),
        ],
    ),
    retrieve=extend_schema(summary="Get post detail"),
    create=extend_schema(summary="Create a post"),
    update=extend_schema(summary="Update a post"),
    partial_update=extend_schema(summary="Partially update a post"),
    destroy=extend_schema(summary="Delete a post"),
)
class PostViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ["tags__name", "text"]

    def get_queryset(self) -> models.QuerySet:
        user = self.request.user
        queryset = Post.objects.select_related("author__user").prefetch_related(
            "tags", "liked_by__user", "comments__author__user"
        )
        if self.request.query_params.get("liked") == "true" and user.is_authenticated:
            queryset = queryset.filter(liked_by=user.profile)

        if self.request.query_params.get("feed") == "true" and user.is_authenticated:
            queryset = queryset.filter(
                models.Q(author__in=user.profile.following.all())
                | models.Q(author=user.profile)
            )

        if user.is_authenticated:
            queryset = queryset.annotate(
                _is_liked=models.Exists(
                    Post.objects.filter(id=models.OuterRef("id"), liked_by=user.profile)
                )
            )
        else:
            queryset = queryset.annotate(
                _is_liked=models.Value(False, output_field=models.BooleanField())
            )

        return queryset.annotate(
            _likes_count=models.Count("liked_by", distinct=True)
        ).order_by("-created_at")

    def get_serializer_class(self) -> Type[serializers.Serializer]:
        if self.action == "list":
            return PostListSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostSerializer

    def get_permissions(self) -> list:
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()

    def perform_create(self, serializer: serializers.Serializer) -> None:
        serializer.save(author=self.request.user.profile)


@extend_schema_view(
    list=extend_schema(
        summary="List comments for a post",
        description="Returns all comments for the selected post.",
    ),
    retrieve=extend_schema(
        summary="Get comment detail",
    ),
    create=extend_schema(
        summary="Add a comment to a post",
    ),
    update=extend_schema(
        summary="Update comment",
    ),
    partial_update=extend_schema(
        summary="Partially update comment",
    ),
    destroy=extend_schema(
        summary="Delete comment",
    ),
)
class CommentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = CommentSerializer

    def get_queryset(self) -> models.QuerySet:
        return Comment.objects.filter(post_id=self.kwargs["post_pk"]).select_related(
            "author__user"
        )

    def perform_create(self, serializer: serializers.Serializer) -> None:
        serializer.save(
            author=self.request.user.profile, post_id=self.kwargs["post_pk"]
        )

    def get_permissions(self) -> list:
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()


class LikeView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Like or unlike a post",
        description="Toggles like on a post. Returns 201 if liked, 200 if unliked. Cannot like your own post.",
        responses={200: None, 201: None, 400: None},
    )
    def create(self, request, *args, **kwargs) -> Response:
        post = get_object_or_404(Post, pk=self.kwargs["post_pk"])
        profile = request.user.profile

        if post.author_id == profile.id:
            return Response(
                {"detail": "You cannot like your own post."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if post.liked_by.filter(id=profile.id).exists():
            post.liked_by.remove(profile)
            return Response({"detail": "Post unliked."}, status=status.HTTP_200_OK)

        post.liked_by.add(profile)
        return Response({"detail": "Post liked."}, status=status.HTTP_201_CREATED)
