from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    class Meta:
        model = User
        fields = ("username", "email", "password", "display_name")

    def validate(self, attrs):
        username = attrs.get("username")
        email = attrs.get("email")

        if User.objects.filter(username=username).exists() or (
            email and User.objects.filter(email=email).exists()
        ):
            raise serializers.ValidationError(
                {"detail": "Unable to register with provided credentials."}
            )

        try:
            validate_password(attrs.get("password"))
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "display_name")
        read_only_fields = ("id", "username")
