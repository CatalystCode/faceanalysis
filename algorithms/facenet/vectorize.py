import json
import os
from typing import List

import numpy as np
import tensorflow as tf
from facenet_sandberg import face


os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.logging.set_verbosity(tf.logging.ERROR)


def get_face_vectors(img_path: str) -> List[List[float]]:
    identifier = identifier = face.Identifier(
        threshold=1.0, facenet_model_checkpoint='20180402-114759.pb')
    image: np.ndarray = identifier.get_image_from_path(img_path)
    vectors: List[np.ndarray] = identifier.vectorize(image)
    return [vector.tolist() for vector in vectors]


def _cli():
    from argparse import ArgumentParser
    from argparse import FileType

    parser = ArgumentParser(description=__doc__)
    parser.add_argument('images', type=FileType('r'), nargs='+')

    args = parser.parse_args()
    image_paths = []
    for image in args.images:
        image.close()
        image_paths.append(image.name)

    # naive implementation for demo purposes, could also batch process images
    vectors = {image_path: get_face_vectors(image_path)
               for image_path in image_paths}

    print(json.dumps({'faceVectors': vectors}))


if __name__ == '__main__':
    _cli()
