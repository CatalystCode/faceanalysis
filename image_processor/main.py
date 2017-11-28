import os
from image_processor.models.database_manager import DatabaseManager
from image_processor.pipeline import Pipeline
from image_processor.queue_poll import QueuePoll

if __name__ == "__main__":
    db = DatabaseManager()
    db.create_all_tables()

    qp = QueuePoll(os.environ['IMAGE_PROCESSOR_QUEUE'])
    NUM_INPUT_PICS = 10
    for i in range(1, NUM_INPUT_PICS+1):
        qp.queue_service.put_message(os.environ['IMAGE_PROCESSOR_QUEUE'], str(i))

    pipeline = Pipeline()
    pipeline.begin_pipeline()
    db.close_engine()
