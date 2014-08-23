Example Project
===============

An example project demonstrating the power of `django-rest-authemail`.
----------------------------------------------------------------------


Features
--------

- Easy to set up.
- Demonstrates how to use `django-rest-authemail`.  Can be extended to AngularJS clients and iOS/Android mobile apps.
- Can be used to test `django-rest-authemail`.


Installation
------------

1. Create a virtual environment.
2. git clone.
3. pip install -r requirements.txt
4. python manage.py syncdb
5. python manage.py migrate
6. python manage.py runserver
7. Open your browser to http://127.0.0.1:8000.

Usage
-----

1. Copy the `settings_email.py.TEMPLATE` file to `settings_email.py` and add your email settings.
2. Test `django-rest-authemail`.

.. code-block:: python

    python manage.py test authemail

3. In browser, type 127.0.0.1:8000/signup.
