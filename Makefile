SHELL=/bin/bash

data_dir := $(shell mktemp -d)
db_dir := $(shell mktemp -d)
queue := $(shell echo "faceanalysis$$RANDOM")

.PHONY: build pylint flake8 lint test clean

build:
	DEVTOOLS="true" docker-compose build

pylint: build
	docker-compose run --rm --no-deps --entrypoint=python3 api -m pylint /app/faceanalysis

flake8: build
	docker-compose run --rm --no-deps --entrypoint=python3 api -m flake8 /app/faceanalysis

lint: pylint flake8

test: build
	APP_PORT="8080" DATA_DIR="$(data_dir)" DB_DIR="$(db_dir)" IMAGE_PROCESSOR_QUEUE="$(queue)" docker-compose run --rm api nose2 -v

clean:
	docker-compose down || true
	rm -rf $(data_dir) $(db_dir) || true
