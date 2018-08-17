from typing import IO
from typing import List
from typing import Tuple

from faceanalysis import tasks
from faceanalysis.domain.errors import DuplicateImage
from faceanalysis.domain.errors import ImageAlreadyProcessed
from faceanalysis.domain.errors import ImageDoesNotExist
from faceanalysis.log import get_logger
from faceanalysis.models import Image
from faceanalysis.models import ImageStatus
from faceanalysis.models import ImageStatusEnum
from faceanalysis.models import Match
from faceanalysis.models import get_db_session
from faceanalysis.storage import store_image

logger = get_logger(__name__)


def process_image(img_id: str):
    with get_db_session() as session:
        img_status = session.query(ImageStatus) \
            .filter(ImageStatus.img_id == img_id) \
            .first()

    if img_status is None:
        raise ImageDoesNotExist()

    if img_status.status != ImageStatusEnum.uploaded.name:
        raise ImageAlreadyProcessed()

    tasks.process_image.delay(img_id)
    logger.debug('Image %s queued for processing', img_id)


def get_processing_status(img_id: str) -> Tuple[str, str]:
    with get_db_session() as session:
        img_status = session.query(ImageStatus) \
            .filter(ImageStatus.img_id == img_id) \
            .first()

    if img_status is None:
        raise ImageDoesNotExist()

    logger.debug('Image %s is in status %s', img_id, img_status.status)
    return img_status.status, img_status.error_msg


def upload_image(stream: IO[bytes], filename: str) -> str:
    img_id = filename[:filename.find('.')]

    with get_db_session() as session:
        prev_img_upload = session.query(ImageStatus) \
            .filter(ImageStatus.img_id == img_id) \
            .first()

    if prev_img_upload is not None:
        raise DuplicateImage()

    store_image(stream, filename)
    img_status = ImageStatus(img_id=img_id,
                             status=ImageStatusEnum.uploaded.name,
                             error_msg=None)

    with get_db_session(commit=True) as session:
        session.add(img_status)

    logger.debug('Image %s uploaded', img_id)
    return img_id


def list_images() -> List[str]:
    with get_db_session() as session:
        image_ids = [image.img_id for image in session.query(Image).all()]

    logger.debug('Got %d images overall', len(image_ids))
    return image_ids


def lookup_matching_images(img_id: str) -> Tuple[List[str], List[float]]:
    with get_db_session() as session:
        matches = session.query(Match) \
            .filter(Match.this_img_id == img_id) \
            .all()

    images = []
    distances = []
    for match in matches:
        images.append(match.that_img_id)
        distances.append(match.distance_score)

    logger.debug('Image %s has %d matches', img_id, len(distances))
    return images, distances
