#!usr/bin/env bash
while ! mysqladmin ping -h"mysql-dev" --silent; do
    sleep 1
done
python main.py
