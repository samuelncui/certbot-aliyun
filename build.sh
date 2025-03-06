#!/usr/bin/env bash
set -xe;

curl -sSL https://install.python-poetry.org | python3 -;
poetry install;
