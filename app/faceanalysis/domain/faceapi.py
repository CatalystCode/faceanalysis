from typing import Dict
from typing import IO
from typing import Iterable
from typing import List
from typing import Optional
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
from faceanalysis.settings import FACE_API_GROUP_ID

if not FACE_API_GROUP_ID or not FACE_API_ACCESS_KEY or not FACE_API_ENDPOINT:
    raise ValueError('FaceAPI settings missing')

cognitive_face.Key.set(FACE_API_ACCESS_KEY)
cognitive_face.BaseUrl.set(FACE_API_ENDPOINT)

logger = get_logger(__name__)


# pylint: disable=unused-argument
def process_image(img_id: str):
    group_id, is_new = _get_group_id()

    if is_new:
        raise ImageDoesNotExist()

    cognitive_face.large_person_group.train(
        large_person_group_id=group_id)

    logger.debug('Retraining group %s', group_id)
# pylint: enable=unused-argument


# pylint: disable=unused-argument
def get_processing_status(img_id: str) -> Tuple[str, str]:
    group_id, is_new = _get_group_id()

    if is_new:
        raise ImageDoesNotExist()

    try:
        response = cognitive_face.large_person_group.get_status(
            large_person_group_id=group_id)
    except CognitiveFaceException as ex:
        if ex.code != 'LargePersonGroupNotTrained':
            raise
        raise ImageDoesNotExist()

    training_step = response['status']
    error_message = response.get('message')

    logger.debug('Group %s is in status %s', group_id, training_step)

    if training_step in ('notstarted', 'running'):
        status = ImageStatusEnum.processing
    elif training_step in ('succeeded', 'failed'):
        status = ImageStatusEnum.finished_processing
    else:
        raise ValueError('Unknown training step {}'.format(training_step))

    return status.name, error_message
# pylint: enable=unused-argument


def _get_group_id() -> Tuple[str, bool]:
    try:
        cognitive_face.large_person_group.get(
            large_person_group_id=FACE_API_GROUP_ID)
    except CognitiveFaceException as ex:
        if ex.code != 'LargePersonGroupNotFound':
            raise
        is_new = True
        cognitive_face.large_person_group.create(FACE_API_GROUP_ID)
    else:
        is_new = False

    return FACE_API_GROUP_ID, is_new


def upload_image(stream: IO[bytes], filename: str) -> str:
    # FIXME: implementation assumes that there is only 1 photo of each person
    group_id, _ = _get_group_id()
    img_id = filename[:filename.find('.')]

    db = get_database_manager()
    session = db.get_session()

    mapping = session.query(FaceApiMapping)\
        .filter(FaceApiMapping.img_id == img_id)\
        .first()

    if mapping:
        session.close()
        raise DuplicateImage()

    response = cognitive_face.large_person_group_person.create(
        large_person_group_id=group_id,
        name=img_id)
    person_id = response['personId']

    mapping = FaceApiMapping(person_id=person_id, img_id=img_id)
    session.add(mapping)
    db.safe_commit(session)

    storage.store_image(stream, filename)
    image_path = storage.get_image_path(img_id)

    cognitive_face.large_person_group_person_face.add(
        image=image_path,
        large_person_group_id=group_id,
        person_id=person_id)

    return img_id


def list_images() -> List[str]:
    group_id, _ = _get_group_id()
    image_ids = []  # type: List[str]

    start = 0
    top = 1000
    num_pages = 1
    while True:
        people = cognitive_face.large_person_group_person.list(
            large_person_group_id=group_id,
            top=top,
            start=start)

        image_ids.extend(person['name'] for person in people)

        if len(people) < top:
            break

        start = people[-1]['personId']
        num_pages += 1

    logger.debug('Got %d images from %d pages', len(image_ids), num_pages)
    return image_ids


def _fetch_faces_for_person(img_id: str) -> Tuple[List[str], Optional[str]]:
    db = get_database_manager()
    session = db.get_session()
    mapping = session.query(FaceApiMapping)\
        .filter(FaceApiMapping.img_id == img_id) \
        .first()
    session.close()

    if not mapping:
        logger.debug('No mapping found for image %s', img_id)
        return [], None

    # FIXME: manage deletion of the files
    img_path = storage.get_image_path(img_id)
    faces = cognitive_face.face.detect(img_path)
    face_ids = [face['faceId'] for face in faces]

    if not face_ids:
        logger.debug('No faces found for image %s', img_id)
        return [], mapping.person_id

    return face_ids, mapping.person_id


def _fetch_people_matching_faces(face_ids: List[str]) -> Dict[str, float]:
    group_id, _ = _get_group_id()
    matches = cognitive_face.face.identify(
        face_ids=face_ids,
        large_person_group_id=group_id)

    person_id_to_confidence = {}  # type: Dict[str, float]
    for match in matches:
        for candidate in match['candidates']:
            person_id = candidate['personId']
            new_confidence = candidate['confidence']
            old_confidence = person_id_to_confidence.get(person_id, -1)
            if new_confidence > old_confidence:
                person_id_to_confidence[person_id] = new_confidence

    return person_id_to_confidence


def _fetch_mappings_for_people(people: Iterable[str]) -> List[FaceApiMapping]:
    db = get_database_manager()
    session = db.get_session()
    mappings = session.query(FaceApiMapping) \
        .filter(FaceApiMapping.person_id.in_(people)) \
        .all()
    session.close()
    return mappings


def lookup_matching_images(img_id: str) -> Tuple[List[str], List[float]]:
    face_ids, person_id = _fetch_faces_for_person(img_id)
    if not face_ids:
        return [], []

    person_id_to_confidence = _fetch_people_matching_faces(face_ids)
    person_id_to_confidence.pop(person_id, None)  # exclude self-match
    if not person_id_to_confidence:
        return [], []

    mappings = _fetch_mappings_for_people(person_id_to_confidence.keys())
    if not mappings:
        return [], []

    images = []
    distances = []
    for mapping in mappings:
        confidence = person_id_to_confidence[mapping.person_id]
        distance = 1 - confidence
        images.append(mapping.img_id)
        distances.append(distance)

    logger.debug('Image %s has %d matches', img_id, len(distances))
    return images, distances
