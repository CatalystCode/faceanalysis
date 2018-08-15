SHELL = /bin/bash
build_tag := $(shell grep '^BUILD_TAG=' .env | cut -d'=' -f2-)
docker_repo := $(shell grep '^DOCKER_REPO=' .env | cut -d'=' -f2-)

.PHONY: build-dev build-prod build-algorithms release-server release-algorithms pylint flake8 mypy lint test

build-dev:
	DOCKER_REPO="$(docker_repo)" BUILD_TAG="$(build_tag)" DEVTOOLS="true" \
    docker-compose build

build-prod:
	DOCKER_REPO="$(docker_repo)" BUILD_TAG="$(build_tag)" \
    docker-compose build

build-algorithms:
	docker build -t "$(docker_repo)/faceanalysis_facerecognition:$(build_tag)" algorithms/face_recognition
	docker build -t "$(docker_repo)/faceanalysis_faceapi:$(build_tag)" algorithms/FaceApi
	docker build -t "$(docker_repo)/faceanalysis_facenet:$(build_tag)" algorithms/facenet
	docker build -t "$(docker_repo)/faceanalysis_insightface:$(build_tag)" algorithms/insightface

release-server: build-prod
	DOCKER_REPO="$(docker_repo)" BUILD_TAG="$(build_tag)" \
    docker-compose push

release-algorithms: build-algorithms
	docker push "$(docker_repo)/faceanalysis_facerecognition:$(build_tag)"
	docker push "$(docker_repo)/faceanalysis_faceapi:$(build_tag)"
	docker push "$(docker_repo)/faceanalysis_facenet:$(build_tag)"
	docker push "$(docker_repo)/faceanalysis_insightface:$(build_tag)"

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
