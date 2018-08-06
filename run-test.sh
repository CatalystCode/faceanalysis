#!/usr/bin/env bash

set -e

app_port="8080"
data_dir="$(mktemp -d)"
db_dir="$(mktemp -d)"

cleanup() { rm -rf "${data_dir}" "${db_dir}"; }
trap cleanup EXIT

docker-compose down
docker-compose build --build-arg DEVTOOLS=true

docker-compose run --rm --no-deps --entrypoint=python3 api -m pylint /app/api

APP_PORT="${app_port}" \
DATA_DIR="${data_dir}" \
DB_DIR="${db_dir}" \
docker-compose run --rm api nose2
