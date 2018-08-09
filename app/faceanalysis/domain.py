from faceanalysis import tasks
from faceanalysis.log import get_logger
from faceanalysis.models.database_manager import get_database_manager
from faceanalysis.models.image_status_enum import ImageStatusEnum
from faceanalysis.models.models import Image
from faceanalysis.models.models import ImageStatus
from faceanalysis.models.models import Match
from faceanalysis.storage import store_image

logger = get_logger(__name__)


class FaceAnalysisError(Exception):
    pass


class ImageDoesNotExist(FaceAnalysisError):
    pass


class ImageAlreadyProcessed(FaceAnalysisError):
    pass


class DuplicateImage(FaceAnalysisError):
    pass


def process_image(img_id):
    db = get_database_manager()
    session = db.get_session()
    img_status = session.query(ImageStatus)\
        .filter(ImageStatus.img_id == img_id)\
        .first()
    session.close()

    if img_status is None:
        raise ImageDoesNotExist()

    if img_status.status != ImageStatusEnum.uploaded.name:
        raise ImageAlreadyProcessed()

    tasks.process_image.delay(img_id)
    logger.debug('Image %s queued for processing', img_id)


def get_processing_status(img_id):
    db = get_database_manager()
    session = db.get_session()
    img_status = session.query(ImageStatus)\
        .filter(ImageStatus.img_id == img_id)\
        .first()
    session.close()

    if img_status is None:
        raise ImageDoesNotExist()

    logger.debug('Image %s is in status %s', img_id, img_status.status)
    return img_status.status, img_status.error_msg


def upload_image(stream, filename):
    img_id = filename[:filename.find('.')]
    db = get_database_manager()
    session = db.get_session()
    prev_img_upload = session.query(ImageStatus)\
        .filter(ImageStatus.img_id == img_id)\
        .first()
    session.close()

    if prev_img_upload is not None:
        raise DuplicateImage()

    store_image(stream, filename)
    img_status = ImageStatus(img_id=img_id,
                             status=ImageStatusEnum.uploaded.name,
                             error_msg=None)
    session = db.get_session()
    session.add(img_status)
    db.safe_commit(session)
    logger.debug('Image %s uploaded', img_id)


def list_images():
    db = get_database_manager()
    session = db.get_session()
    query = session.query(Image)\
        .all()
    image_ids = [image.img_id for image in query]
    session.close()

    logger.debug('Got %d images overall', len(image_ids))
    return image_ids


def lookup_matching_images(img_id):
    db = get_database_manager()
    session = db.get_session()
    query = session.query(Match)\
        .filter(Match.this_img_id == img_id)\
        .all()
    session.close()

    images = []
    distances = []
    for match in query:
        images.append(match.that_img_id)
        distances.append(match.distance_score)

    logger.debug('Image %s has %d matches', img_id, len(distances))
    return images, distances
