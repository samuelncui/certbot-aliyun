#!/usr/bin/env bash
set -xe;

pip3 install -U pip setuptools;
pip3 install -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com poetry;

poetry source add --priority=primary aliyun https://mirrors.aliyun.com/pypi/simple/;
poetry install;
