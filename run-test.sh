#!/usr/bin/env bash

set -e

app_port="8080"
data_dir="$(mktemp -d)"
db_dir="$(mktemp -d)"

cleanup() { rm -rf "${data_dir}" "${db_dir}"; }
trap cleanup EXIT

docker-compose down
docker-compose build

APP_PORT="${app_port}" \
DATA_DIR="${data_dir}" \
DB_DIR="${db_dir}" \
docker-compose run api nose2
