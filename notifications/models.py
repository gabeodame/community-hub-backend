from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):
    class Verb(models.TextChoices):
        FOLLOWED = "followed", "Followed"
        GROUP_APPROVED = "group_approved", "Group approved"
        COMMENTED = "commented", "Commented"
        REPLIED = "replied", "Replied"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="notifications_sent",
        null=True,
        blank=True,
    )
    verb = models.CharField(max_length=40, choices=Verb.choices)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["recipient", "is_read"], name="notif_recipient_read_idx"),
            models.Index(fields=["created_at"], name="notif_created_idx"),
            models.Index(fields=["recipient", "created_at"], name="notif_recipient_created_idx"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Notification({self.recipient_id}:{self.verb})"
