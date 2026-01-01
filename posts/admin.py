from django.contrib import admin

from posts.models import Comment, Post, Report


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "group", "created_at")
    list_filter = ("group", "created_at")
    search_fields = ("content", "author__username")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "parent", "created_at")
    list_filter = ("created_at",)
    search_fields = ("content", "author__username")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("id", "reporter", "reason", "status", "created_at")
    list_filter = ("status", "reason", "created_at")
    search_fields = ("details", "reporter__username")
