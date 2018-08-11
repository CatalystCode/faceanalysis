from typing import Iterable
from typing import List
from typing import Optional

import face_recognition as fr
import numpy as np

FaceVector = List[float]
Image = np.array


def get_face_embedding(face: Image) -> Optional[FaceVector]:
    cropped_features = fr.face_encodings(face)
    if not cropped_features:
        return None

    face_vector = cropped_features[0]
    return face_vector.tolist()


def find_faces(img: Image) -> Iterable[Image]:
    face_locations = fr.face_locations(img)
    for top, right, bottom, left in face_locations:
        yield img[top:bottom, left:right]


def get_face_vectors(img_path: str) -> List[FaceVector]:
    img = fr.load_image_file(img_path)
    faces = find_faces(img)

    face_vectors = []
    for face in faces:
        face_vector = get_face_embedding(face)
        if face_vector:
            face_vectors.append(face_vector)
    return face_vectors


def _cli():
    from argparse import ArgumentParser
    from argparse import FileType
    import json

    parser = ArgumentParser(description=__doc__)
    parser.add_argument('images', type=FileType('r'), nargs='+')

    args = parser.parse_args()
    image_paths = []
    for image in args.images:
        image.close()
        image_paths.append(image.name)

    # naive implementation for demo purposes, could also batch process images
    vectors = [get_face_vectors(image_path)
               for image_path in image_paths]

    print(json.dumps({'faceVectors': vectors}))


if __name__ == '__main__':
    _cli()
