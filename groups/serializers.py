from rest_framework import serializers

from groups.models import Group, Membership


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "visibility",
            "join_policy",
            "created_by",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "slug", "created_by", "created_at", "updated_at")


class MembershipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ("id", "user", "group", "role", "status", "created_at")
        read_only_fields = ("id", "user", "group", "created_at")
