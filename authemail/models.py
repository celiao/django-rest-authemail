import binascii
import os
import uuid
from datetime import date
from typing import Optional

import mmh3
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.mail import send_mail
from django.core.mail.message import EmailMultiAlternatives
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from ua_parser import user_agent_parser

EXPIRY_PERIOD = getattr(settings, "AUTH_EMAIL_VERIFICATION_EXPIRATION", 3)  # days
STRICT_USER_AGENT_VERIFICATION = getattr(settings, "AUTH_EMAIL_STRICT_UA_CHECK", False)
ASYNC_ENABLED = apps.is_installed("django_q") and getattr(
    settings, "AUTH_EMAIL_ASYNC", True
)


def _generate_code():
    return binascii.hexlify(os.urandom(20)).decode("utf-8")


class EmailUserManager(BaseUserManager):
    def _create_user(
        self, email, password, is_staff, is_superuser, is_verified, **extra_fields
    ):
        """
        Creates and saves a User with a given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            is_staff=is_staff,
            is_active=True,
            is_superuser=is_superuser,
            is_verified=is_verified,
            last_login=now,
            date_joined=now,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, True, **extra_fields)


class EmailAbstractUser(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Email and password are required. Other fields are optional.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(_("first name"), max_length=30, blank=True)
    last_name = models.CharField(_("last name"), max_length=30, blank=True)
    email = models.EmailField(_("email address"), max_length=255, unique=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this " "admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as "
            "active.  Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)

    is_verified = models.BooleanField(
        _("verified"),
        default=False,
        help_text=_(
            "Designates whether this user has completed the email "
            "verification process to allow login."
        ),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        abstract = True

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return f"{self.email} ({self.id})"


class SignupCodeManager(models.Manager):
    def create_signup_code(self, user, ipaddr):
        code = _generate_code()
        signup_code = self.create(user=user, code=code, ipaddr=ipaddr)

        return signup_code

    def set_user_is_verified(self, signup_code, request):
        try:
            # TODO: Check origin of request is same as when the code was
            #       issued.
            delta = date.today() - signup_code.created_at.date()
            if delta.days > SignupCode.objects.get_expiry_period():
                signup_code.delete()
                return False, "Verification code has expired"

            # If different browser than during issue time, reject
            # TODO: IP check?
            if STRICT_USER_AGENT_VERIFICATION:
                # Fetch the log entry for when the user signed up
                log = AuthAuditLog.objects.filter(
                    user=signup_code.user, event_type=AuthAuditEventType.ACCOUNT_SIGNUP
                ).latest("created_at")

                ua_hash = mmh3.hash_bytes(request.META.get("HTTP_USER_AGENT"))

                if log.user_agent.identifier != ua_hash:
                    return False, "Unable to verify user"

            signup_code.user.is_verified = True
            signup_code.user.save()
            return True, "Account verified"
        except AuthAuditLog.DoesNotExist:
            pass

        return False, "Unable to verify user"

    def get_expiry_period(self):
        return EXPIRY_PERIOD


class PasswordResetCodeManager(models.Manager):
    def create_password_reset_code(self, user):
        code = _generate_code()
        password_reset_code = self.create(user=user, code=code)

        return password_reset_code

    def get_expiry_period(self):
        return EXPIRY_PERIOD


class EmailChangeCodeManager(models.Manager):
    def create_email_change_code(self, user, email):
        code = _generate_code()
        email_change_code = self.create(user=user, code=code, email=email)

        return email_change_code

    def get_expiry_period(self):
        return EXPIRY_PERIOD


def send_multi_format_email(template_prefix, template_ctxt, target_email):
    subject_file = "authemail/%s_subject.txt" % template_prefix
    txt_file = "authemail/%s.txt" % template_prefix
    html_file = "authemail/%s.html" % template_prefix

    subject = render_to_string(subject_file).strip()
    from_email = settings.EMAIL_FROM
    to = target_email
    bcc_email = settings.EMAIL_BCC
    text_content = render_to_string(txt_file, template_ctxt)
    html_content = render_to_string(html_file, template_ctxt)
    msg = EmailMultiAlternatives(
        subject, text_content, from_email, [to], bcc=[bcc_email]
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()


class AbstractBaseCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(_("code"), max_length=40, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def send_email(self, prefix):
        ctxt = {
            "base_url": settings.BASE_URL,
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "code": self.code,
            "user": {"id": str(self.user.id)},
        }
        send_multi_format_email(prefix, ctxt, target_email=self.user.email)

    def __str__(self):
        return self.code


class SignupCode(AbstractBaseCode):
    ipaddr = models.GenericIPAddressField(_("ip address"))

    objects = SignupCodeManager()

    def send_signup_email(self):
        prefix = "signup_email"
        self.send_email(prefix)

    # We are going to put an expiry on signup codes as well since they
    # effectively give authenticated access when provided to the application
    def get_expiry_period(self):
        return EXPIRY_PERIOD


class PasswordResetCode(AbstractBaseCode):
    objects = PasswordResetCodeManager()

    def send_password_reset_email(self):
        prefix = "password_reset_email"
        self.send_email(prefix)


class EmailChangeCode(AbstractBaseCode):
    email = models.EmailField(_("email address"), max_length=255)

    objects = EmailChangeCodeManager()

    def send_email_change_emails(self):
        prefix = "email_change_notify_previous_email"
        self.send_email(prefix)

        prefix = "email_change_confirm_new_email"
        ctxt = {
            "base_url": settings.BASE_URL,
            "email": self.email,
            "code": self.code,
            "user": {"id": str(self.user.id)},
        }

        send_multi_format_email(prefix, ctxt, target_email=self.email)


class AuthAuditEventType(models.TextChoices):
    ACCOUNT_SIGNUP = "SIGNUP", "New account signup"
    LOGIN = "LOGIN", "Login"
    RESET_PASSWORD_REQ = "RESET_PASSWORD_REQ", "Password reset request"
    PASSWORD_UPDATED = "PASSWORD_UPDATED", "Password has been changed"
    CHANGE_EMAIL_REQ = (
        "CHANGE_EMAIL_REQ",
        "A request to change email has been submitted",
    )
    EMAIL_UPDATED = (
        "EMAIL_UPDATED",
        "The email associated with the account has been updated",
    )


# User agent strings can be crazy long, but they also are in most cases the
# same across multiple users. So to save memory store in spearate table and
# reuse across multiple log entries.
# The `identifier` field is a hash of the UA String to provide the uniqueness
# constraint.
class UserAgent(models.Model):
    identifier = models.BinaryField(
        _("identifier"), unique=True, blank=False, null=False, max_length=128
    )
    ua_string = models.TextField(_("user agent string"), blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Parsed out UA details
    browser_name = models.CharField(max_length=100, null=True, blank=True)
    browser_version = models.CharField(max_length=20, null=True, blank=True)
    os_family = models.CharField(max_length=100, null=True, blank=True)
    os_version = models.CharField(max_length=20, null=True, blank=True)
    device_brand = models.CharField(max_length=100, null=True, blank=True)
    device_family = models.CharField(max_length=50, null=True, blank=True)
    device_model = models.CharField(max_length=50, null=True, blank=True)


@receiver(post_save, sender=UserAgent)
def enrich_ua(sender, instance, created, **kwargs):
    if created:
        ua_string = instance.ua_string
        parsed = user_agent_parser.Parse(ua_string)

        if "device" in parsed and parsed["device"]:
            device_info = parsed["device"]

            instance.device_brand = device_info.get("brand")
            instance.device_family = device_info.get("family")
            instance.device_model = device_info.get("model")

        if "os" in parsed and parsed["os"]:
            os_info = parsed["os"]

            instance.os_family = os_info.get("family")

            if os_info.get("major") and os_info["major"]:
                major = os_info["major"]

                minor = os_info.get("minor", 0)
                if minor is None:
                    minor = 0

                patch = os_info.get("patch", 0)
                if patch is None:
                    patch = 0

                os_version = f"{major}.{minor}.{patch}"
                instance.os_version = os_version

        if "user_agent" in parsed and parsed["user_agent"]:
            ua_info = parsed["user_agent"]

            if ua_info.get("major") and ua_info["major"]:
                major = os_info["major"]

                minor = os_info.get("minor", 0)
                if minor is None:
                    minor = 0

                patch = os_info.get("patch", 0)
                if patch is None:
                    patch = 0

                browser_version = f"{major}.{minor}.{patch}"
                instance.browser_version = browser_version

            instance.browser_name = ua_info.get("family")

        instance.save()


class AuthAuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_type = models.CharField(
        choices=AuthAuditEventType.choices, max_length=20, null=False, blank=False
    )
    user_agent = models.ForeignKey(
        UserAgent, on_delete=models.SET_NULL, null=True, blank=True
    )
    ipaddr = models.GenericIPAddressField(_("ip address"), null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("AuditLog")
        verbose_name_plural = _("AuditLogs")

    def __str__(self):
        return f"{self.event_type} ({self.user=})"

    def get_absolute_url(self):
        return reverse("_detail", kwargs={"pk": self.pk})

    @staticmethod
    def track(
        user,
        event_type: AuthAuditEventType,
        ip_address: Optional[str] = None,
        ua_agent: Optional[str] = None,
    ) -> None:
        log = AuthAuditLog(user=user, event_type=event_type)

        if ua_agent:
            ua_hash = mmh3.hash_bytes(ua_agent)
            agent_obj, _ = UserAgent.objects.get_or_create(
                identifier=ua_hash, defaults={"ua_string": ua_agent[:256]}
            )
            log.user_agent = agent_obj

        if ip_address:
            log.ipaddr = ip_address

        log.save()
