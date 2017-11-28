#!usr/bin/env bash
while ! mysqladmin ping -h"mysql-dev" --silent; do
    sleep 1
done
#python main.py
gunicorn --bind 0.0.0.0:5000 wsgi
