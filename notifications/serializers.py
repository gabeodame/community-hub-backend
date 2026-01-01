from rest_framework import serializers

from notifications.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor_username = serializers.CharField(source="actor.username", read_only=True)
    target_type = serializers.SerializerMethodField()
    target_id = serializers.IntegerField(source="object_id", read_only=True)

    class Meta:
        model = Notification
        fields = (
            "id",
            "actor_username",
            "verb",
            "target_type",
            "target_id",
            "data",
            "is_read",
            "created_at",
        )
        read_only_fields = fields

    def get_target_type(self, obj):
        if not obj.content_type:
            return None
        return obj.content_type.model
