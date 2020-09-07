from __future__ import absolute_import
import binascii
import os
from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.core.mail.message import EmailMultiAlternatives
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.mail import send_mail

# Make part of the model eventually, so it can be edited
EXPIRY_PERIOD = 3    # days

def _generate_code():
    return binascii.hexlify(os.urandom(20)).decode('utf-8')


class EmailUserManager(BaseUserManager):
    def _create_user(self, email, password, is_staff, is_superuser,
                     is_verified, **extra_fields):
        """
        Creates and saves a User with a given email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email,
                          is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, is_verified=is_verified,
                          last_login=now, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, False,
                                 **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, True,
                                 **extra_fields)


class EmailAbstractUser(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Email and password are required. Other fields are optional.
    """
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), max_length=255, unique=True)
    is_staff = models.BooleanField(
        _('staff status'), default=False,
        help_text=_('Designates whether the user can log into this '
                    'admin site.'))
    is_active = models.BooleanField(
        _('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active.  Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    is_verified = models.BooleanField(
        _('verified'), default=False,
        help_text=_('Designates whether this user has completed the email '
                    'verification process to allow login.'))

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
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
        return self.email


class SignupCodeManager(models.Manager):
    def create_signup_code(self, user, ipaddr):
        code = _generate_code()
        signup_code = self.create(user=user, code=code, ipaddr=ipaddr)

        return signup_code

    def set_user_is_verified(self, code):
        try:
            signup_code = SignupCode.objects.get(code=code)
            signup_code.user.is_verified = True
            signup_code.user.save()
            return True
        except SignupCode.DoesNotExist:
            pass

        return False


class PasswordResetCodeManager(models.Manager):
    def create_reset_code(self, user):
        code = _generate_code()
        password_reset_code = self.create(user=user, code=code)

        return password_reset_code

    def get_expiry_period(self):
        return EXPIRY_PERIOD


def send_multi_format_email(template_prefix, template_ctxt, target_email):
    subject_file = 'authemail/%s_subject.txt' % template_prefix
    txt_file = 'authemail/%s.txt' % template_prefix
    html_file = 'authemail/%s.html' % template_prefix

    subject = render_to_string(subject_file).strip()
    from_email = settings.EMAIL_FROM
    to = target_email
    bcc_email = settings.EMAIL_BCC
    text_content = render_to_string(txt_file, template_ctxt)
    html_content = render_to_string(html_file, template_ctxt)
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to],
                                 bcc=[bcc_email])
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


class AbstractBaseCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(_('code'), max_length=40, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def send_email(self, prefix):
        ctxt = {
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'code': self.code
        }
        send_multi_format_email(prefix, ctxt, target_email=self.user.email)

    def __str__(self):
        return self.code


class SignupCode(AbstractBaseCode):
    ipaddr = models.GenericIPAddressField(_('ip address'))

    objects = SignupCodeManager()

    def send_signup_email(self):
        prefix = 'signup_email'
        self.send_email(prefix)


class PasswordResetCode(AbstractBaseCode):
    objects = PasswordResetCodeManager()

    def send_password_reset_email(self):
        prefix = 'password_reset_email'
        self.send_email(prefix)
