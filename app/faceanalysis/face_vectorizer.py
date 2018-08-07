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
            face_vectors.append(face_vector)
    return face_vectors
