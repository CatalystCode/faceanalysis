from faceanalysis.settings import IMAGE_PROCESSOR_CONCURRENCY
from faceanalysis.settings import IMAGE_PROCESSOR_QUEUE
from faceanalysis.settings import LOGGING_LEVEL
from faceanalysis.tasks import celery

if __name__ == '__main__':
    celery.worker_main([
        '--queues={}'.format(IMAGE_PROCESSOR_QUEUE),
        '--concurrency={}'.format(IMAGE_PROCESSOR_CONCURRENCY),
        '--loglevel={}'.format(LOGGING_LEVEL),
        '-Ofair',
    ])
