import json
import requests

from django.core.serializers.json import DjangoJSONEncoder


# API class from https://pypi.python.org/pypi/tmdbsimple
class API(object):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Connection': 'close'
    }
    BASE_PATH = ''
    URLS = {}

    def __init__(self):
        self.base_uri = 'http://127.0.0.1:8000/api'

    def _get_path(self, key):
        return self.BASE_PATH + self.URLS[key]

    def _get_complete_url(self, path):
        return'{base_uri}/{path}'.format(base_uri=self.base_uri, path=path)

    def _request(self, method, path, params=None, payload=None):
        url = self._get_complete_url(path)

        headers = self.headers.copy()
        if 'token' in params:
            headers.update({'Authorization': 'Token ' + params['token']})

        response = requests.request(
            method, url, params=params,
            data=json.dumps(payload, cls=DjangoJSONEncoder) if payload else payload,
            headers=headers)

        response.encoding = 'utf-8'
        return response.json()

    def _GET(self, path, params=None):
        return self._request('GET', path, params=params)

    def _POST(self, path, params=None, payload=None):
        return self._request('POST', path, params=params, payload=payload)

    def _set_attrs_to_values(self, response={}):
        """
        Set attributes to dictionary values so can access via dot notation.
        """
        for key in response.keys():
            setattr(self, key, response[key])


class Authemail(API):
    BASE_PATH = 'accounts'
    URLS = {
        'signup': '/signup/',
        'signup_verify': '/signup/verify/',
        'login': '/login/',
        'logout': '/logout/',
        'password_reset': '/password/reset/',
        'password_reset_verify': '/password/reset/verify/',
        'password_reset_verified': '/password/reset/verified/',
        'password_change': '/password/change/',
        'users_me': '/users/me/',
    }

    def signup(self, **kwargs):
        path = self._get_path('signup')

        payload = {
            'email': kwargs.pop('email'),
            'password': kwargs.pop('password'),
            'first_name': kwargs.pop('first_name'),
            'last_name': kwargs.pop('last_name'),
        }

        response = self._POST(path, kwargs, payload)

        self._set_attrs_to_values(response)
        return response

    def signup_verify(self, **kwargs):
        path = self._get_path('signup_verify')

        response = self._GET(path, kwargs)

        self._set_attrs_to_values(response)
        return response

    def login(self, **kwargs):
        path = self._get_path('login')

        payload = {
            'email': kwargs.pop('email'),
            'password': kwargs.pop('password'),
        }

        response = self._POST(path, kwargs, payload)

        self._set_attrs_to_values(response)
        return response

    def logout(self, **kwargs):
        path = self._get_path('logout')

        response = self._GET(path, kwargs)

        self._set_attrs_to_values(response)
        return response

    def password_reset(self, **kwargs):
        path = self._get_path('password_reset')

        payload = {
            'email': kwargs.pop('email'),
        }

        response = self._POST(path, kwargs, payload)

        self._set_attrs_to_values(response)
        return response

    def password_reset_verify(self, **kwargs):
        path = self._get_path('password_reset_verify')

        response = self._GET(path, kwargs)

        self._set_attrs_to_values(response)
        return response

    def password_reset_verified(self, **kwargs):
        path = self._get_path('password_reset_verified')

        payload = {
            'code': kwargs.pop('code'),
            'password': kwargs.pop('password'),
        }

        response = self._POST(path, kwargs, payload)

        self._set_attrs_to_values(response)
        return response

    def password_change(self, **kwargs):
        path = self._get_path('password_change')

        payload = {
            'password': kwargs.pop('password'),
        }

        response = self._POST(path, kwargs, payload)

        self._set_attrs_to_values(response)
        return response

    def users_me(self, **kwargs):
        path = self._get_path('users_me')

        response = self._GET(path, kwargs)

        self._set_attrs_to_values(response)
        return response
