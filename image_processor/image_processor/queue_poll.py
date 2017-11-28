from azure.storage.queue import QueueService
from time import sleep
import os

class QueuePoll:
    def __init__(self, queue_name):
        self.queue_service = QueueService(account_name=os.environ['STORAGE_ACCOUNT_NAME'],
                                          account_key=os.environ['STORAGE_ACCOUNT_KEY'])
        self.queue_name = queue_name
        self.queue_service.create_queue(self.queue_name)

    def _get_messages_from_queue(self):
        messages = []
        try:
            messages = self.queue_service.get_messages(self.queue_name)
            if messages:
                print("Successfully received messages from queue")
        except Exception as e:
            print(e)
        return messages
    
    def poll(self):
        print("Polling...")
        while True:
            for message in self._get_messages_from_queue():
                self.queue_service.delete_message(self.queue_name, message.id, message.pop_receipt)
                yield message
            sleep(3)

if __name__ == "__main__":
    queue_name = os.environ['IMAGE_PROCESSOR_QUEUE']
    p = QueuePoll(queue_name)
    num_pics_in_input_folder = 10
    for i in range(1, num_pics_in_input_folder+1):
        p.queue_service.put_message(queue_name, str(i))
    #for message in p.poll():
    #    print(message.content)
    #p.queue_service.delete_queue('task')
