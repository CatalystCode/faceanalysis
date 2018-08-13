# FaceAPI container

Given that the [FaceAPI](https://azure.microsoft.com/en-us/services/cognitive-services/face/)
currently does not expose an endpoint to get embeddings for a face, this algorithm
container has a slightly different interface.

## Training

To train a new FaceAPI model, run the following:

```bash
docker run \
  -e FACE_API_KEY="<change-me>" \
  -e FACE_API_REGION="<change-me>" \
  -v /path/to/training/images:/images \
  face_api_container \
  /images
```

The container expects the directory structure to be laid out like so:

```
/path/to/training/images
├── person1
│   ├── image1.jpg
│   ├── image2.png
│   └── image3.jpeg
├── person2
│   └── image1.png
└── person3
    ├── image1.jpg
    └── image2.png
```

The container will print to stdout the group ID of the trained FaceAPI model.

## Evaluation

After training a model and obtaining a group ID, you can check whether two
prealigned images contain the same face like so:

```bash
docker run \
  -e FACE_API_KEY="<change-me>" \
  -e FACE_API_REGION="<change-me>" \
  -e FACE_API_GROUP_ID="<change-me>" \
  -v /path/to/evaluation/images:/images \
  face_api_container \
  /images/1.jpg \
  /images/2.jpg
```

The container will print `true` to stdout if the two images contain the same
face and `false` otherwise.
