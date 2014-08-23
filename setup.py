import os
from setuptools import setup

setup(
    name='django-rest-authemail',
    version='0.0.1',
    author='Celia Oakley',
    author_email='celia.oakley@alumni.stanford.edu',
    description='A RESTful API for user signup and authentication using email addresses',
    keywords=[
        'django', 'rest', 'rest-framework', 'api', 
        'auth', 'authentication', 'email', 'user', 'username', 
        'registration', 'signup', 'login', 'logout', 'password',
        'django-rest-framework', 'django-registration', 
        'django-email-as-username'
    ],
    url='http://github.com/celiao/django-rest-authemail',
    download_url='https://github.com/celiao/django-rest-authemail/tarball/0.0.1',
    license='GPLv3 licence, see LICENSE file',
    packages=['authemail'],
    long_description=open('README.rst').read(),
    install_requires=[
        'Django>=1.6.5',
        'South>=0.8.4',
        'djangorestframework>=2.3.14',
        'requests>=2.3.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
)
