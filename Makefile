SHELL = /bin/bash
build_tag := $(shell grep '^BUILD_TAG=' .env | cut -d'=' -f2-)
docker_repo := $(shell grep '^DOCKER_REPO=' .env | cut -d'=' -f2-)
prod_db := $(shell grep '^DB_DIR=' .env | cut -d'=' -f2-)
prod_data := $(shell grep '^DATA_DIR=' .env | cut -d'=' -f2-)

face_recognition = $(docker_repo)/faceanalysis_facerecognition:$(build_tag)
faceapi = $(docker_repo)/faceanalysis_faceapi:$(build_tag)
facenet = $(docker_repo)/faceanalysis_facenet:$(build_tag)
insightface = $(docker_repo)/faceanalysis_insightface:$(build_tag)

.PHONY: build-dev build-prod build-algorithms release-server release-algorithms pylint flake8 mypy lint test

build-dev:
	DOCKER_REPO="$(docker_repo)" BUILD_TAG="$(build_tag)" DEVTOOLS="true" \
    docker-compose build

build-prod:
	DOCKER_REPO="$(docker_repo)" BUILD_TAG="$(build_tag)" \
    docker-compose build

build-algorithms:
	docker build -t "$(face_recognition)" algorithms/face_recognition
	docker build -t "$(faceapi)" algorithms/FaceApi
	docker build -t "$(facenet)" algorithms/facenet
	docker build -t "$(insightface)" algorithms/insightface

release-server: build-prod
	DOCKER_REPO="$(docker_repo)" BUILD_TAG="$(build_tag)" \
    docker-compose push

release-algorithms: build-algorithms
	docker push "$(face_recognition)"
	docker push "$(faceapi)"
	docker push "$(facenet)"
	docker push "$(insightface)"

pylint: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m pylint /app/faceanalysis

flake8: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m flake8 /app/faceanalysis

mypy: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m mypy /app/faceanalysis

lint: pylint flake8 mypy

test: build-dev
	$(eval test_data := $(shell mktemp -d))
	$(eval test_db := $(shell mktemp -d))
	$(eval queue_name := $(shell echo "faceanalysisq$$RANDOM"))
	$(eval db_name := $(shell echo "faceanalysisdb$$RANDOM"))
	DATA_DIR="$(test_data)" DB_DIR="$(test_db)" IMAGE_PROCESSOR_QUEUE="$(queue_name)" MYSQL_DATABASE="$(db_name)" \
    docker-compose run --rm api nose2 --verbose --with-coverage; \
    exit_code=$$?; \
    docker-compose down; \
    rm -rf $(test_data); \
    rm -rf $(test_db); \
    exit $$exit_code

createdb: build-prod
	mkdir -p $(prod_db)
	docker-compose run --rm api python3 /app/main.py createdb

server: build-prod
	mkdir -p $(prod_data)
	docker-compose up
