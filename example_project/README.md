example_project
===============

An example project demonstrating the power of `django-rest-authemail`.


Features
--------

- Easy to set up.
- Can be used to test `django-rest-authemail`.
- Demonstrates how to use `django-rest-authemail`.
- Can be extended to React and AngularJS front end clients and iOS/Android mobile apps.


Installation
------------

Create a virtual environment and activate it.

```python
virtualenv -p /usr/local/bin/python3.7 ~/.virtualenvs/example_project-3.7
source ~/.virtualenvs/example_project-3.7/bin/activate
```

Clone the `django-rest-authemail` repo.

```python
git clone https://github.com/celiao/django-rest-authemail.git
```

All you need is the `example_project` directory, so extract `example_project` and delete the other files and directories.

```
mv django-rest-authemail/example_project .
rm -rf django-rest-authemail
```

Change into the `example_project` directory.

```
cd example_project
```

Install the required packages into your virtual environment.

```python
pip install -r requirements.txt
```

Either add your email settings to your environment or enter them directly at the bottom of the `settings.py` file.  The setting `AUTH_EMAIL_VERIFICATION` (default: True) can be set to False, if you don't want email verification to be performed.

```python
vim example_project/settings.py
```

Create the database tables with Django's `migrate` and create a superuser with `createsuperuser`.

```python
python manage.py migrate
python manage.py createsuperuser
```

Usage
-----

Test `django-rest-authemail`.  There shouldn't be any failures, but if there are, try to address them (most likely in your email settings).  Go onto the next step for more clues, if you get stuck.

```python
python manage.py test authemail
```

Check your setup by starting a Web server on your local machine.

```python
python manage.py runserver
```

Direct your browser to the `Django /admin` interface, and log in.  You should see `Users`, `Verified Users`, `Tokens`, `Password reset codes`, `Signup codes`, and `Groups`.  If you click on `Users`, you should see your superuser account.

```python
http://127.0.0.1:8000/admin
```

Begin the playing with `django-rest-authemail` by going to the `/landing` page.

```python
http://127.0.0.1:8000/landing
```

Click on the `Signup` link, or go to the `/signup` page directly.

```python
http://127.0.0.1:8000/signup
```

Enter your signup details.  A verification email will be sent to the email address you enter, so include an email address to which you have access (but not the superuser email you entered earlier).  If you don't see the email in your inbox, check your spam folder.

Once you have entered your signup information and submitted the form, open up a new tab in your browser and go to the `Django /admin`.  Click on `Signup codes` to see the newly issued code. A new `User` will have been created with the email address, but will not yet appear under `Verified users`.

Go to the inbox for the email address and click on the link in the verification email.  The `code` in the email should match that in the database.

Go back to the `Django /admin` and check that the `Signup code` has been removed and that your email address appears on the `Verified users` list.

Now, go back to the `Email Verified` page and click on the `Login` link, or go to the `/login` page directly.

```python
http://127.0.0.1:8000/login
```

Login with your credentials.  Go back to the `Django /admin` and click on `Tokens` to see your newly issued authorization token.

Go back to your `Home` page and click on the `Logout` button.  You will be returned to the `/landing` page.

Click on the `Login` link and check out the `Forgot Password` functionality.

Login and check out the `Change Email`, `Change Password`, and `Change Me`  functionality.  Logout and log in again to confirm that your password has been changed.

Enter incorrect email addresses and passwords to exercise the error messages.
