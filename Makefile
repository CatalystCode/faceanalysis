SHELL=/bin/bash

.PHONY: build-dev build-prod pylint flake8 mypy lint test

build-dev:
	DEVTOOLS="true" docker-compose build

build-prod:
	docker-compose build

pylint: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m pylint /app/faceanalysis

flake8: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m flake8 /app/faceanalysis

mypy: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m mypy /app/faceanalysis

lint: pylint flake8 mypy

test: build-dev
	$(eval data_dir := $(shell mktemp -d))
	$(eval db_dir := $(shell mktemp -d))
	$(eval queue_name := $(shell echo "faceanalysisq$$RANDOM"))
	$(eval db_name := $(shell echo "faceanalysisdb$$RANDOM"))
	DATA_DIR="$(data_dir)" DB_DIR="$(db_dir)" IMAGE_PROCESSOR_QUEUE="$(queue_name)" MYSQL_DATABASE="$(db_name)" \
    docker-compose run --rm api nose2 --verbose --with-coverage; \
    exit_code=$$?; \
    docker-compose down; \
    rm -rf $(data_dir); \
    rm -rf $(db_dir); \
    exit $$exit_code

server: build-prod
	docker-compose up
