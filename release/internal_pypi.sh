#!/bin/bash

usage () {
    echo "$0 <version>"
    echo "Must also set the following environment variables:"
    echo "- PYPI_URL: the url to the pypi server to upload"
    echo "- PYPI_AUTH_USR: The username to authenticate with"
    echo "- PYPI_AUTH_PSW: The password to authenticate with"

}

if [ ! $# -eq 1 ]; then
    usage
    exit 1
fi

export version=$1

if [ -z ${PYPI_URL} ]; then
    usage
    exit 1
fi

if [[ -z ${PYPI_AUTH_USR} || -z ${PYPI_AUTH_PSW} ]]; then
    usage
    exit 1
fi

if [ ! -f setup.py ]; then
    echo "Must be run from the directory containing setup.py"
    exit 1
fi

set -ex

# bump version
sed -i.bak "s/version=\".*\",/version=\"${version}\",/" setup.py
sed -i.bak "s/download_url=\"\(.*\)\/.*\",/download_url=\"\1\/${version}\",/" setup.py

# build and upload
python3 -m build
python3 -m twine upload \
    --skip-existing \
    --repository-url ${PYPI_URL} \
    --username ${PYPI_AUTH_USR} \
    --password ${PYPI_AUTH_PSW} \
    dist/*
