#!usr/bin/env bash
while ! mysqladmin ping -h"$MYSQL_CONTAINER_NAME" --silent; do
    sleep 1
done
python main.py
