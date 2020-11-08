from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.utils.translation import ugettext_lazy as _


class AddErrorMixin(object):
    def add_error(self, field, msg):
        field = field or NON_FIELD_ERRORS
        if field in self._errors:
            self._errors[field].append(msg)
        else:
            self._errors[field] = self.error_class([msg])


class PasswordConfirmForm(AddErrorMixin, forms.Form):
    password = forms.CharField(max_length=128)
    password2 = forms.CharField(max_length=128)

    def clean_password2(self):
        password = self.cleaned_data.get('password', '')
        password2 = self.cleaned_data['password2']
        if password != password2:
            raise forms.ValidationError(
                _("Confirmation password doesn't match."))
        return password2


class SignupForm(PasswordConfirmForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(max_length=255)


class LoginForm(AddErrorMixin, forms.Form):
    email = forms.EmailField(max_length=255)
    password = forms.CharField(max_length=128)


class PasswordResetForm(AddErrorMixin, forms.Form):
    email = forms.EmailField(max_length=255)


class PasswordResetVerifiedForm(AddErrorMixin, forms.Form):
    pass


class EmailChangeForm(AddErrorMixin, forms.Form):
    email = forms.EmailField(max_length=255)


class PasswordChangeForm(PasswordConfirmForm):
    pass


class UsersMeChangeForm(AddErrorMixin, forms.Form):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    date_of_birth = forms.DateField(required=False)
