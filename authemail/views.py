from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext as _

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authemail.models import SignupCode, PasswordResetCode, send_multi_format_email
from authemail.serializers import SignupSerializer, LoginSerializer
from authemail.serializers import PasswordResetSerializer
from authemail.serializers import PasswordResetVerifiedSerializer
from authemail.serializers import PasswordChangeSerializer
from authemail.serializers import UserSerializer


class Signup(APIView):
    permission_classes = (AllowAny,)
    serializer_class = SignupSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.data['email']
            password = serializer.data['password']
            first_name = serializer.data['first_name']
            last_name = serializer.data['last_name']

            must_validate_email = getattr(settings, "AUTH_EMAIL_VERIFICATION", True)

            try:
                user = get_user_model().objects.get(email=email)
                if user.is_verified:
                    content = {
                        'detail': _('User with this Email address already '
                                    'exists.')}
                    return Response(content, status=status.HTTP_400_BAD_REQUEST)

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

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
            content = {'success': _('User verified.')}
            return Response(content, status=status.HTTP_200_OK)
        else:
            content = {'detail': _('Unable to verify user.')}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class Login(APIView):
    permission_classes = (AllowAny,)
    serializer_class = LoginSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.data['email']
            password = serializer.data['password']
            user = authenticate(email=email, password=password)

            if user:
                if user.is_verified:
                    if user.is_active:
                        token, created = Token.objects.get_or_create(user=user)
                        return Response({'token': token.key},
                                        status=status.HTTP_200_OK)
                    else:
                        content = {'detail': _('User account not active.')}
                        return Response(content,
                                        status=status.HTTP_401_UNAUTHORIZED)
                else:
                    content = {'detail':
                               _('User account not verified.')}
                    return Response(content, status=status.HTTP_401_UNAUTHORIZED)
            else:
                content = {'detail':
                           _('Unable to login with provided credentials.')}
                return Response(content, status=status.HTTP_401_UNAUTHORIZED)

        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class Logout(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        """
        Remove all auth tokens owned by request.user.
        """
        tokens = Token.objects.filter(user=request.user)
        for token in tokens:
            token.delete()
        content = {'success': _('User logged out.')}
        return Response(content, status=status.HTTP_200_OK)


class PasswordReset(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            email = serializer.data['email']

            try:
                user = get_user_model().objects.get(email=email)

                # Delete all unused password reset codes
                PasswordResetCode.objects.filter(user=user).delete()

                if user.is_verified and user.is_active:
                    password_reset_code = \
                        PasswordResetCode.objects.create_reset_code(user)
                    password_reset_code.send_password_reset_email()
                    content = {'email': email}
                    return Response(content, status=status.HTTP_201_CREATED)

            except get_user_model().DoesNotExist:
                pass

            # Since this is AllowAny, don't give away error.
            content = {'detail': _('Password reset not allowed.')}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


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
                
            content = {'success': _('User verified.')}
            return Response(content, status=status.HTTP_200_OK)
        except PasswordResetCode.DoesNotExist:
            content = {'detail': _('Unable to verify user.')}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetVerified(APIView):
    permission_classes = (AllowAny,)
    serializer_class = PasswordResetVerifiedSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            code = serializer.data['code']
            password = serializer.data['password']

            try:
                password_reset_code = PasswordResetCode.objects.get(code=code)
                password_reset_code.user.set_password(password)
                password_reset_code.user.save()

                # Delete password code just used
                password_reset_code.delete()

                content = {'success': _('Password reset.')}
                return Response(content, status=status.HTTP_200_OK)
            except PasswordResetCode.DoesNotExist:
                content = {'detail': _('Unable to verify user.')}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class PasswordChange(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PasswordChangeSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = request.user

            password = serializer.data['password']
            user.set_password(password)
            user.save()

            content = {'success': _('Password changed.')}
            return Response(content, status=status.HTTP_200_OK)

        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)


class UserMe(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get(self, request, format=None):
        return Response(self.serializer_class(request.user).data)
