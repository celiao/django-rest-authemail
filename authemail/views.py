from datetime import date

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _

from rest_framework import status, exceptions
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SignupCode, EmailChangeCode, PasswordResetCode
from .models import send_multi_format_email
from .serializers import SignupSerializer, LoginSerializer
from .serializers import PasswordResetSerializer
from .serializers import PasswordResetVerifiedSerializer
from .serializers import EmailChangeSerializer
from .serializers import PasswordChangeSerializer
from .serializers import UserSerializer


class Signup(APIView):
    permission_classes = (AllowAny,)
    serializer_class = SignupSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)

        email = serializer.data['email']
        password = serializer.data['password']
        first_name = serializer.data['first_name']
        last_name = serializer.data['last_name']

        must_validate_email = getattr(settings, "AUTH_EMAIL_VERIFICATION", True)

        try:
            user = get_user_model().objects.get(email=email)
            if user.is_verified:
                raise exceptions.ValidationError(_('Email address already taken.'))

            try:
                # Delete old signup codes
                signup_code = SignupCode.objects.get(user=user)
                signup_code.delete()
            except SignupCode.DoesNotExist:
                pass

        except get_user_model().DoesNotExist:
            user = get_user_model().objects.create_user(email=email)

        # Set user fields provided
        user.set_password(password)
        user.first_name = first_name
        user.last_name = last_name
        if not must_validate_email:
            user.is_verified = True
            send_multi_format_email('welcome_email',
                                    {'email': user.email, },
                                    target_email=user.email)
        user.save()

        if must_validate_email:
            # Create and associate signup code
            ipaddr = self.request.META.get('REMOTE_ADDR', '0.0.0.0')
            signup_code = SignupCode.objects.create_signup_code(user, ipaddr)
            signup_code.send_signup_email()

        content = {'email': email, 'first_name': first_name,
                    'last_name': last_name}
        return Response(content, status=status.HTTP_201_CREATED)


class SignupVerify(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        code = request.GET.get('code', '')
        verified = SignupCode.objects.set_user_is_verified(code)

        if verified:
            try:
                signup_code = SignupCode.objects.get(code=code)
                signup_code.delete()
            except SignupCode.DoesNotExist:
                pass
            content = {'success': _('Email address verified.')}
            return Response(content, status=status.HTTP_200_OK)
        else:
            raise exceptions.ValidationError(_('Unable to verify user.'))


class Login(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)

        email = serializer.data['email']
        password = serializer.data['password']
        user = authenticate(email=email, password=password)

        if not user:
            raise exceptions.AuthenticationFailed(_('Unable to login with provided credentials.'))
        
        if not user.is_verified:
            raise exceptions.AuthenticationFailed(_('User account not verified.'))
        
        if not user.is_active:
            raise exceptions.ValidationError(_('User account not active.'))

        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key},
                        status=status.HTTP_200_OK)
                


class Logout(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        """
        Remove all auth tokens owned by request.user.
        """
        tokens = Token.objects.filter(user=request.user).delete()
        content = {'success': _('User logged out.')}
        return Response(content, status=status.HTTP_200_OK)


class PasswordReset(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)
        email = serializer.data['email']
        content = {'email': email}
        try:
            user = get_user_model().objects.get(email=email)

            # Delete all unused password reset codes
            PasswordResetCode.objects.filter(user=user).delete()

            if user.is_verified and user.is_active:
                password_reset_code = \
                    PasswordResetCode.objects.create_password_reset_code(user)
                password_reset_code.send_password_reset_email()

        except get_user_model().DoesNotExist:
            pass

        # return a 201 status for any email - we don't want to give away if an email exists or not
        return Response(content, status=status.HTTP_201_CREATED)


class PasswordResetVerify(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        code = request.GET.get('code', '')

        try:
            password_reset_code = PasswordResetCode.objects.get(code=code)

            # Delete password reset code if older than expiry period
            delta = date.today() - password_reset_code.created_at.date()
            if delta.days > PasswordResetCode.objects.get_expiry_period():
                password_reset_code.delete()
                raise PasswordResetCode.DoesNotExist()

            content = {'success': _('Email address verified.')}
            return Response(content, status=status.HTTP_200_OK)
        except PasswordResetCode.DoesNotExist:
            pass

        raise exceptions.ValidationError(_('Unale to verify user.'))


class PasswordResetVerified(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetVerifiedSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)
    
        code = serializer.data['code']
        password = serializer.data['password']

        try:
            password_reset_code = PasswordResetCode.objects.get(code=code)
            password_reset_code.user.set_password(password)
            password_reset_code.user.save()

            # Delete password reset code just used
            password_reset_code.delete()

            content = {'success': _('Password reset.')}
            return Response(content, status=status.HTTP_200_OK)
        except PasswordResetCode.DoesNotExist:
            pass

        raise exceptions.ValidationError(_('Unable to verify user.'))


class EmailChange(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EmailChangeSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)

        user = request.user

        # Delete all unused email change codes
        EmailChangeCode.objects.filter(user=user).delete()

        email_new = serializer.data['email']

        try:
            user_with_email = get_user_model().objects.get(email=email_new)
            if user_with_email.is_verified:
                raise exceptions.ValidationError(_('Email address already in use.'))
            else:
                # If the account with this email address is not verified,
                # give this user a chance to verify and grab this email address
                raise get_user_model().DoesNotExist

        except get_user_model().DoesNotExist:
            pass

        email_change_code = EmailChangeCode.objects.create_email_change_code(user, email_new)
        email_change_code.send_email_change_emails()

        content = {'email': email_new}
        return Response(content, status=status.HTTP_201_CREATED)


class EmailChangeVerify(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, format=None):
        code = request.GET.get('code', '')

        try:
            # Check if the code exists.
            email_change_code = EmailChangeCode.objects.get(code=code)

            # Check if the code has expired.
            delta = date.today() - email_change_code.created_at.date()
            if delta.days > EmailChangeCode.objects.get_expiry_period():
                email_change_code.delete()
                raise EmailChangeCode.DoesNotExist()

        except EmailChangeCode.DoesNotExist:
            # email change code doesn't exist or has expired
            raise exceptions.ValidationError(_('Unable to verify user.'))

        # Check if the email address is already being used by a verified user.
        try:
            user_with_email = get_user_model().objects.get(email=email_change_code.email)
            if user_with_email.is_verified:
                # Delete email change code since won't be used
                email_change_code.delete()
                raise exceptions.ValidationError(_('Email address already taken.'))

            # If the account with this email address is not verified,
            # delete the account (and signup code) because the email
            # address will be used for the user who just verified.
            user_with_email.delete()
        except get_user_model().DoesNotExist:
            pass

        # If all is well, change the email address.
        email_change_code.user.email = email_change_code.email
        email_change_code.user.save()

        # Delete email change code just used
        email_change_code.delete()

        content = {'success': _('Email address changed.')}
        return Response(content, status=status.HTTP_200_OK)


class PasswordChange(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data, context={'request': request})

        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)

        user = request.user

        password = serializer.data['password']
        user.set_password(password)
        user.save()

        content = {'success': _('Password changed.')}
        return Response(content, status=status.HTTP_200_OK)


class UserMe(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request, format=None):
        return Response(self.serializer_class(request.user, context={'request': request}).data)
