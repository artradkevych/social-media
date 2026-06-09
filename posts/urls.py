from django.urls import path, include
from rest_framework.routers import DefaultRouter
from posts.views import PostViewSet, CommentViewSet, LikeView

router = DefaultRouter()
router.register("posts", PostViewSet, basename="post")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "posts/<int:post_pk>/comments/",
        CommentViewSet.as_view({"get": "list", "post": "create"}),
        name="post-comments",
    ),
    path(
        "posts/<int:post_pk>/comments/<int:pk>/",
        CommentViewSet.as_view(
            {
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="post-comment-detail",
    ),
    path(
        "posts/<int:post_pk>/like/",
        LikeView.as_view({"post": "create"}),
        name="post-like",
    ),
]

app_name = "posts"
