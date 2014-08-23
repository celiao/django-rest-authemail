django-rest-authemail
=====================

A RESTful API for user signup and authentication using email addresses. 
-----------------------------------------------------------------------

*django-rest-authemail* is a Django application that provides a RESTful interface for user signup and authentication.  Email addresses are used for authentication, rather than usernames.  Because the authentication user model is based on Django's `AbstractBaseUser` and is itself abstract, the model can be extended without the need for additional database tables.  Token authentication allows the API to be accessed from a variety of front ends, including Django, AngularJS clients, and iOS/Android mobile apps.


Features
--------

- API endpoints for signup, email verification, login, logout, password reset, password reset verification, password change, and user detail.
- Requires the front end to perform password confirmation for a better user experience.
- Extensible abstract user model.
- Token authentication.
- User models in the admin interface include inlines for signup and password reset codes.
- An example project extends the authentication user model and includes simple UI templates.
- Uses the Django REST Framework.
- Supports and tested under Python 2.7.6


Installation
------------

*django-rest-authemail* is available on the Python Package Index (PyPI) at https://pypi.python.org/pypi/django-rest-authemail.

You can install *django-rest-authemail* using one of the following techniques.

- Use pip:

::

    pip install django-rest-authemail

- Download the .zip or .tar.gz file from PyPI and install it yourself
- Download the `source from Github`_ and install it yourself

If you install it yourself, also install the `Django REST Framework`.

.. _source from Github: http://github.com/celiao/django-rest-authemail
.. _Django REST Framework: http://www.django-rest-framework.org


Usage
-----

1. In the `settings.py` file of your project, include `authemail` in `INSTALLED_APPS'. Set the authentication scheme for the Django REST Framework to `TokenAuthentication`.

.. code-block:: python

    INSTALLED_APPS = (
        ...
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

Also include your application in your `INSTALLED_APPS` setting.

3. In the `models.py` file of your application, extend `EmailAbstractUser`, add custom fields, and assign `objects` to `EmailUser Manager()`.  For example,

.. code-block:: python

    class MyUser(EmailAbstractUser):
        # Custom fields
        date_of_birth = models.DateField(_('Date of birth'), null=True, 
            blank=True)

        # Required
        objects = EmailUserManager()

4. In the `admin.py` file of your application, extend `EmailUserAdmin` to add your custom fields.  For example,

.. code-block:: python

    class MyUserAdmin(EmailUserAdmin):
        fieldsets = (
            (None, {'fields': ('email', 'password')}),
            (_('Personal Info'), {'fields': ('first_name', 'last_name')}),
            (_('Permissions'), {'fields': ('is_active', 'is_staff', 
                                           'is_superuser', 'is_verified', 
                                           'groups', 'user_permissions')}),
            (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
            (_('Custom info'), {'fields': ('date_of_birth',)}),
        )

    admin.site.unregister(get_user_model())
    admin.site.register(get_user_model(), MyUserAdmin)

5. Make API calls from your front end code.  For the endpoints requiring authentication (logout, password change, and user detail), include the auth token key in the HTTP header.  For example,

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
A wrapper is available to access the API with Python code.  First create an instance of the AuthEmail class, then call methods to access the API.  There is a one-to-one mapping between the endpoints and instance methods.

.. code-block:: python

    from authemail import wrapper

    account = wrapper.AuthEmail()
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

