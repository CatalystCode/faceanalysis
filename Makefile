SHELL=/bin/bash

.PHONY: build pylint flake8 lint test

build:
	DEVTOOLS="true" docker-compose build

pylint: build
	docker-compose run --rm --no-deps --entrypoint=python3 api -m pylint /app/faceanalysis

flake8: build
	docker-compose run --rm --no-deps --entrypoint=python3 api -m flake8 /app/faceanalysis

lint: pylint flake8

test: build
	$(eval data_dir := $(shell mktemp -d))
	$(eval db_dir := $(shell mktemp -d))
	$(eval queue := $(shell echo "faceanalysis$$RANDOM"))
	APP_PORT="8080" DATA_DIR="$(data_dir)" DB_DIR="$(db_dir)" IMAGE_PROCESSOR_QUEUE="$(queue)" \
    docker-compose run --rm api nose2 -v; \
    exit_code=$$?; \
    docker-compose down; \
    rm -rf $(data_dir); \
    rm -rf $(db_dir); \
    exit $$exit_code
