import os
from typing import List

import numpy as np
import tensorflow as tf

from facenet_sandberg import Identifier, get_image_from_path_bgr

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.logging.set_verbosity(tf.logging.ERROR)

FaceVector = List[float]
Image = np.array


def get_face_vectors_batch(
        img_paths: List[str], prealigned: bool) -> List[List[FaceVector]]:
    identifier = Identifier(
        model_path='insightface/insightface_ckpt',
        is_insightface=True)

    images = map(get_image_from_path_bgr, img_paths)
    all_vectors = identifier.vectorize_all(images, prealigned=prealigned)
    identifier.tear_down()
    np_to_list = []
    for vectors in all_vectors:
        np_to_list.append([vector.tolist() for vector in vectors])
    return np_to_list


def _cli():
    from argparse import ArgumentParser
    from argparse import FileType
    from os import getenv
    import json

    parser = ArgumentParser(description=__doc__)
    parser.add_argument('images', type=FileType('r'), nargs='+')

    args = parser.parse_args()
    image_paths = []
    for image in args.images:
        image.close()
        image_paths.append(image.name)

    prealigned = getenv('PREALIGNED') == 'true'

    vectors = get_face_vectors_batch(image_paths, prealigned)

    print(json.dumps({'faceVectors': vectors}))


if __name__ == '__main__':
    _cli()
