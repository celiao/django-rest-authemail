from django.contrib.auth import get_user_model
from rest_framework import serializers

from authemail.public_email_domains import burner_email_domains, public_email_domains


class SignupSerializer(serializers.Serializer):
    """
    Don't require email to be unique so visitor can signup multiple times,
    if misplace verification email.  Handle in view.
    """

    email = serializers.EmailField(max_length=255)

    # Support the flow where the user supply email -> verify email and then
    # add password
    password = serializers.CharField(max_length=128, default=None, required=False)
    first_name = serializers.CharField(max_length=30, default="", required=False)
    last_name = serializers.CharField(max_length=30, default="", required=False)

    def validate_email(self, value):
        """
        Pull out the email domain and check if its possibly a work email.

        If the domain exists in our dataset of public emails, its rejected.
        """
        domain_portion = value.split("@")[-1].strip()

        if (
            domain_portion in public_email_domains
            or domain_portion in burner_email_domains
        ):
            raise serializers.ValidationError("Only work emails are allowed to sign up")

        return value


class SignupVerificationSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128)


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class PasswordResetVerifiedSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=40)
    password = serializers.CharField(max_length=128)


class PasswordChangeSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=128)


class EmailChangeSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class EmailChangeVerifySerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("id", "email", "first_name", "last_name")
