SHELL = /bin/bash
build_tag := $(shell grep '^BUILD_TAG=' .env | cut -d'=' -f2-)
docker_repo := $(shell grep '^DOCKER_REPO=' .env | cut -d'=' -f2-)
prod_db := $(shell grep '^DB_DIR=' .env | cut -d'=' -f2-)
prod_data := $(shell grep '^DATA_DIR=' .env | cut -d'=' -f2-)

face_recognition = $(docker_repo)/faceanalysis_facerecognition:$(build_tag)
faceapi = $(docker_repo)/faceanalysis_faceapi:$(build_tag)
facenet = $(docker_repo)/faceanalysis_facenet:$(build_tag)
insightface = $(docker_repo)/faceanalysis_insightface:$(build_tag)

get_famous_people_list = $(docker_repo)/faceanalysis_getfamouspeoplelist:$(build_tag)
get_famous_people_photos = $(docker_repo)/faceanalysis_getfamouspeoplephotos:$(build_tag)
preprocessor = $(docker_repo)/faceanalysis_preprocessor:$(build_tag)
validation = $(docker_repo)/faceanalysis_validation:$(build_tag)

.PHONY: build-dev
build-dev:
	DOCKER_REPO="$(docker_repo)" BUILD_TAG="$(build_tag)" DEVTOOLS="true" \
    docker-compose build

.PHONY: build-prod
build-prod:
	DOCKER_REPO="$(docker_repo)" BUILD_TAG="$(build_tag)" \
    docker-compose build

.PHONY: build-scripts
build-scripts:
	docker build -t "$(preprocessor)" ./scripts/preprocessor
	docker build -t "$(get_famous_people_list)" ./scripts/get_famous_people_list
	docker build -t "$(get_famous_people_photos)" ./scripts/get_famous_people_photos
	docker build -t "$(validation)" ./scripts/validation

.PHONY: build-algorithms
build-algorithms:
	docker build -t "$(face_recognition)" algorithms/face_recognition
	docker build -t "$(faceapi)" algorithms/FaceApi
	docker build -t "$(facenet)" algorithms/facenet
	docker build -t "$(insightface)" algorithms/insightface

.PHONY: release-server
release-server: build-prod
	DOCKER_REPO="$(docker_repo)" BUILD_TAG="$(build_tag)" \
    docker-compose push

.PHONY: release-algorithms
release-algorithms: build-algorithms
	docker push "$(face_recognition)"
	docker push "$(faceapi)"
	docker push "$(facenet)"
	docker push "$(insightface)"

.PHONY: pylint-scripts
pylint-scripts: build-scripts
	docker run -v $$PWD/app/.pylintrc:/app/.pylintrc --entrypoint=sh "$(get_famous_people_list)" -c "pip -qq install pylint && pylint --rcfile=/app/.pylintrc /app/get_famous_people_list/src"
	docker run -v $$PWD/app/.pylintrc:/app/.pylintrc --entrypoint=sh "$(get_famous_people_photos)" -c "pip -qq install pylint && pylint --rcfile=/app/.pylintrc /app/get_famous_people_photos/src"
	docker run -v $$PWD/app/.pylintrc:/app/.pylintrc --entrypoint=sh "$(preprocessor)" -c "pip -qq install pylint && pylint --rcfile=/app/.pylintrc /app/preprocessor/src"
	docker run -v $$PWD/app/.pylintrc:/app/.pylintrc --entrypoint=sh "$(validation)" -c "pip -qq install pylint && pylint --rcfile=/app/.pylintrc /app/validation/src"

.PHONY: flake8-scripts
flake8-scripts: build-scripts
	docker run --entrypoint=sh "$(get_famous_people_list)" -c "pip -qq install flake8 && flake8 /app/get_famous_people_list/src"
	docker run --entrypoint=sh "$(get_famous_people_photos)" -c "pip -qq install flake8 && flake8 /app/get_famous_people_photos/src"
	docker run --entrypoint=sh "$(preprocessor)" -c "pip -qq install flake8 && flake8 /app/preprocessor/src"
	docker run --entrypoint=sh "$(validation)" -c "pip -qq install flake8 && flake8 /app/validation/src"

.PHONY: mypy-scripts
mypy-scripts: build-scripts
	docker run -v $$PWD/app/mypy.ini:/app/mypy.ini --entrypoint=sh "$(get_famous_people_list)" -c "pip -qq install mypy && mypy --config-file=/app/mypy.ini /app/get_famous_people_list/src"
	docker run -v $$PWD/app/mypy.ini:/app/mypy.ini --entrypoint=sh "$(get_famous_people_photos)" -c "pip -qq install mypy && mypy --config-file=/app/mypy.ini /app/get_famous_people_photos/src"
	docker run -v $$PWD/app/mypy.ini:/app/mypy.ini --entrypoint=sh "$(preprocessor)" -c "pip -qq install mypy && mypy --config-file=/app/mypy.ini /app/preprocessor/src"
	docker run -v $$PWD/app/mypy.ini:/app/mypy.ini --entrypoint=sh "$(validation)" -c "pip -qq install mypy && mypy --config-file=/app/mypy.ini /app/validation/src"

.PHONY: lint-scripts
lint-scripts: pylint-scripts flake8-scripts mypy-scripts

.PHONY: pylint
pylint: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m pylint /app/faceanalysis

.PHONY: flake8
flake8: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m flake8 /app/faceanalysis

.PHONY: mypy
mypy: build-dev
	docker-compose run --rm --no-deps --entrypoint=python3 api -m mypy /app/faceanalysis

.PHONY: lint
lint: pylint flake8 mypy

.PHONY: test
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

.PHONY: server
createdb: build-prod
	mkdir -p $(prod_db)
	docker-compose run --rm api python3 /app/main.py createdb

.PHONY: server
server: build-prod
	mkdir -p $(prod_data)
	docker-compose up
