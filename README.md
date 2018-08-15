# FaceAnalysis

[![Travis CI status](https://api.travis-ci.org/c-w/faceanalysis.svg?branch=master)](https://travis-ci.org/c-w/faceanalysis)

## What's this?

This repository contains an API for face detection and matching. The algorithm backend used for the computer vision is pluggable and customizable. Currently the following algorithms are supported:

- [Azure FaceAPI](https://azure.microsoft.com/en-us/services/cognitive-services/face/)
- [face_recognition](https://github.com/ageitgey/face_recognition)
- [FaceNet](https://github.com/davidsandberg/facenet)
- [InsightFace (coming soon)](https://github.com/deepinsight/insightface)

More information on customizing and implementing new face detection algorithms can be found [here](./algorithms/README.md).

![Architecture diagram for faceanalysis](https://user-images.githubusercontent.com/1086421/44155170-90283422-a07a-11e8-8f46-7ccf7f98ebd4.png)

## Setup instructions

1. Install [Docker](https://docs.docker.com/install/), [Docker-Compose](https://docs.docker.com/compose/install/) and [GNU Make](https://www.gnu.org/software/make/).
2. Clone this repo.
3. Review the default configuration values in `.env`.
4. To run tests type `make test` from within the top level directory.
5. To run in production type `make server` from within the top level directory.

## API definition

1. Register your user by making a POST request to `/api/v1/register_user` with a `username` and `password`.

2. Optionally retrieve a token by making a GET request to `/api/v1/token` with your username:password in the Authentication header. Access all other resources by passing your_token:any_value in the Authentication header (using Basic Auth) or by passing username:password for each request

3. Upload an image by making a POST request to `/api/v1/upload_image`.

4. Process an image by making a POST request to `/api/v1/process_image`. This will extract face vectors for the image and match it against all other images in the database. This is an asynchronous process.

5. Check the status of the image to see if it is finished processing by making a GET request to `/api/v1/process_image/<image_id>`. Once the image is finished processing, it will be removed from the system's storage and only the face vectors and matches are persisted in the system's database.

6. See which other images are matches for a given image by making a GET request to `/api/v1/image_matches/<image_id>`.
