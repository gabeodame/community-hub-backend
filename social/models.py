from django.conf import settings
from django.db import models
from django.db.models import Q, F


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["follower", "following"], name="uniq_follow"),
            models.CheckConstraint(
                condition=~Q(follower=F("following")), name="chk_follow_no_self"
            ),
        ]
        indexes = [
            models.Index(fields=["follower"]),
            models.Index(fields=["following"]),
        ]

    def __str__(self) -> str:
        return f"Follow({self.follower_id}->{self.following_id})"


class Block(models.Model):
    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocking",
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="blocked_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="uniq_block"),
            models.CheckConstraint(
                condition=~Q(blocker=F("blocked")), name="chk_block_no_self"
            ),
        ]
        indexes = [
            models.Index(fields=["blocker"]),
            models.Index(fields=["blocked"]),
        ]

    def __str__(self) -> str:
        return f"Block({self.blocker_id}x{self.blocked_id})"
