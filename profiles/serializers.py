from rest_framework import serializers

from profiles.models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("id", "bio", "avatar_url", "is_private", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")
