#!/usr/bin/env bash

while ! mysqladmin ping -h"$MYSQL_HOST" --silent; do
  sleep 1
done

exec "$@"
