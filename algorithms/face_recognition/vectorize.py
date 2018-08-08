import json
import face_recognition as fr


def get_face_vectors(img_path):
    img = fr.load_image_file(img_path)
    face_locations = fr.face_locations(img)
    face_vectors = []
    for top, right, bottom, left in face_locations:
        cropped_img = img[top:bottom, left:right]
        cropped_features = fr.face_encodings(cropped_img)
        if cropped_features:
            face_vector = cropped_features[0]
            face_vectors.append(face_vector.tolist())
    return face_vectors


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
