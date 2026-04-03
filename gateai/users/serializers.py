from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from datetime import timedelta
import os
from django.core.mail import send_mail
from django.conf import settings
import uuid
import logging

from .models import UserSettings



User = get_user_model()
logger = logging.getLogger(__name__)

BASE_URL = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:8000")


# ----------------------------------------------------------
# Register serializer
# ----------------------------------------------------------
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password2",
            "role"
        )
        read_only_fields = ("id",)

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        validate_password(attrs["password"])

        if User.objects.filter(email__iexact=attrs["email"]).exists():
            raise serializers.ValidationError(
                {"email": "A user with that email already exists."}
            )
        return attrs

    # 🔁 CHANGED: use create_user
    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password2")

        return User.objects.create_user(
            password=password,
            **validated_data,
        )


# ----------------------------------------------------------
# User serializer (read-only)
# ❌ REMOVED duplicate definition – keep ONE
# ----------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        # Phase-A: Added is_superuser/is_staff for frontend world routing
        fields = ("id", "username", "email", "first_name", "last_name", "role", "avatar", "phone", "location", "email_verified", "is_superuser", "is_staff")
        read_only_fields = ("id", "is_superuser", "is_staff")


# ----------------------------------------------------------
# Login serializer
# ----------------------------------------------------------
class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get("identifier", "").strip()
        password = attrs.get("password")

        if not identifier or not password:
            raise serializers.ValidationError(
                {"detail": "Login and password are required."}
            )

        user = authenticate(username=identifier, password=password)

        if not user and "@" in identifier:
            try:
                u = User.objects.get(email__iexact=identifier)
                user = authenticate(username=u.username, password=password)
            except User.DoesNotExist:
                pass

        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserSerializer(user).data,
        }
# ----------------------------------------------------------
# Email verification serializer
# ----------------------------------------------------------
class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.UUIDField()

    def validate_token(self, value):
        try:
            user = User.objects.get(email_verification_token=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")

        if user.email_verification_sent_at:
            if timezone.now() - user.email_verification_sent_at > timedelta(hours=24):
                raise serializers.ValidationError("Verification link has expired.")

        self.user = user
        return value

    def save(self):
        self.user.email_verified = True
        self.user.email_verification_token = None
        self.user.email_verification_sent_at = None
        self.user.save()
        return self.user


# ----------------------------------------------------------
# Resend verification email serializer
# ----------------------------------------------------------
class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "If an account exists, a verification email will be sent."
            )

        if user.email_verified:
            raise serializers.ValidationError("Email is already verified.")

        self.user = user
        return value

    def save(self):
        if (
            self.user.email_verification_sent_at
            and timezone.now() - self.user.email_verification_sent_at
            < timedelta(minutes=5)
        ):
            raise serializers.ValidationError(
                "Please wait before requesting another verification email."
            )

        self.user.email_verification_token = uuid.uuid4()
        self.user.email_verification_sent_at = timezone.now()
        self.user.save()

        send_verification_email(self.user)
        return self.user


# ----------------------------------------------------------
# User update serializer
# ----------------------------------------------------------
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "avatar", "first_name", "last_name", "phone", "location"]

    def validate_username(self, value):
        user = self.context["request"].user

        if (
            User.objects.filter(username=value)
            .exclude(id=user.id)
            .exists()
        ):
            raise serializers.ValidationError("This username is already taken.")

        if user.username != value and user.username_updated_at:
            if timezone.now() - user.username_updated_at < timedelta(days=90):
                raise serializers.ValidationError(
                    "You can only change your username once every 3 months."
                )

        return value


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = ["data", "updated_at"]

    def update(self, instance, validated_data):
        if validated_data.get("username") != instance.username:
            validated_data["username_updated_at"] = timezone.now()
        return super().update(instance, validated_data)


# ----------------------------------------------------------
# Password reset request serializer
# ----------------------------------------------------------
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        self.user = User.objects.filter(email=value, email_verified=True).first()
        return value

    def save(self):
        if not self.user:
            return

        self.user.password_reset_token = uuid.uuid4()
        self.user.password_reset_sent_at = timezone.now()
        self.user.save()

        send_password_reset_email(self.user)


# ----------------------------------------------------------
# Password reset serializer
# ----------------------------------------------------------
class PasswordResetSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("Passwords do not match.")

        validate_password(attrs["new_password"])

        try:
            self.user = User.objects.get(password_reset_token=attrs["token"])
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid password reset token.")

        if (
            self.user.password_reset_sent_at
            and timezone.now() - self.user.password_reset_sent_at > timedelta(hours=1)
        ):
            raise serializers.ValidationError("Password reset link expired.")

        return attrs

    def save(self):
        self.user.set_password(self.validated_data["new_password"])
        self.user.password_reset_token = None
        self.user.password_reset_sent_at = None
        self.user.save()
        return self.user


# ----------------------------------------------------------
# Email helpers (minimal service extraction)
# ----------------------------------------------------------
def send_verification_email(user):
    url = f"{BASE_URL}/verify-email/{user.email_verification_token}"
    send_mail(
        "CareerBridge - Email Verification",
        f"Verify your email: {url}",
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(user):
    url = f"{BASE_URL}/reset-password/{user.password_reset_token}"
    send_mail(
        "CareerBridge - Password Reset",
        f"Reset your password: {url}",
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )
# ----------------------------------------------------------
# Password change serializer
# Handles password updates with validation
# ----------------------------------------------------------
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("The old password is incorrect")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError("The new passwords do not match")
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user
