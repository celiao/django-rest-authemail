import os
from setuptools import setup

setup(
    name='django-rest-authemail',
    version='1.0.0',
    author='Celia Oakley',
    author_email='celia.oakley@alumni.stanford.edu',
    description='A RESTful API for user signup and authentication using email addresses',
    keywords=[
        'django', 'python', 'rest', 'rest-framework', 'api', 
        'auth', 'authentication', 'email', 'user', 'username', 
        'registration', 'signup', 'login', 'logout', 'password',
        'django-rest-framework', 'djangorestframework', 'django-registration', 
        'django-email-as-username'
    ],
    url='http://github.com/celiao/django-rest-authemail',
    download_url='https://github.com/celiao/django-rest-authemail/tarball/1.0.0',
    license='GPLv3 licence, see LICENSE file',
    packages=['authemail'],
    include_package_data=True,
    long_description=open('README.rst').read(),
    install_requires=[
        'Django==1.7',
        'djangorestframework==3.3.3',
        'requests>=2.3.0',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
)
