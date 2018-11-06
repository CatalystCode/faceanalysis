from typing import Iterable, List, Optional

import numpy as np

from face_recognition import face_encodings, face_locations, load_image_file

FaceVector = List[float]
Image = np.array


def get_face_embedding(face: Image) -> Optional[FaceVector]:
    cropped_features = face_encodings(face)
    if not cropped_features:
        return None

    face_vector = cropped_features[0]
    return face_vector.tolist()


def find_faces(img: Image) -> Iterable[Image]:
    for top, right, bottom, left in face_locations(img):
        yield img[top:bottom, left:right]


def get_face_vectors(img_path: str, prealigned: bool) -> List[FaceVector]:
    img = load_image_file(img_path)
    faces = [img] if prealigned else find_faces(img)

    face_vectors = []
    for face in faces:
        face_vector = get_face_embedding(face)
        if face_vector:
            face_vectors.append(face_vector)
    return face_vectors


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

    # naive implementation for demo purposes, could also batch process images
    vectors = [get_face_vectors(image_path, prealigned)
               for image_path in image_paths]

    print(json.dumps({'faceVectors': vectors}))


if __name__ == '__main__':
    _cli()
