#!/usr/bin/env bash

mysql_is_available() {
  mysqladmin ping -h"$MYSQL_HOST" -u"${MYSQL_USER}" -p"${MYSQL_PASSWORD}" --silent > /dev/null
}

rabbitmq_is_available() {
  local status="$(curl -s -u "${RABBITMQ_USER:-guest}:${RABBITMQ_PASSWORD:-guest}" "http://${RABBITMQ_HOST}:15672/api/healthchecks/node" | jq -r ".status")"
  test "${status}" = "ok"
}

until mysql_is_available; do echo "Waiting for MySQL"; sleep 3; done
echo "MySQL is alive"

until rabbitmq_is_available; do echo "Waiting for RabbitMQ"; sleep 3; done
echo "RabbitMQ is alive"

exec "$@"
