# pylint: disable=too-few-public-methods

from time import sleep
from azure.storage.queue import QueueService
from .log import get_logger
from .settings import STORAGE_ACCOUNT_KEY, STORAGE_ACCOUNT_NAME


class QueuePoll:
    def __init__(self, queue_name):
        self.logger = get_logger(__name__)
        self.queue_service = QueueService(
            account_name=STORAGE_ACCOUNT_NAME,
            account_key=STORAGE_ACCOUNT_KEY)
        self.queue_name = queue_name
        self.logger.debug('Creating queue %s', queue_name)
        self.queue_service.create_queue(self.queue_name)

    # pylint: disable=broad-except
    def _get_messages_from_queue(self):
        messages = []
        try:
            messages = self.queue_service.get_messages(self.queue_name)
            if messages:
                self.logger.debug("Successfully received messages from queue")
        except Exception as e:
            self.logger.error(e, exc_info=True)
        return messages

    def poll(self):
        self.logger.debug("Polling...")
        while True:
            for message in self._get_messages_from_queue():
                self.queue_service.delete_message(
                    self.queue_name, message.id, message.pop_receipt)
                yield message
            sleep(3)

# pylint: enable=too-few-public-methods
