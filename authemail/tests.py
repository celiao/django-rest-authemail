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
from authemail.models import EmailChangeCode


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
        self.user_visitor_email = 'visitor@mail.com'
        self.user_visitor_pw = 'visitor'

        # A verified user on the site
        self.user_verified_email = 'user_verified@mail.com'
        self.user_verified_pw = 'user_verified'
        user = get_user_model().objects.create_user(self.user_verified_email, self.user_verified_pw)
        user.is_verified = True
        user.save()

    def test_signup_serializer_errors(self):
        error_dicts = [
            # Email required
            {'payload': {'email': '',
                         'password': self.user_visitor_pw},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'This field may not be blank.')
             },
            # Password required
            {'payload': {'email': self.user_visitor_email,
                         'password': ''},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('password', 'This field may not be blank.')
             },
            # Invalid email
            {'payload': {'email': 'XXX',
                         'password': self.user_visitor_pw},
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
            'email': self.user_verified_email,
            'password': self.user_verified_pw,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'],
                         'Email address already taken.')

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
            'email': self.user_visitor_email,
            'password': self.user_visitor_pw,
        }
        response = self.client.post(url, payload)

        # Confirm that new user created, but not verified
        user = get_user_model().objects.latest('id')
        self.assertEqual(user.email, self.user_visitor_email)
        self.assertEqual(user.is_verified, False)

        # Confirm that signup code created
        signup_code = SignupCode.objects.latest('code')
        self.assertEqual(signup_code.user.email, self.user_visitor_email)

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
        self.assertEqual(response.data['success'], 'Email address verified.')

    def test_signup_without_email_verification(self):

        with self.settings(AUTH_EMAIL_VERIFICATION=False):
            # Send Signup request
            url = reverse('authemail-signup')
            payload = {
                'email': self.user_visitor_email,
                'password': self.user_visitor_pw,
            }
            self.client.post(url, payload)

            # Confirm that new user got created, and was automatically marked as verified
            # (else changing AUTH_EMAIL_VERIFICATION setting later would have horrible consequences)
            user = get_user_model().objects.latest('id')
            self.assertEqual(user.email, self.user_visitor_email)
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
                'email': self.user_visitor_email,
                'password': self.user_visitor_pw,
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
        self.assertEqual(response.data['success'], 'Email address verified.')

        # Confirm all signup codes were removed
        self.assertEqual(SignupCode.objects.count(), 0)

        # Confirm multiple signups resulted in only one additional user login
        self.assertEqual(get_user_model().objects.count(), 1+1)


class LoginTests(APITestCase):
    def setUp(self):
        # User who is verified on the site
        self.user_verified_email = 'user_verified@mail.com'
        self.user_verified_pw = 'user_verified'
        self.user_verified = get_user_model().objects.create_user(self.user_verified_email, self.user_verified_pw)
        self.user_verified.is_verified = True
        self.user_verified.save()

        # User who is not verified yet on the site
        self.user_not_verified_email = 'user_not_verified@mail.com'
        self.user_not_verified_pw = 'user_not_verified'
        self.user_not_verified = get_user_model().objects.create_user(self.user_not_verified_email, 'pw')
        self.user_not_verified.save()

        # User who is not active on the site
        self.user_not_active_email = 'user_not_active@mail.com'
        self.user_not_active_pw = 'user_not_active'
        self.user_not_active = get_user_model().objects.create_user(self.user_not_active_email, self.user_not_active_pw)
        self.user_not_active.is_verified = True
        self.user_not_active.is_active = False
        self.user_not_active.save()

    def test_login_serializer_errors(self):
        error_dicts = [
            # Email required
            {'payload': {'email': '',
                         'password': self.user_verified_pw},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'This field may not be blank.')
             },
            # Password required
            {'payload': {'email': self.user_verified_email,
                         'password': ''},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('password', 'This field may not be blank.')
             },
            # Invalid email
            {'payload': {'email': 'XXX',
                         'password': self.user_verified_pw},
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
            'password': self.user_verified_pw,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')

        # Invalid password for user
        url = reverse('authemail-login')
        payload = {
            'email': self.user_verified_email,
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
            'email': self.user_verified_email,
            'password': self.user_verified_pw,
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

    def test_login_not_verified_not_active_no_login(self):
        # Not verified user can't login
        url = reverse('authemail-login')
        payload = {
            'email': self.user_not_verified_email,
            'password': self.user_not_verified_pw,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')

        # Not active user can't login
        url = reverse('authemail-login')
        payload = {
            'email': self.user_not_active_email,
            'password': self.user_not_active_pw,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')


class PasswordResetTests(APITestCase):
    def setUp(self):
        # User who is verified on the site
        self.user_verified_email = 'user_verified@mail.com'
        self.user_verified_pw = 'user_verified'
        self.user_verified_pw_reset = 'user_verified reset'
        self.user_verified = get_user_model().objects.create_user(self.user_verified_email, self.user_verified_pw)
        self.user_verified.is_verified = True
        self.user_verified.save()

        # Create auth token for user (so user logged in)
        token = Token.objects.create(user=self.user_verified)
        self.token = token.key

        # User who is not verified yet on the site
        self.user_not_verified_email = 'user_not_verified@mail.com'
        self.user_not_verified_pw = 'user_not_verified'
        self.user_not_verified = get_user_model().objects.create_user(self.user_not_verified_email, 'pw')
        self.user_not_verified.save()

        # User who is verified but not active on the site
        self.user_not_active_email = 'user_not_active@mail.com'
        self.user_not_active_pw = 'user_not_active'
        self.user_not_active = get_user_model().objects.create_user(self.user_not_active_email, self.user_not_active_pw)
        self.user_not_active.is_verified = True
        self.user_not_active.is_active = False
        self.user_not_active.save()

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

    def test_password_reset_no_user_with_email(self):
        # No user with email address
        url = reverse('authemail-password-reset')
        payload = {
            'email': 'XXX@mail.com'
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Password reset not allowed.')

    def test_password_reset_user_not_verified_not_allowed(self):
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.user_not_verified_email
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Password reset not allowed.')

    def test_password_reset_user_not_active_not_allowed(self):
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.user_not_active_email
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Password reset not allowed.')

    def test_password_reset_user_verified_code_created_email_sent(self):
        # Create two past reset codes that aren't used
        password_reset_code_old1 = PasswordResetCode.objects.create_password_reset_code(
            self.user_verified)
        password_reset_code_old2 = PasswordResetCode.objects.create_password_reset_code(
            self.user_verified)
        count = PasswordResetCode.objects.filter(user=self.user_verified).count()
        self.assertEqual(count, 2)

        # Send Password Reset request
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.user_verified_email,
        }
        response = self.client.post(url, payload)

        # Get password reset code
        password_reset_code = PasswordResetCode.objects.latest('code')

        # Confirm that old password reset codes deleted
        count = PasswordResetCode.objects.filter(user=self.user_verified).count()
        self.assertEqual(count, 1)
        self.assertNotEqual(password_reset_code.code, password_reset_code_old1.code)
        self.assertNotEqual(password_reset_code.code, password_reset_code_old2.code)

        # Confirm that password reset code created
        password_reset_code = PasswordResetCode.objects.latest('code')
        self.assertEqual(password_reset_code.user.email, self.user_verified_email)

        # Confirm that email address in response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], payload['email'])

        # Confirm that one email sent and that Subject correct
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Reset Your Password')

    def test_password_reset_verify_invalid_code(self):
        url = reverse('authemail-password-reset-verify')
        params = {
            'code': 'XXX',
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unable to verify user.')

    def test_password_reset_verify_expired_code(self):
        # Send Password Reset request
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.user_verified_email,
        }
        self.client.post(url, payload)

        # Get password reset code and make it expire
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

    def test_password_reset_verify_user_verified(self):
        # Send Password Reset request
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.user_verified_email,
        }
        self.client.post(url, payload)
        password_reset_code = PasswordResetCode.objects.latest('code')
        code = password_reset_code.code

        # Send Password Reset Verify request
        url = reverse('authemail-password-reset-verify')
        params = {
            'code': code,
        }
        response = self.client.get(url, params)

        # Confirm password reset successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'Email address verified.')

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

    def test_password_reset_verified_invalid_code(self):
        # Send Password Reset request
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.user_verified_email,
        }
        self.client.post(url, payload)
        password_reset_code = PasswordResetCode.objects.latest('code')
        code = password_reset_code.code

        # Send Password Reset Verify request
        url = reverse('authemail-password-reset-verify')
        params = {
            'code': code,
        }
        response = self.client.get(url, params)

        # Send Password Reset Verified request
        url = reverse('authemail-password-reset-verified')
        params = {
            'code': 'XXX',
            'password': self.user_verified_pw_reset,
        }
        response = self.client.post(url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unable to verify user.')

    def test_password_reset_verified_user_verified(self):
        # Send Password Reset request for not used code
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.user_verified_email,
        }
        response = self.client.post(url, payload)
        password_reset_code = PasswordResetCode.objects.latest('code')
        code_not_used = password_reset_code.code

        # Send Password Reset request for used code
        url = reverse('authemail-password-reset')
        payload = {
            'email': self.user_verified_email,
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

        # Confirm password reset verify is successful
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'Email address verified.')

        # Confirm old codes deleted and one remains
        num_codes = PasswordResetCode.objects.count()
        self.assertEqual(num_codes, 1)

        # Send Password Reset Verified request
        url = reverse('authemail-password-reset-verified')
        payload = {
            'code': code_used,
            'password': self.user_verified_pw_reset,
        }
        response = self.client.post(url, payload)

        # Confirm password reset successfully
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'Password reset.')

        # Confirm used code deleted and none remain
        num_codes = PasswordResetCode.objects.count()
        self.assertEqual(num_codes, 0)

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

        # Confirm unable to log in with old password
        url = reverse('authemail-login')
        payload = {
            'email': self.user_verified_email,
            'password': self.user_verified_pw,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')

        # Confirm able to log in with new password
        url = reverse('authemail-login')
        payload = {
            'email': self.user_verified_email,
            'password': self.user_verified_pw_reset,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class EmailChangeTests(APITestCase):
    def setUp(self):
        # User who wants to change their email address
        self.user_to_change_email = 'user_to_change@mail.com'
        self.user_to_change = get_user_model().objects.create_user(self.user_to_change_email, 'pw')
        self.user_to_change.is_verified = True
        self.user_to_change.save()

        # Create auth token for user (so user logged in)
        token = Token.objects.create(user=self.user_to_change)
        self.token = token.key

        # User who is verified on the site
        self.user_verified_email = 'user_verified@mail.com'
        self.user_verified_pw = 'user_verified'
        self.user_verified = get_user_model().objects.create_user(self.user_verified_email, 'pw')
        self.user_verified.is_verified = True
        self.user_verified.save()

        # User who is not verified yet on the site
        self.user_not_verified_email = 'user_not_verified@mail.com'
        self.user_not_verified_pw = 'user_not_verified'
        self.user_not_verified = get_user_model().objects.create_user(self.user_not_verified_email, 'pw')
        self.user_not_verified.save()

        # Email address available
        self.available_email = 'available@mail.com'

    def test_email_change_no_auth_token(self):
        url = reverse('authemail-email-change')
        payload = {
            'email': self.user_to_change_email,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Authentication credentials were not provided.')

    def test_email_change_invalid_auth_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + 'XXX')
        url = reverse('authemail-email-change')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid token.')

    def test_email_change_serializer_errors(self):
        error_dicts = [
            # Email required
            {'payload': {'email': ''},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'This field may not be blank.')
             },
            # Email must be valid
            {'payload': {'email': 'abc'},
             'status_code': status.HTTP_400_BAD_REQUEST,
             'error': ('email', 'Enter a valid email address.')
             },
        ]

        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-email-change')
        for error_dict in error_dicts:
            response = self.client.post(url, error_dict['payload'])

            self.assertEqual(response.status_code, error_dict['status_code'])
            self.assertEqual(response.data[error_dict['error'][0]][0],
                             error_dict['error'][1])

    def test_email_change_user_verified_so_email_taken(self):
        # Send Email Change request
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-email-change')
        payload = {
            'email': self.user_verified_email,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Email address already taken.')

    def test_email_change_user_not_verified_code_created_and_emails_sent(self):
        # Send Email Change request
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-email-change')
        payload = {
            'email': self.user_not_verified_email,
        }
        response = self.client.post(url, payload)

        # Confirm that email change code created
        email_change_code = EmailChangeCode.objects.latest('code')
        self.assertEqual(email_change_code.user.email, self.user_to_change_email)
        self.assertEqual(email_change_code.email, self.user_not_verified_email)

        # Confirm that email address in response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], payload['email'])

        # Confirm that two emails sent and that Subject correct
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, 'Notify Previous Email Address')
        self.assertEqual(mail.outbox[1].subject, 'Confirm New Email Address')

    def test_email_change_no_other_user_code_created_and_emails_sent(self):
        # Create two past change codes that aren't used
        email_change_code_old1 = EmailChangeCode.objects.create_email_change_code(
            self.user_to_change, self.user_not_verified_email)
        email_change_code_old2 = EmailChangeCode.objects.create_email_change_code(
            self.user_to_change, self.user_not_verified_email)
        count = EmailChangeCode.objects.filter(user=self.user_to_change).count()
        self.assertEqual(count, 2)

        # Send Email Change request
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-email-change')
        payload = {
            'email': self.available_email,
        }
        response = self.client.post(url, payload)

        # Get email change code
        email_change_code = EmailChangeCode.objects.latest('code')

        # Confirm that old email change codes deleted
        count = EmailChangeCode.objects.filter(user=self.user_to_change).count()
        self.assertEqual(count, 1)
        self.assertNotEqual(email_change_code.code, email_change_code_old1.code)
        self.assertNotEqual(email_change_code.code, email_change_code_old2.code)

        # Confirm that new email change code created properly
        self.assertEqual(email_change_code.user.email, self.user_to_change_email)
        self.assertEqual(email_change_code.email, self.available_email)

        # Confirm that email address in response
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], payload['email'])

        # Confirm that two emails sent and that Subject correct
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, 'Notify Previous Email Address')
        self.assertEqual(mail.outbox[1].subject, 'Confirm New Email Address')

    def test_email_change_verify_invalid_code(self):
        url = reverse('authemail-email-change-verify')
        params = {
            'code': 'XXX',
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unable to verify user.')

    def test_email_change_verify_expired_code(self):
        # Send Email Change request
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-email-change')
        payload = {
            'email': self.available_email,
        }
        response = self.client.post(url, payload)

        # Get email change code and make it expire
        email_change_code = EmailChangeCode.objects.latest('code')
        email_change_code.created_at += timedelta(days=-(EmailChangeCode.objects.get_expiry_period()+1))
        email_change_code.save()
        code_lapsed = email_change_code.code

        # Confirm email change code_lapsed can't be used
        url = reverse('authemail-email-change-verify')
        params = {
            'code': code_lapsed,
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Unable to verify user.')

    def test_email_change_verify_user_verified_so_email_taken(self):
        # Send Email Change request
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-email-change')
        payload = {
            'email': self.user_not_verified_email,
        }
        response = self.client.post(url, payload)

        # Get email change code and make email that of a verified user
        email_change_code = EmailChangeCode.objects.latest('code')
        email_change_code.email = self.user_verified_email
        email_change_code.save()

        # Confirm email address taken
        url = reverse('authemail-email-change-verify')
        params = {
            'code': email_change_code,
        }
        response = self.client.get(url, params)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Email address already taken.')

    def test_email_change_verify_user_not_verified_change_email(self):
        # Send Email Change request
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-email-change')
        payload = {
            'email': self.user_not_verified_email,
        }
        response = self.client.post(url, payload)

        # Get email change code and number of users
        email_change_code = EmailChangeCode.objects.latest('code')
        num_users = get_user_model().objects.count()

        # Confirm user_not_verified deleted, email changed, email change code deleted
        url = reverse('authemail-email-change-verify')
        params = {
            'code': email_change_code,
        }
        response = self.client.get(url, params)

        num_users_minus_1 = get_user_model().objects.count()
        self.assertEqual(num_users, num_users_minus_1 + 1)

        try:
            user_exists = get_user_model().objects.get(email=email_change_code.email)
        except get_user_model().DoesNotExist:
            self.fail('User did not get email address changed.')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'Email address changed.')

        num_codes = EmailChangeCode.objects.filter(code=email_change_code.code).count()
        self.assertEqual(num_codes, 0)

    def test_email_change_verify_no_other_user_change_email(self):
        # Send Email Change request
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-email-change')
        payload = {
            'email': self.available_email,
        }
        response = self.client.post(url, payload)

        # Get email change code
        email_change_code = EmailChangeCode.objects.latest('code')

        # Confirm email changed email change code deleted
        url = reverse('authemail-email-change-verify')
        params = {
            'code': email_change_code,
        }
        response = self.client.get(url, params)

        try:
            user_exists = get_user_model().objects.get(email=email_change_code.email)
        except get_user_model().DoesNotExist:
            self.fail('User did not get email address changed.')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'Email address changed.')

        num_codes = EmailChangeCode.objects.filter(code=email_change_code.code).count()
        self.assertEqual(num_codes, 0)


class PasswordChangeTests(APITestCase):
    def setUp(self):
        # A verified user on the site
        self.user_to_change_email = 'user_to_change@mail.com'
        self.user_to_change_pw = 'pw'
        self.user_to_change = get_user_model().objects.create_user(self.user_to_change_email, self.user_to_change_pw)
        self.user_to_change.is_verified = True
        self.user_to_change.save()

        # Create auth token for user (so user logged in)
        token = Token.objects.create(user=self.user_to_change)
        self.token = token.key

        # New password
        self.user_to_change_pw_new = 'pw new'

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
            'password': self.user_to_change_pw_new,
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
            'password': self.user_to_change_pw_new,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], 'Password changed.')

        # Confirm unable to log in with old password
        url = reverse('authemail-login')
        payload = {
            'email': self.user_to_change_email,
            'password': self.user_to_change_pw,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Unable to login with provided credentials.')

        # Confirm able to log in with new password
        url = reverse('authemail-login')
        payload = {
            'email': self.user_to_change_email,
            'password': self.user_to_change_pw_new,
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)


class UserDetailTests(APITestCase):
    def setUp(self):
        # A verified user on the site
        self.user_me_email = 'user_me@mail.com'
        self.user_me = get_user_model().objects.create_user(self.user_me_email, 'pw')
        self.user_me.is_verified = True
        self.user_me.save()

        # Create auth token for user (so user logged in)
        token = Token.objects.create(user=self.user_me)
        self.token = token.key

    def test_user_me_no_auth_token(self):
        url = reverse('authemail-me')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'],
                         'Authentication credentials were not provided.')

    def test_user_me_invalid_auth_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + 'XXX')
        url = reverse('authemail-me')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['detail'], 'Invalid token.')

    def test_user_me(self):
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token)
        url = reverse('authemail-me')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_me_email)
