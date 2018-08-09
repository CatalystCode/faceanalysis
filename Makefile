SHELL=/bin/bash

.PHONY: build-dev build-prod pylint flake8 lint test

build-dev:
	DEVTOOLS="true" docker-compose build

build-prod:
	docker-compose build

pylint: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m pylint /app/faceanalysis

flake8: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m flake8 /app/faceanalysis

lint: pylint flake8

test: build-dev
	$(eval data_dir := $(shell mktemp -d))
	$(eval db_dir := $(shell mktemp -d))
	$(eval queue_name := $(shell echo "faceanalysisq$$RANDOM"))
	$(eval db_name := $(shell echo "faceanalysisdb$$RANDOM"))
	DATA_DIR="$(data_dir)" DB_DIR="$(db_dir)" IMAGE_PROCESSOR_QUEUE="$(queue_name)" MYSQL_DATABASE="$(db_name)" \
    docker-compose run --rm api nose2 -v; \
    exit_code=$$?; \
    docker-compose down; \
    rm -rf $(data_dir); \
    rm -rf $(db_dir); \
    exit $$exit_code

server: build-prod
	docker-compose up
