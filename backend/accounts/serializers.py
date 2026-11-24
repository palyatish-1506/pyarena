"""Serializers for the accounts app."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Validates sign-up payloads, then delegates creation to services."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "password_confirm",
            "full_name",
            "roll_no",
            "branch",
            "year",
            "division",
        ]
        extra_kwargs = {
            "full_name": {"required": False, "allow_blank": True},
            "roll_no": {"required": False, "allow_blank": True, "allow_null": True},
            "branch": {"required": False, "allow_blank": True},
            "year": {"required": False, "allow_null": True},
            "division": {"required": False, "allow_blank": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        from .services import register_user

        return register_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    """Public profile shape returned by /auth/me/ and embedded in auth responses."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "division",
            "year",
            "branch",
            "xp",
            "level",
            "current_streak",
            "avatar_seed",
            "date_joined",
        ]
        read_only_fields = fields
