#!/usr/bin/env bash

mysql_is_available() {
  mysqladmin ping -h"$MYSQL_HOST" -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" --silent > /dev/null
}

until mysql_is_available; do echo "Waiting for MySQL"; sleep 3; done
echo "MySQL is alive"

exec "$@"
