from authemail import wrapper


class AuthemailPlus(wrapper.Authemail):
    URLS = {
        'users_me_change': '/users/me/change/',
    }

    def users_me_change(self, **kwargs):
        path = self._get_path('users_me_change')

        payload = {
            'first_name': kwargs.pop('first_name'),
            'last_name': kwargs.pop('last_name'),
            'date_of_birth': kwargs.pop('date_of_birth'),
        }

        response = self._POST(path, kwargs, payload)

        self._set_attrs_to_values(response)
        return response
