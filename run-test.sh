#!/usr/bin/env bash
./delete-test-data.sh
docker-compose -f docker-compose-test.yml down
docker-compose -f docker-compose-test.yml build
docker-compose -f docker-compose-test.yml up
