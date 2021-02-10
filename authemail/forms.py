from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserChangeForm
from django.utils.translation import ugettext_lazy as _


class EmailUserPasswordResetForm(forms.Form):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """
    password1 = forms.CharField(label=_('Password'),
                                widget=forms.PasswordInput)
    password2 = forms.CharField(label=_('Password confirmation'),
                                widget=forms.PasswordInput,
                                help_text=_('Enter the same password as '
                                            'above, for verification.'))
    code = forms.CharField(widget=forms.HiddenInput)

    def clean(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                _('The two password fields did not match.'))
        return self.cleaned_data


class EmailUserChangeForm(UserChangeForm):
    class Meta:
        model = get_user_model()
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(EmailUserChangeForm, self).__init__(*args, **kwargs)
        if 'username' in self.fields:
            del self.fields['username']
