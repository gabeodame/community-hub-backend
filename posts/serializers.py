from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from posts.models import Comment, Post, Report


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "group",
            "content",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "author",
            "parent",
            "content",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "post", "author", "created_at", "updated_at")


class ReportSerializer(serializers.ModelSerializer):
    target_type = serializers.ChoiceField(choices=["post", "comment"], write_only=True)
    target_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Report
        fields = (
            "id",
            "target_type",
            "target_id",
            "reason",
            "details",
            "status",
            "created_at",
        )
        read_only_fields = ("id", "status", "created_at")

    def validate(self, attrs):
        target_type = attrs.get("target_type")
        target_id = attrs.get("target_id")
        model = Post if target_type == "post" else Comment
        target = model.objects.filter(pk=target_id, is_deleted=False).first()
        if not target:
            raise serializers.ValidationError("Target not found.")
        attrs["content_type"] = ContentType.objects.get_for_model(model)
        attrs["object_id"] = target_id
        return attrs

    def create(self, validated_data):
        validated_data.pop("target_type", None)
        validated_data.pop("target_id", None)
        return super().create(validated_data)
