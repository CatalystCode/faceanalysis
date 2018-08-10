# Face vectorization algorithm container interface

This directory contains a number of face vectorization implementations, each
exposing a unified interface so that the algorithms can be used interchangeably
in the faceanalysis app and in evaluation scripts.

The algorithm container will be called like so:

```bash
docker run -v /path/to/images:/data the_algorithm_container /data/image1.jpg ... /data/imageN.jpg
```

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
