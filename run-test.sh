#!/usr/bin/env bash

set -e

data_dir="$(mktemp -d)"
db_dir="$(mktemp -d)"

cleanup() {
  set +e
  rm -rf "${data_dir}" "${db_dir}"
  docker-compose down
}
trap cleanup EXIT

DEVTOOLS="true" \
docker-compose build

docker-compose run --rm --no-deps --entrypoint=python3 api -m pylint /app/faceanalysis
docker-compose run --rm --no-deps --entrypoint=python3 api -m flake8 /app/faceanalysis

APP_PORT="8080" \
DATA_DIR="${data_dir}" \
DB_DIR="${db_dir}" \
docker-compose run --rm api nose2
