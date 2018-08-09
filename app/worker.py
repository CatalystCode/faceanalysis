from faceanalysis.pipeline import celery
from faceanalysis.settings import IMAGE_PROCESSOR_QUEUE
from faceanalysis.settings import LOGGING_LEVEL

if __name__ == '__main__':
    celery.worker_main([
        '--queues={}'.format(IMAGE_PROCESSOR_QUEUE),
        '--loglevel={}'.format(LOGGING_LEVEL),
        '-Ofair',
        '--concurrency=1'])
