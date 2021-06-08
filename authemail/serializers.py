from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from authemail.public_email_domains import burner_email_domains, public_email_domains

MIN_PASSWORD_LENGTH = getattr(settings, "AUTH_EMAIL_MIN_PASSWORD_LENGTH", 8)


class SignupSerializer(serializers.Serializer):
    """
    Don't require email to be unique so visitor can signup multiple times,
    if misplace verification email.  Handle in view.
    """

    email = serializers.EmailField(max_length=255)

    # Support the flow where the user supply email -> verify email and then
    # add password
    password = serializers.CharField(
        max_length=128, min_length=MIN_PASSWORD_LENGTH, default=None, required=False
    )
    first_name = serializers.CharField(max_length=30, default="", required=False)
    last_name = serializers.CharField(max_length=30, default="", required=False)

    def validate_email(self, value):
        """
        Pull out the email domain and check if its possibly a work email.

        If the domain exists in our dataset of public emails, its rejected.
        """
        domain_portion = value.split("@")[-1].strip().lower()

        if (
            domain_portion in public_email_domains
            or domain_portion in burner_email_domains
        ):
            raise serializers.ValidationError("Only work emails are allowed to sign up")

        return value


class SignupVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)
    email = serializers.EmailField(max_length=255)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class PasswordResetVerifiedSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)
    password = serializers.CharField(max_length=128, min_length=MIN_PASSWORD_LENGTH)


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        max_length=128, min_length=MIN_PASSWORD_LENGTH, required=False
    )
    password = serializers.CharField(max_length=128, min_length=MIN_PASSWORD_LENGTH)


class EmailChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(
        max_length=128, min_length=MIN_PASSWORD_LENGTH
    )
    email = serializers.EmailField(max_length=255)


class EmailChangeVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name")
