from django.contrib import admin

from posts.models import Tag, Post, Comment


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "text_preview",
        "created_at",
        "updated_at",
    )
    search_fields = ("text", "author__user__username")
    list_filter = ("created_at", "tags")
    list_select_related = ("author__user",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "author",
        "text_preview",
        "post",
        "created_at",
    )
    search_fields = ("text", "author__user__username", "post__text")
    list_filter = ("created_at",)
    list_select_related = ("author__user", "post")
