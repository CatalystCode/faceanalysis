# pylint: disable=too-few-public-methods

from time import sleep
from azure.storage.queue import QueueService
from .log import get_logger
from .settings import STORAGE_ACCOUNT_KEY, STORAGE_ACCOUNT_NAME

logger = get_logger(__name__)


def create_queue_service(queue_name):
    queue_service = QueueService(
        account_name=STORAGE_ACCOUNT_NAME,
        account_key=STORAGE_ACCOUNT_KEY)
    logger.debug('Creating queue %s', queue_name)
    queue_service.create_queue(queue_name)
    return queue_service


class QueuePoll:
    def __init__(self, queue_name):
        self.queue_service = create_queue_service(queue_name)
        self.queue_name = queue_name

    # pylint: disable=broad-except
    def _get_messages_from_queue(self):
        messages = []
        try:
            messages = self.queue_service.get_messages(self.queue_name)
            if messages:
                logger.debug('Got %d messages from queue', len(messages))
        except Exception:
            logger.exception('Unable to fetch messages from queue')
        return messages

    def poll(self):
        logger.debug('Starting polling')
        while True:
            for message in self._get_messages_from_queue():
                self.queue_service.delete_message(
                    self.queue_name, message.id, message.pop_receipt)
                yield message
            sleep(3)

# pylint: enable=too-few-public-methods
