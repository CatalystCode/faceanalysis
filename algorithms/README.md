# Face vectorization algorithm container interface

This directory contains a number of face vectorization implementations, each
exposing a unified interface so that the algorithms can be used interchangeably
in the faceanalysis app and in evaluation scripts.

The algorithm container will be called like so:

```bash
docker run -v /path/to/images:/data the_algorithm_container /data/image1.jpg ... /data/imageN.jpg
```

Each of the paths passed as arguments to the container is a raw image file.
The container must find all the faces in the image and create a face embedding
for each of the faces. If the environment variable `PREALIGNED=true` is set in
the container, the face finding step can be skipped and the container should
assume that each image contains a single cropped face.

The container is expected output the following JSON structure to stdout:

```js
{
  "faceVectors": [
    [
      [0, 1, 2, 3],  // face vector for the first person in the first image
                     // ...
      [4, 5, 6, 7]   // face vector for the last person in the first image
    ],
                     //
                     // ...
                     //
    [
      [3, 2, 1, 0],  // face vector for the first person in the Nth image
                     // ...
      [7, 6, 5, 4]   // face vector for the last person in the Nth image
    ]
  ]
}
```
