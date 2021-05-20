# -*- coding: utf-8 -*-

# See http://pythonhosted.org/an_example_pypi_project/setuptools.html
# See https://packaging.python.org/tutorials/packaging-projects/#uploading-your-project-to-pypi

from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="django-rest-authemail",
    version="2.0.6",
    author="Celia Oakley",
    author_email="celia.oakley@alumni.stanford.edu",
    description="A RESTful API for user signup and authentication using email addresses",
    keywords=[
        "django",
        "python",
        "rest",
        "rest-framework",
        "api",
        "auth",
        "authentication",
        "email",
        "user",
        "username",
        "registration",
        "signup",
        "login",
        "logout",
        "password",
        "django-rest-framework",
        "djangorestframework",
        "django-registration",
        "django-email-as-username",
    ],
    url="http://github.com/celiao/django-rest-authemail",
    download_url="https://github.com/celiao/django-rest-authemail/tarball/2.0.6",
    packages=["authemail"],
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "Django>=2.2.8,<=3.2",
        "djangorestframework<=3.12",
        "requests>=2.3.0",
        "mmh3>=3.0",
        "ua-parser>=0.10",
        "django-ipware>=3.0.2",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development",
        "Topic :: Utilities",
    ],
)
