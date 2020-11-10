from django.db import models
from django.utils.translation import ugettext_lazy as _

from authemail.models import EmailAbstractUser, EmailUserManager


class MyUser(EmailAbstractUser):
    # Custom fields
    date_of_birth = models.DateField(_('Date of birth'), null=True, blank=True)

    # Required
    objects = EmailUserManager()


class VerifiedUserManager(EmailUserManager):
    def get_queryset(self):
        return super(VerifiedUserManager, self).get_queryset().filter(
            is_verified=True)


class VerifiedUser(MyUser):
    objects = VerifiedUserManager()

    class Meta:
        proxy = True
