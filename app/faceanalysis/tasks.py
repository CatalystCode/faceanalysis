from celery import Celery

from faceanalysis import face_matcher
from faceanalysis.settings import CELERY_BROKER
from faceanalysis.settings import IMAGE_PROCESSOR_QUEUE


celery = Celery('pipeline', broker=CELERY_BROKER)
celery.conf.task_default_queue = IMAGE_PROCESSOR_QUEUE


@celery.task(ignore_result=True)
def process_image(img_id):
    face_matcher.process_image(img_id)
