from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from groups.models import Group


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name="posts",
        null=True,
        blank=True,
    )
    content = models.TextField(max_length=2000)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["author"], name="posts_post_author_idx"),
            models.Index(fields=["group"], name="posts_post_group_idx"),
            models.Index(fields=["-created_at"], name="posts_post_created_idx"),
        ]

    def __str__(self) -> str:
        return f"Post({self.id})"


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="replies",
        null=True,
        blank=True,
    )
    content = models.TextField(max_length=1000)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["post"], name="posts_comment_post_idx"),
            models.Index(fields=["author"], name="posts_comment_author_idx"),
            models.Index(fields=["-created_at"], name="posts_comment_created_idx"),
        ]

    def __str__(self) -> str:
        return f"Comment({self.id})"


class Report(models.Model):
    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        HARASSMENT = "harassment", "Harassment"
        MISINFORMATION = "misinfo", "Misinformation"
        ILLEGAL = "illegal", "Illegal"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWED = "reviewed", "Reviewed"
        ACTIONED = "actioned", "Actioned"
        DISMISSED = "dismissed", "Dismissed"

    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True, max_length=1000)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["reporter", "content_type", "object_id"],
                name="uniq_reporter_target",
            )
        ]
        indexes = [
            models.Index(fields=["content_type", "object_id"], name="posts_report_target_idx"),
            models.Index(fields=["status"], name="posts_report_status_idx"),
        ]

    def __str__(self) -> str:
        return f"Report({self.reporter_id}->{self.content_type_id}:{self.object_id})"
