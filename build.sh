#!/usr/bin/env bash
set -xe;

CURDIR=$(cd $(dirname $0); pwd);
cd ${CURDIR};

pip install -U pip setuptools;
curl -sSL https://install.python-poetry.org | python3 -;
poetry install;
