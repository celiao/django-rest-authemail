from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.views.generic.edit import FormView

from authemail import wrapper

from .forms import SignupForm, LoginForm
from .forms import PasswordResetForm, PasswordResetVerifiedForm
from .forms import EmailChangeForm
from .forms import PasswordChangeForm, UsersMeChangeForm

from . import wrapperplus


class LandingFrontEnd(TemplateView):
    template_name = 'landing.html'


class SignupFrontEnd(FormView):
    template_name = 'signup.html'
    form_class = SignupForm
    success_url = reverse_lazy('signup_email_sent_page')

    def form_valid(self, form):
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        account = wrapper.Authemail()
        response = account.signup(first_name=first_name, last_name=last_name,
                                  email=email, password=password)

        # Handle other error responses from API
        if 'detail' in response:
            form.add_error(None, response['detail'])
            return self.form_invalid(form)

        return super(SignupFrontEnd, self).form_valid(form)


class SignupEmailSentFrontEnd(TemplateView):
    template_name = 'signup_email_sent.html'


class SignupVerifyFrontEnd(View):
    def get(self, request, format=None):
        code = request.GET.get('code', '')

        account = wrapper.Authemail()
        response = account.signup_verify(code=code)

        # Handle other error responses from API
        if 'detail' in response:
            return HttpResponseRedirect(reverse('signup_not_verified_page'))

        return HttpResponseRedirect(reverse('signup_verified_page'))


class SignupVerifiedFrontEnd(TemplateView):
    template_name = 'signup_verified.html'


class SignupNotVerifiedFrontEnd(TemplateView):
    template_name = 'signup_not_verified.html'


class LoginFrontEnd(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = reverse_lazy('home_page')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        account = wrapper.Authemail()
        response = account.login(email=email, password=password)

        if 'token' in response:
            self.request.session['auth_token'] = response['token']
        else:
            # Handle other error responses from API
            if 'detail' in response:
                form.add_error(None, response['detail'])
            return self.form_invalid(form)

        return super(LoginFrontEnd, self).form_valid(form)


class HomeFrontEnd(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeFrontEnd, self).get_context_data(**kwargs)

        token = self.request.session['auth_token']

        account = wrapper.Authemail()
        account.users_me(token=token)

        context['first_name'] = account.first_name
        context['last_name'] = account.last_name
        context['email'] = account.email

        return context


class LogoutFrontEnd(View):
    def get(self, request):
        token = self.request.session['auth_token']

        account = wrapper.Authemail()
        account.logout(token=token)

        self.request.session.flush()

        return HttpResponseRedirect(reverse('landing_page'))


class PasswordResetFrontEnd(FormView):
    template_name = 'password_reset.html'
    form_class = PasswordResetForm
    success_url = reverse_lazy('password_reset_email_sent_page')

    def form_valid(self, form):
        email = form.cleaned_data['email']

        account = wrapper.Authemail()
        response = account.password_reset(email=email)

        # Handle other error responses from API
        if 'detail' in response:
            form.add_error(None, response['detail'])
            return self.form_invalid(form)

        return super(PasswordResetFrontEnd, self).form_valid(form)


class PasswordResetEmailSentFrontEnd(TemplateView):
    template_name = 'password_reset_email_sent.html'


class PasswordResetVerifyFrontEnd(View):
    def get(self, request, format=None):
        code = request.GET.get('code', '')

        account = wrapper.Authemail()
        response = account.password_reset_verify(code=code)

        # Handle other error responses from API
        if 'detail' in response:
            return HttpResponseRedirect(
                reverse('password_reset_not_verified_page'))

        request.session['password_reset_code'] = code

        return HttpResponseRedirect(reverse('password_reset_verified_page'))


class PasswordResetVerifiedFrontEnd(FormView):
    template_name = 'password_reset_verified.html'
    form_class = PasswordResetVerifiedForm
    success_url = reverse_lazy('password_reset_success_page')

    def form_valid(self, form):
        code = self.request.session['password_reset_code']
        password = form.cleaned_data['password']

        account = wrapper.Authemail()
        response = account.password_reset_verified(code=code, password=password)

        # Handle other error responses from API
        if 'detail' in response:
            form.add_error(None, response['detail'])
            return self.form_invalid(form)

        return super(PasswordResetVerifiedFrontEnd, self).form_valid(form)


class PasswordResetNotVerifiedFrontEnd(TemplateView):
    template_name = 'password_reset_not_verified.html'


class PasswordResetSuccessFrontEnd(TemplateView):
    template_name = 'password_reset_success.html'


class EmailChangeFrontEnd(FormView):
    template_name = 'email_change.html'
    form_class = EmailChangeForm
    success_url = reverse_lazy('email_change_emails_sent_page')

    def form_valid(self, form):
        token = self.request.session['auth_token']
        email = form.cleaned_data['email']

        account = wrapper.Authemail()
        response = account.email_change(token=token, email=email)

        # Handle other error responses from API
        if 'detail' in response:
            form.add_error(None, response['detail'])
            return self.form_invalid(form)

        return super(EmailChangeFrontEnd, self).form_valid(form)


class EmailChangeEmailsSentFrontEnd(TemplateView):
    template_name = 'email_change_emails_sent.html'


class EmailChangeVerifyFrontEnd(View):
    def get(self, request, format=None):
        code = request.GET.get('code', '')

        account = wrapper.Authemail()
        response = account.email_change_verify(code=code)

        # Handle other error responses from API
        if 'detail' in response:
            return HttpResponseRedirect(
                reverse('email_change_not_verified_page'))

        request.session['email_change_code'] = code

        return HttpResponseRedirect(reverse('email_change_verified_page'))


class EmailChangeVerifiedFrontEnd(TemplateView):
    template_name = 'email_change_verified.html'


class EmailChangeNotVerifiedFrontEnd(TemplateView):
    template_name = 'email_change_not_verified.html'


class PasswordChangeFrontEnd(FormView):
    template_name = 'password_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('password_change_success_page')

    def form_valid(self, form):
        token = self.request.session['auth_token']
        password = form.cleaned_data['password']

        account = wrapper.Authemail()
        response = account.password_change(token=token, password=password)

        # Handle other error responses from API
        if 'detail' in response:
            form.add_error(None, response['detail'])
            return self.form_invalid(form)

        return super(PasswordChangeFrontEnd, self).form_valid(form)


class PasswordChangeSuccessFrontEnd(TemplateView):
    template_name = 'password_change_success.html'


class UsersMeChangeFrontEnd(FormView):
    template_name = 'users_me_change.html'
    form_class = UsersMeChangeForm
    success_url = reverse_lazy('users_me_change_success_page')

    def get_context_data(self, **kwargs):
        context = super(UsersMeChangeFrontEnd, self).get_context_data(**kwargs)

        token = self.request.session['auth_token']

        account = wrapper.Authemail()
        account.users_me(token=token)

        context['first_name'] = account.first_name
        context['last_name'] = account.last_name
        context['date_of_birth'] = account.date_of_birth

        return context

    def form_valid(self, form):
        token = self.request.session['auth_token']
        first_name = form.cleaned_data['first_name']
        last_name = form.cleaned_data['last_name']
        date_of_birth = form.cleaned_data['date_of_birth']

        account = wrapperplus.AuthemailPlus()
        response = account.users_me_change(token=token,
                                           first_name=first_name,
                                           last_name=last_name,
                                           date_of_birth=date_of_birth)

        # Handle other error responses from API
        if 'detail' in response:
            form.add_error(None, response['detail'])
            return self.form_invalid(form)

        return super(UsersMeChangeFrontEnd, self).form_valid(form)


class UsersMeChangeSuccessFrontEnd(TemplateView):
    template_name = 'users_me_change_success.html'
