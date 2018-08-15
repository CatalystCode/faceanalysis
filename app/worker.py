from faceanalysis.log import get_logger
from faceanalysis.settings import FACE_VECTORIZE_ALGORITHM
from faceanalysis.settings import IMAGE_PROCESSOR_CONCURRENCY
from faceanalysis.settings import IMAGE_PROCESSOR_QUEUE
from faceanalysis.settings import LOGGING_LEVEL
from faceanalysis.tasks import celery

logger = get_logger(__name__)


def _main():
    if FACE_VECTORIZE_ALGORITHM == 'FaceApi':
        logger.warning('FaceApi backend detected: not starting Celery worker')
        return

    celery.worker_main([
        '--queues={}'.format(IMAGE_PROCESSOR_QUEUE),
        '--concurrency={}'.format(IMAGE_PROCESSOR_CONCURRENCY),
        '--loglevel={}'.format(LOGGING_LEVEL),
        '-Ofair',
    ])


if __name__ == '__main__':
    _main()
