# FaceAPI container

Given that the [FaceAPI](https://azure.microsoft.com/en-us/services/cognitive-services/face/)
currently does not expose an endpoint to get embeddings for a face, this algorithm
container has a slightly different interface.

## Model variants

This container implements three methods of face matching which can be selected
via the `FACE_API_PREDICTION_MODE` environment variable:

1. `Verify` requires no training. The mode simply compares two faces against
   each other and determines whether they are similar or not. When using this
   prediction mode, the `FACE_API_GROUP_ID` environment variable can be set to
   an unused string since the mode does not require a pre-trained model.

2. `Identify` (default) requires training. During training, the mode builds an
   association between people and their faces. At prediction time, the mode
   looks up the N most simliar people for a given face.

3. `FindSimilar` requires training. During training, the mode builds a custom
   list of faces. At prediction time, the mode looks up the N most similar faces
   to the provided face.

## Training

To train a new FaceAPI model, run the following (only required for
`Identify` and `FindSimilar` prediction modes):

```bash
docker run \
  -e FACE_API_KEY="<change-me>" \
  -e FACE_API_REGION="<change-me>" \
  -e FACE_API_PREDICTION_MODE="<change-me>" \
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

## Prediction

After training a model and obtaining a group ID, you can check whether two
prealigned images contain the same face like so:

```bash
docker run \
  -e FACE_API_KEY="<change-me>" \
  -e FACE_API_REGION="<change-me>" \
  -e FACE_API_GROUP_ID="<change-me>" \
  -e FACE_API_PREDICTION_MODE="<change-me>" \
  -v /path/to/evaluation/images:/images \
  face_api_container \
  /images/1.jpg \
  /images/2.jpg
```

The container will print `true` to stdout if the two images contain the same
face and `false` otherwise.

## Evaluation

The model can also be evaluated against a FaceNet pairs.txt file:

```bash
docker run \
  -e FACE_API_KEY="<change-me>" \
  -e FACE_API_REGION="<change-me>" \
  -e FACE_API_GROUP_ID="<change-me>" \
  -e FACE_API_EVALUATE="true" \
  -e FACE_API_PREDICTION_MODE="<change-me>" \
  -v /path/to/evaluation/data:/data \
  face_api_container \
  /data/pairs.txt \
  /data/images
```

The container will print summary statistics like accuracy, precision and
recall to stdout.
