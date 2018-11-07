#!/usr/bin/env bash

set -o errexit

python3 ./main.py createdb || true

gunicorn --bind="0.0.0.0:5000" main
