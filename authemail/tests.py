import re
from datetime import timedelta

from django.core import mail
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from authemail.models import SignupCode, PasswordResetCode


def _get_code_from_email(mail):
    match = re.search(r'\?code=([0-9a-f]+)$', mail.outbox[-1].body, re.MULTILINE)
    if match:
        code = match.group(1)
        return code
    return None


@override_settings(AUTH_EMAIL_VERIFICATION=True)
class SignupTests(APITestCase):
    def setUp(self):
        # A visitor to the site
        self.em_visitor = 'visitor@mail.com'
        self.pw_visitor = 'visitor'

        # A visitor to the site (for testing the wrapper)
        self.em_wrapper = 'wrapper@mail.com'
        self.pw_wrapper = 'wrapper'

        # A verified user on the site
        self.em_user = 'user@mail.com'
        self.pw_user = 'user'
        user = get_user_model().objects.create_user(self.em_user, self.pw_user)
        user.is_verified = True
        user.save()

    def test_signup_serializer_errors(self):
        error_dicts = [
            # Email required
            {'payload': {'email': '',
                         'password': self.pw_visitor},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'This field may not be blank.')
             },
            # Password required
            {'payload': {'email': self.em_visitor,
                         'password': ''},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('password', 'This field may not be blank.')
             },
            # Invalid email
            {'payload': {'email': 'XXX',
                         'password': self.pw_visitor},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'Enter a valid email address.')
             },
        ]

        url = reverse('authemail-signup')
        for error_dict in error_dicts:
            response = self.client.post(url, error_dict['payload'])

            self.assertEqual(response.status_code, error_dict['status_code'])
            self.assertEqual(response.data[error_dict['error'][0]][0],
                             error_dict['error'][1])

    def test_signup_email_already_exists(self):
        url = reverse('authemail-signup')
        payload = {
            'email': self.em_user,
            'password': self.pw_user,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'],
                         'User with this Email address already exists.')

    def test_signup_verify_invalid_code(self):
        url = reverse('authemail-signup-verify')
        params = {
            'code': 'XXX',
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unable to verify user.')

    def test_signup_and_signup_verify(self):
        # Send Signup request
        url = reverse('authemail-signup')
        payload = {
            'email': self.em_visitor,
            'password': self.pw_visitor,
        }
        response = self.client.post(url, payload)

        # Confirm that new user created, but not verified
        user = get_user_model().objects.latest('id')
        self.assertEqual(user.email, self.em_visitor)
        self.assertEqual(user.is_verified, False)

        # Confirm that signup code created
        signup_code = SignupCode.objects.latest('code')
        self.assertEqual(signup_code.user.email, self.em_visitor)

        # Confirm that email address in response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], payload['email'])

        # Confirm that one email sent and that Subject correct
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject,
                         'Verify your email address')

        code = _get_code_from_email(mail)

        # Send Signup Verify request
        url = reverse('authemail-signup-verify')
        params = {
            'code': code,
        }
        response = self.client.get(url, params)

        # Confirm email verified successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'User verified.')

    def test_signup_without_email_verification(self):

        with self.settings(AUTH_EMAIL_VERIFICATION=False):

            # Send Signup request
            url = reverse('authemail-signup')
            payload = {
                'email': self.em_visitor,
                'password': self.pw_visitor,
            }
            self.client.post(url, payload)

            # Confirm that new user got created, and was automatically marked as verified
            # (else changing AUTH_EMAIL_VERIFICATION setting later would have horrible consequences)
            user = get_user_model().objects.latest('id')
            self.assertEqual(user.email, self.em_visitor)
            self.assertEqual(user.is_verified, True)

            # no verification email sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].subject,
                             'Welcome')

    def test_signup_twice_then_email_verify(self):
        # Signup mulitple times with same credentials
        num_signups = 2
        self.assertTrue(num_signups > 1)
        for i in range(0, num_signups):
            url = reverse('authemail-signup')
            payload = {
                'email': self.em_visitor,
                'password': self.pw_visitor,
            }
            response = self.client.post(url, payload)

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(response.data['email'], payload['email'])
            self.assertEqual(SignupCode.objects.count(), 1)
            self.assertEqual(len(mail.outbox), i+1)
            self.assertEqual(mail.outbox[i].subject,
                             'Verify your email address')

        code = _get_code_from_email(mail)

        # Send Signup Verify request
        url = reverse('authemail-signup-verify')
        params = {
            'code': code,
        }
        response = self.client.get(url, params)

        # Confirm email verified successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'User verified.')

        # Confirm all signup codes were removed
        self.assertEqual(SignupCode.objects.count(), 0)

        # Confirm multiple signups resulted in only one additional user login
        self.assertEqual(get_user_model().objects.count(), 1+1)


class LoginTests(APITestCase):
    def setUp(self):
        # A verified user on the site
        self.em_user = 'user@mail.com'
        self.pw_user = 'user'
        self.user = get_user_model().objects.create_user(
            self.em_user, self.pw_user)
        self.user.is_verified = True
        self.user.save()

    def test_login_serializer_errors(self):
        error_dicts = [
            # Email required
            {'payload': {'email': '',
                         'password': self.pw_user},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'This field may not be blank.')
             },
            # Password required
            {'payload': {'email': self.em_user,
                         'password': ''},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('password', 'This field may not be blank.')
             },
            # Invalid email
            {'payload': {'email': 'XXX',
                         'password': self.pw_user},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'Enter a valid email address.')
             },
        ]

        url = reverse('authemail-login')
        for error_dict in error_dicts:
            response = self.client.post(url, error_dict['payload'])

            self.assertEqual(response.status_code, error_dict['status_code'])
            self.assertEqual(response.data[error_dict['error'][0]][0],
                             error_dict['error'][1])

    def test_login_invalid_credentials(self):
        # Invalid email address
        url = reverse('authemail-login')
        payload = {
            'email': 'XXX@mail.com',
            'password': self.pw_user,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')

        # Invalid password for user
        url = reverse('authemail-login')
        payload = {
            'email': self.em_user,
            'password': 'XXX',
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')

    def test_logout_no_auth_token(self):
        url = reverse('authemail-logout')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Authentication credentials were not provided.')

    def test_logout_invalid_auth_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + 'XXX')
        url = reverse('authemail-logout')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid token.')

    def test_login_logout(self):
        # Log in as the user
        url = reverse('authemail-login')
        payload = {
            'email': self.em_user,
            'password': self.pw_user,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

        token = response.data['token']

        # Log out as the user
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        url = reverse('authemail-logout')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'User logged out.')

    def test_login_inactive_notverified_no_login(self):
        # Inactive user can't login
        self.user.is_active = False
        self.user.save()

        url = reverse('authemail-login')
        payload = {
            'email': self.em_user,
            'password': self.pw_user,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')

        self.user.is_active = True
        self.user.save()

        # Unverified user can't login
        self.user.is_verified = False
        self.user.save()

        url = reverse('authemail-login')
        payload = {
            'email': self.em_user,
            'password': self.pw_user,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'User account not verified.')

        self.user.is_verified = True
        self.user.save()


class PasswordTests(APITestCase):
    def setUp(self):
        # A verified user on the site
        self.em_user = 'user@mail.com'
        self.pw_user = 'user'
        self.pw_user_reset = 'user reset'
        self.pw_user_change = 'user change'
        user = get_user_model().objects.create_user(self.em_user, self.pw_user)
        user.is_verified = True
        user.save()

        # Create auth token for user (so user logged in)
        token = Token.objects.create(user=user)
        self.token = token.key

    def test_password_reset_serializer_errors(self):
        error_dicts = [
            # Email required
            {'payload': {'email': ''},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'This field may not be blank.')
             },
            # Invalid email
            {'payload': {'email': 'XXX'},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'Enter a valid email address.')
             },
        ]

        url = reverse('authemail-password-reset')
        for error_dict in error_dicts:
            response = self.client.post(url, error_dict['payload'])

            self.assertEqual(response.status_code, error_dict['status_code'])
            self.assertEqual(response.data[error_dict['error'][0]][0],
                             error_dict['error'][1])

    def test_password_reset_invalid_code(self):
        code = 'XXX'

        url = reverse('authemail-password-reset-verify')
        url = '{url}?code={code}'.format(url=url, code=code)
        payload = {
            'password': self.pw_user,
        }
        response = self.client.get(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unable to verify user.')

    def test_password_reset_invalid_credentials(self):
        # Invalid email address
        url = reverse('authemail-password-reset')
        payload = {'email': 'XXX@mail.com'}
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Password reset not allowed.')

    def test_password_reset_verified_serializer_errors(self):
        error_dicts = [
            # Password required
            {'payload': {'password': ''},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('password', 'This field may not be blank.')
             },
        ]

        url = reverse('authemail-password-reset-verified')
        for error_dict in error_dicts:
            response = self.client.post(url, error_dict['payload'])

            self.assertEqual(response.status_code, error_dict['status_code'])
            self.assertEqual(response.data[error_dict['error'][0]][0],
                             error_dict['error'][1])

    def test_password_reset_and_verify_and_verified(self):
        # Send Password Reset request
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.em_user,
        }
        response = self.client.post(url, payload)

        # Confirm that password reset code created
        password_reset_code = PasswordResetCode.objects.latest('code')
        self.assertEqual(password_reset_code.user.email, self.em_user)

        # Confirm that email address in response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], payload['email'])

        # Confirm that one email sent and that Subject correct
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Reset Your Password')

        code_not_used = _get_code_from_email(mail)

        # Get a second code to use
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.em_user,
        }
        self.client.post(url, payload)
        password_reset_code = PasswordResetCode.objects.latest('code')
        code_used = password_reset_code.code

        # Send Password Reset Verify request
        url = reverse('authemail-password-reset-verify')
        params = {
            'code': code_used,
        }
        response = self.client.get(url, params)

        # Confirm password reset successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'User verified.')

        # Send Password Reset Verified request
        url = reverse('authemail-password-reset-verified')
        payload = {
            'code': code_used,
            'password': self.pw_user_reset,
        }
        response = self.client.post(url, payload)

        # Confirm password reset successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'Password reset.')

        # Confirm password reset code_not_used can't be used again
        url = reverse('authemail-password-reset-verify')
        params = {
            'code': code_not_used,
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unable to verify user.')

        # Confirm password reset code_used can't be used again
        url = reverse('authemail-password-reset-verify')
        params = {
            'code': code_used,
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unable to verify user.')

        # Get a third code to lapse
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.em_user,
        }
        self.client.post(url, payload)
        password_reset_code = PasswordResetCode.objects.latest('code')
        password_reset_code.created_at += timedelta(days=-(PasswordResetCode.objects.get_expiry_period()+1))
        password_reset_code.save()
        code_lapsed = password_reset_code.code

        # Confirm password reset code_lapsed can't be used
        url = reverse('authemail-password-reset-verify')
        params = {
            'code': code_lapsed,
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unable to verify user.')

        # Confirm unable to log in with old password
        url = reverse('authemail-login')
        payload = {
            'email': self.em_user,
            'password': self.pw_user,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')

        # Confirm able to log in with new password
        url = reverse('authemail-login')
        payload = {
            'email': self.em_user,
            'password': self.pw_user_reset,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_password_change_serializer_errors(self):
        error_dicts = [
            # Password required
            {'payload': {'password': ''},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('password', 'This field may not be blank.')
             },
        ]

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-password-change')
        for error_dict in error_dicts:
            response = self.client.post(url, error_dict['payload'])

            self.assertEqual(response.status_code, error_dict['status_code'])
            self.assertEqual(response.data[error_dict['error'][0]][0],
                             error_dict['error'][1])

    def test_password_change_no_auth_token(self):
        url = reverse('authemail-password-change')
        payload = {
            'password': self.pw_user,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Authentication credentials were not provided.')

    def test_password_change_invalid_auth_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + 'XXX')
        url = reverse('authemail-password-change')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid token.')

    def test_password_change(self):
        # Change password
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-password-change')
        payload = {
            'password': self.pw_user_change,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'Password changed.')

        # Confirm unable to log in with old password
        url = reverse('authemail-login')
        payload = {
            'email': self.em_user,
            'password': self.pw_user,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')

        # Confirm able to log in with new password
        url = reverse('authemail-login')
        payload = {
            'email': self.em_user,
            'password': self.pw_user_change,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class UserDetailTests(APITestCase):
    def setUp(self):
        # A verified user on the site
        self.em_user = 'user@mail.com'
        self.pw_user = 'user'
        user = get_user_model().objects.create_user(self.em_user, self.pw_user)
        user.is_verified = True
        user.save()

        # Create auth token for user (so user logged in)
        token = Token.objects.create(user=user)
        self.token = token.key

    def test_me_no_auth_token(self):
        url = reverse('authemail-me')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Authentication credentials were not provided.')

    def test_me_invalid_auth_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + 'XXX')
        url = reverse('authemail-me')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid token.')

    def test_me(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-me')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.em_user)
