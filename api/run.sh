#!usr/bin/env bash
if [ "$TESTING" == "TRUE" ]; then
    while ! mysqladmin ping -h"$MYSQL_CONTAINER_NAME" --silent; do
        sleep 1
    done
    sleep 20
    nose2
else
    while ! mysqladmin ping -h"$MYSQL_CONTAINER_NAME" --silent; do
        sleep 1
    done
    gunicorn --bind 0.0.0.0:5000 wsgi
fi
