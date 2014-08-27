django-rest-authemail
=====================

8/27/14 - DOCUMENTATION UPDATED SUBSTANTIALLY!

`django-rest-authemail` is a Django application that provides a RESTful interface for user signup and authentication.  Email addresses are used for authentication, rather than usernames.  Because the authentication user model is based on Django's `AbstractBaseUser` and is itself abstract, the model can be extended without the need for additional database tables.  Token authentication allows the API to be accessed from a variety of front ends, including Django, AngularJS clients, and iOS and Android mobile apps.


Features
--------

- API endpoints for signup, email verification, login, logout, password reset, password reset verification, password change, and user detail.
- Perform password confirmation on the front end for a better user experience.
- Extensible abstract user model.
- Token authentication.
- User models in the admin interface include inlines for signup and password reset codes.
- Uses the Django REST Framework.
- An example project is included and contains example UI templates.
- Supports and tested under Python 2.7.6


Installation
------------

`django-rest-authemail` is available on the Python Package Index (PyPI) at https://pypi.python.org/pypi/django-rest-authemail.

Install `django-rest-authemail` using one of the following techniques.

- Use pip:

::

    pip install django-rest-authemail

- Download the .tar.gz file from PyPI and install it yourself
- Download the `source from Github`_ and install it yourself

If you install it yourself, also install the `Django`_, `Django REST Framework`_, `South`_, and `requests`_.

.. _source from Github: http://github.com/celiao/django-rest-authemail
.. _Django: https://www.djangoproject.com/
.. _Django REST Framework: http://www.django-rest-framework.org
.. _South: http://south.readthedocs.org/en/latest/index.html
.. _requests: http://www.python-requests.org/en/latest

Usage
-----

1. In the `settings.py` file of your project, include `south`, `rest_framework`, `rest_framework.authtoken`, and `authemail` in `INSTALLED_APPS`. Set the authentication scheme for the Django REST Framework to `TokenAuthentication`.

.. code-block:: python

    INSTALLED_APPS = (
        ...
        'south',
        'rest_framework',
        'rest_framework.authtoken',
        'authemail',
        ...
    )

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.TokenAuthentication',
        )
    }

2. Create a Django application for your user data.  For example,

.. code-block:: python

    python manage.py startapp accounts

3. In the `models.py` file of your application, extend `EmailAbstractUser`, add custom fields, and assign `objects` to `EmailUserManager()`.  For example,

.. code-block:: python

    from django.db import models
    from authemail.models import EmailUserManager, EmailAbstractUser

    class MyUser(EmailAbstractUser):
        # Custom fields
        date_of_birth = models.DateField('Date of birth', null=True, 
            blank=True)

        # Required
        objects = EmailUserManager()

4. In the `settings.py` file of your project, include your application in `INSTALLED_APPS`. Set `AUTH_USER_MODEL` to the class of your user model.  For example,

.. code-block:: python

    AUTH_USER_MODEL = 'accounts.MyUser'

    INSTALLED_APPS = (
        ...
        'rest_framework',
        'rest_framework.authtoken',
        'authemail',
        'accounts',
        ...
    )

5. In the `admin.py` file of your application, extend `EmailUserAdmin` to add your custom fields.  For example,

.. code-block:: python

    from django.contrib import admin
    from django.contrib.auth import get_user_model
    from authemail.admin import EmailUserAdmin

    class MyUserAdmin(EmailUserAdmin):
        fieldsets = (
            (None, {'fields': ('email', 'password')}),
            ('Personal Info', {'fields': ('first_name', 'last_name')}),
            ('Permissions', {'fields': ('is_active', 'is_staff', 
                                           'is_superuser', 'is_verified', 
                                           'groups', 'user_permissions')}),
            ('Important dates', {'fields': ('last_login', 'date_joined')}),
            ('Custom info', {'fields': ('date_of_birth',)}),
        )

    admin.site.unregister(get_user_model())
    admin.site.register(get_user_model(), MyUserAdmin)

6. Create the database tables with `syncdb` and South's `migrate`.  Set up a superuser when prompted by `syncdb`.

.. code-block:: python

    python manage.py syncdb
    python manage.py migrate

7. Convert your `accounts` application to South.  You will receive an error message from South, so fake the initial migration as a workaround (see http://south.aeracode.org/ticket/1179).

.. code-block:: python

    python manage.py convert_to_south accounts
    python manage.py migrate accounts 0001 --fake

8. Check your setup by starting a Web server on your local machine:

.. code-block:: python

    python manage.py runserver

Direct your browser to:

.. code-block:: python

    127.0.0.1:8000/admin

and log in.  You should see `Users`, `Groups`, `Password reset codes`, `Signup codes`, and `Tokens`.  If you click on `Users`, you should see your superuser account.

9. Add the API urls to your projects `urls.py` file.  For example,

.. code-block:: python

    from accounts import views

    urlpatterns = patterns('',
        url(r'^admin/', include(admin.site.urls)),

        url(r'^api/accounts/', include('authemail.urls')),
    )

10. When users signup or reset their password, they will be sent an email with a link and verification code.  Include email settings in your project's `settings.py` file.  See https://docs.djangoproject.com/en/dev/ref/settings/#email-host for more information.  For example,

.. code-block:: python

    # Email settings
    DEFAULT_EMAIL_FROM = 'your_email_address@gmail.com'
    DEFAULT_EMAIL_BCC = ''

    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_HOST_USER = 'your_email_address@gmail.com'
    EMAIL_HOST_PASSWORD = 'xxxx xxxx xxxx xxxx'
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    SERVER_EMAIL = 'your_email_address@gmail.com'

11. Try out API calls by firing up Python and using authemail wrapper (see below) methods.  For example,

.. code-block:: python

    python
    >>> from authemail import wrapper
    >>> account = wrapper.Authemail()
    >>> first_name = 'Your first name'
    >>> last_name = 'Your last name'
    >>> email = 'your_email@gmail.com'
    >>> password = 'Your password'
    >>> response = account.signup(first_name=first_name, last_name=last_name,
    ... email=email, password=password)

In the Django admin, you should see a new user (not verified) and a new signup code.  You should receive an email at `your_email@gmail.com`.  Use the code in the email to verify your email address using the wrapper:

.. code-block:: python

    >>> code = '7f31e7a515df266532df4e00e0cf1967a7de7d17'
    >>> response = account.signup_verify(code=code)

In the Django admin, the new user is now verified and the signup code is absent.The new user can now login and inspect associated login token:

.. code-block:: python

    >>> response = account.login(email=email, password=password)
    >>> account.token
    u'a84d062c1b60a36e6740eb60c6f9da8d1f709322'

You will find the same token for the user in the Django admin.  Find out more information about the user:

.. code-block:: python

    >>> token = 'a84d062c1b60a36e6740eb60c6f9da8d1f709322'
    >>> response = account.users_me(token=token)
    >>> response
    {u'first_name': u'Your first name', u'last_name': u'Your last name', u'email': u'your_email@gmail.com'}

Use the authentication token to logout:

.. code-block:: python

    >>> response = account.logout(token=token)
    >>> response
    {u'success': u'User logged out.'}

Play with password reset and change!

12. If you are having trouble getting your code to execute, or are just curious, try out the Django REST Framework Browsable API.  If you type an Authemail endpoint into your browser, the Browsable API should appear (`runserver` should still be executing from Step 8).  For example,

.. code-block:: python

    127.0.0.1/api/accounts/signup

In the `Content:` field of the Browsable API, type:

.. code-block:: python

    {
        "first_name": "Your first name",
        "last_name": "Your last name",
        "email": "your_email@gmail.com",
        "password": "Your password"
    }

Then click on `POST`.  You will either receive an error message to help in your debugging, or, if your signup was successful:

.. code-block:: python

    {
        "first_name": "Your first name",
        "last_name": "Your last name",
        "email": "your_email@gmail.com",
    }

Try out the other endpoints with the Django REST Framework Browsable API.

13. Make API calls with front end code.  To get started, follow the steps in the `README.rst` for the `example_project`.  Extend the concepts to AngularJS, iOS, and Android front ends.

14. When calling endpoints from the front end that require authentication (logout, password change, and user detail), include the auth token key in the HTTP header.  For example,

.. code-block:: python

    Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

Here's an example using `curl`,

.. code-block:: python

    curl -X GET 'http://127.0.0.1:8000/accounts/logout' \
         -H 'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b' \


API Endpoints
-------------
For the endpoints that follow, the base path is shown as `/api/accounts`.  This path is for example purposes.  It can be customized in your project's `urls.py` file.

**POST /api/accounts/signup**

Call this endpoint to sign up a new user and send a verification email.  Sample email templates are found in `authemail/templates/authemail`.  To override the email templates, copy and modify the sample templates, or create your own, in `your_app/templates/authemail`.

Your front end should handle password confirmation, and if desired, require the visitor to input their first and last names.

Unverified users can sign up multiple times, but only the latest signup code will be active.

- Payload
    
    - email (required)
    - password (required)
    - first_name (optional)
    - last_name (optional)

- Possible responses

.. code-block:: python

    201 (Created)
    Content-Type: application/json
    {
        "email": "amelia.earhart@boeing.com"
        "first_name": "Amelia", 
        "last_name": "Earhart", 
    }

    400 (Bad Request)
    Content-Type: application/json
    {
        "email": [
            "This field is required."
        ], 
        "password": [
            "This field is required."
        ] 
    }

    {
        "email": [
            "Enter a valid email address."
        ]
    }

    {
        "detail": "User with this Email address already exists."
    }

**GET /api/accounts/signup/verify/?code=<code>**

When the user clicks the link in the verification email, the front end should call this endpoint to verify the user.

- Parameters

    - code (required)

- Possible responses

.. code-block:: python

    200 (OK)
    Content-Type: application/json
    {
        "success": "User verified."
    }

    400 (Bad Request)
    Content-Type: application/json
    {
        "detail": "Unable to verify user."
    }

**POST /api/accounts/login**

Call this endpoint to log in a user.  Use the authentication token in future calls to identify the user.

- Payload

    - email (required)
    - password (required)

- Possible responses

.. code-block:: python

    200 (OK)
    Content-Type: application/json
    {
        "token": "91ec67d093ded89e0a752f35188802c261899013"
    }

    400 (Bad Request)
    Content-Type: application/json
    {
        "password": [
            "This field is required."
        ], 
        "email": [
            "This field is required."
        ]
    }

    {
        "email": [
            "Enter a valid email address."
        ]
    }

    401 (Unauthorized)
    {
        "detail": "Authentication credentials were not provided."
    }

    {
        "detail": "Unable to login with provided credentials."
    }

    {
        "detail": "User account not active."
    }

**GET /api/accounts/logout**

Call this endpoint to log out an authenticated user.

- HTTP Header

.. code-block:: python

    Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

- Possible responses

.. code-block:: python

    200 (OK)
    Content-Type: application/json
    {
        "success": "User logged out."
    }

    401 (Unauthorized)
    Content-Type: application/json
    {
        "detail": "Authentication credentials were not provided."
    }

    {
        "detail": "Invalid token"
    }

**POST /api/accounts/password/reset**

Call this endpoint to send an email to a user so they can reset their password.   Similar to signup verification, the password reset email templates are found in `authemail/templates/authemail`.  Override the default templates by placing your similarly-named templates in `your_app/templates/authemail`.

- Payload

    - email (required)

- Possible responses

.. code-block:: python

    201 (Created)
    Content-Type: application/json
    {
        "email": "amelia.earhart@boeing.com"
    }

    400 (Bad Request)
    Content-Type: application/json
    {
        "email": [
            "This field is required."
        ]
    }

    {
        "email": [
            "Enter a valid email address."
        ]
    }

    {
        "detail": "Password reset not allowed."
    }

**GET /api/accounts/password/reset/verify/?code=<code>**

When the user clicks the link in the password reset email, call this endpoint to verify the password reset code.

- Parameters

    - code (required)

- Possible responses

.. code-block:: python

    200 (OK)
    Content-Type: application/json
    {
        "success": "User verified."
    }

    400 (Bad Request)
    Content-Type: application/json
    {
        "password": [
            "This field is required."
        ] 
    }

    400 (Bad Request)
    Content-Type: application/json
    {
        "detail": "Unable to verify user."
    }

**POST /api/accounts/password/reset/verified**

Call this endpoint with the password reset code and the new password, to reset the user's password.  The front end should prompt the user for a confirmation password and give feedback if the passwords don't match.

- Payload

    - code (required)
    - password (required)

- Possible responses

.. code-block:: python

    200 (OK)
    Content-Type: application/json
    {
        "success": "Password reset."
    }

    400 (Bad Request)
    Content-Type: application/json
    {
        "password": [
            "This field is required."
        ] 
    }

    400 (Bad Request)
    Content-Type: application/json
    {
        "detail": "Unable to verify user."
    }

**POST /api/accounts/password/change**

Call this endpoint to change a user's password.

- HTTP Header

.. code-block:: python

    Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

- Payload

    - password (required)

- Possible responses

.. code-block:: python

    200 (OK)
    Content-Type: application/json
    {
        "success": "Password changed."
    }

    400 (Bad Request)
    Content-Type: application/json
    {
        "password": [
            "This field is required."
        ] 
    }

    401 (Unauthorized)
    Content-Type: application/json
    {
        "detail": "Authentication credentials were not provided."
    }

    {
        "detail": "Invalid token"
    }

**GET /api/accounts/users/me**

Call this endpoint after logging in and obtaining an authorization token to learn more about the user.

- HTTP Header

.. code-block:: python

    Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

- Possible responses

.. code-block:: python

    200 (OK)
    Content-Type: application/json
    {
        "id": 1,
        "email": "amelia.earhart@boeing.com",
        "first_name": "Amelia",
        "last_name": "Earhart",
    }
    
    401 (Unauthorized)
    Content-Type: application/json
    {
        "detail": "Authentication credentials were not provided."
    }
    
    {
        "detail": "Invalid token"
    }


Wrapper
-------
A wrapper is available to access the API with Python code.  First create an instance of the Authemail class, then call methods to access the API.  There is a one-to-one mapping between the endpoints and instance methods.

.. code-block:: python

    from authemail import wrapper

    account = wrapper.Authemail()
    response = account.signup(first_name=first_name, last_name=last_name,
        email=email, password=password)

    if 'detail' in response:
        # Handle error condition
    else:
        # Handle good response

See `example_project/views.py` for more sample usage.


Inspiration and Ideas
---------------------
Inspiration and ideas for `django-rest-authemail` were derived from:

- `django-rest-framework`_
- `django-email-as-username`_
- `django-registration`_
- `django-rest-auth`_
- `tmdbsimple`_

.. _django-rest-framework: http://www.django-rest-framework.org/
.. _django-email-as-username: https://pypi.python.org/pypi/django-email-as-username/1.6.7
.. _django-registration: http://django-registration.readthedocs.org/en/latest/ 
.. _django-rest-auth: https://pypi.python.org/pypi/django-rest-auth
.. _tmdbsimple: https://pypi.python.org/pypi/tmdbsimple

