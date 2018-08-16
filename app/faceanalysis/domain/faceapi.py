from typing import Dict
from typing import IO
from typing import Iterable
from typing import List
from typing import Tuple

import cognitive_face
from cognitive_face import CognitiveFaceException

from faceanalysis import storage
from faceanalysis.domain.errors import DuplicateImage
from faceanalysis.domain.errors import ImageDoesNotExist
from faceanalysis.log import get_logger
from faceanalysis.models.database_manager import get_database_manager
from faceanalysis.models.image_status_enum import ImageStatusEnum
from faceanalysis.models.models import FaceApiMapping
from faceanalysis.settings import FACE_API_ACCESS_KEY
from faceanalysis.settings import FACE_API_ENDPOINT
from faceanalysis.settings import FACE_API_MODEL_ID
from faceanalysis.storage import StorageError

if not FACE_API_MODEL_ID or not FACE_API_ACCESS_KEY or not FACE_API_ENDPOINT:
    raise ValueError('FaceAPI settings missing')

cognitive_face.Key.set(FACE_API_ACCESS_KEY)
cognitive_face.BaseUrl.set(FACE_API_ENDPOINT)

logger = get_logger(__name__)


# pylint: disable=unused-argument
def process_image(img_id: str):
    model_id, is_new = _get_model_id()

    if is_new:
        raise ImageDoesNotExist()

    try:
        storage.get_image_path(img_id)
    except StorageError:
        raise ImageDoesNotExist()

    cognitive_face.large_face_list.train(
        large_face_list_id=model_id)

    logger.debug('Retraining model %s', model_id)
# pylint: enable=unused-argument


# pylint: disable=unused-argument
def get_processing_status(img_id: str) -> Tuple[str, str]:
    model_id, is_new = _get_model_id()

    if is_new:
        raise ImageDoesNotExist()

    try:
        response = cognitive_face.large_face_list.get_status(
            large_face_list_id=model_id)
    except CognitiveFaceException as ex:
        if ex.code != 'LargeFaceListNotTrained':
            raise
        raise ImageDoesNotExist()

    training_step = response['status']
    error_message = response.get('message')

    logger.debug('Model %s is in status %s', model_id, training_step)

    if training_step in ('notstarted', 'running'):
        status = ImageStatusEnum.processing
    elif training_step in ('succeeded', 'failed'):
        status = ImageStatusEnum.finished_processing
    else:
        raise ValueError('Unknown model status {}'.format(training_step))

    return status.name, error_message
# pylint: enable=unused-argument


def _get_model_id() -> Tuple[str, bool]:
    try:
        cognitive_face.large_face_list.get(
            large_face_list_id=FACE_API_MODEL_ID)
    except CognitiveFaceException as ex:
        if ex.code != 'LargeFaceListNotFound':
            raise
        is_new = True
        cognitive_face.large_face_list.create(
            large_face_list_id=FACE_API_MODEL_ID)
    else:
        is_new = False

    return FACE_API_MODEL_ID, is_new


def upload_image(stream: IO[bytes], filename: str) -> str:
    model_id, _ = _get_model_id()
    img_id = filename[:filename.find('.')]

    db = get_database_manager()
    session = db.get_session()

    mapping = session.query(FaceApiMapping)\
        .filter(FaceApiMapping.img_id == img_id)\
        .first()

    if mapping:
        session.close()
        raise DuplicateImage()

    storage.store_image(stream, filename)
    image_path = storage.get_image_path(img_id)

    faces = cognitive_face.face.detect(image_path)
    if len(faces) != 1:
        face_id = ''
    else:
        response = cognitive_face.large_face_list_face.add(
            image=image_path,
            large_face_list_id=model_id,
            user_data=img_id)
        face_id = response['persistedFaceId']

    mapping = FaceApiMapping(face_id=face_id, img_id=img_id)
    session.add(mapping)
    db.safe_commit(session)

    return img_id


def list_images() -> List[str]:
    db = get_database_manager()
    session = db.get_session()
    mappings = session.query(FaceApiMapping)\
        .all()
    session.close()

    image_ids = [mapping.img_id for mapping in mappings]

    logger.debug('Got %d images', len(image_ids))
    return image_ids


def _fetch_faces_for_person(img_id: str) -> Tuple[List[str], str]:
    db = get_database_manager()
    session = db.get_session()
    mapping = session.query(FaceApiMapping)\
        .filter(FaceApiMapping.img_id == img_id) \
        .first()
    session.close()

    if not mapping:
        logger.debug('No mapping found for image %s', img_id)
        return [], ''

    # FIXME: manage deletion of the files
    img_path = storage.get_image_path(img_id)
    faces = cognitive_face.face.detect(img_path)
    face_ids = [face['faceId'] for face in faces]

    if not face_ids:
        logger.debug('No faces found for image %s', img_id)
        return [], mapping.face_id

    return face_ids, mapping.face_id


def _fetch_matching_faces(face_ids: List[str]) -> Dict[str, float]:
    model_id, _ = _get_model_id()

    matches = []  # type: List[dict]
    for face_id in face_ids:
        face_matches = cognitive_face.face.find_similars(
            face_id=face_id,
            large_face_list_id=model_id)
        matches.extend(face_matches)

    face_id_to_confidence = {}  # type: Dict[str, float]
    for match in matches:
        face_id = match['persistedFaceId']
        new_confidence = match['confidence']
        old_confidence = face_id_to_confidence.get(face_id, -1)
        if new_confidence > old_confidence:
            face_id_to_confidence[face_id] = new_confidence

    return face_id_to_confidence


def _fetch_mappings_for_faces(face_ids: Iterable[str]) -> List[FaceApiMapping]:
    db = get_database_manager()
    session = db.get_session()
    mappings = session.query(FaceApiMapping) \
        .filter(FaceApiMapping.face_id.in_(face_ids)) \
        .all()
    session.close()
    return mappings


def lookup_matching_images(img_id: str) -> Tuple[List[str], List[float]]:
    face_ids, own_id = _fetch_faces_for_person(img_id)
    if not face_ids:
        return [], []

    face_id_to_confidence = _fetch_matching_faces(face_ids)
    face_id_to_confidence.pop(own_id, None)  # exclude self-match
    if not face_id_to_confidence:
        return [], []

    mappings = _fetch_mappings_for_faces(face_id_to_confidence.keys())
    if not mappings:
        return [], []

    images = []
    distances = []
    for mapping in mappings:
        confidence = face_id_to_confidence[mapping.face_id]
        distance = 1 - confidence
        images.append(mapping.img_id)
        distances.append(distance)

    logger.debug('Image %s has %d matches', img_id, len(distances))
    return images, distances
