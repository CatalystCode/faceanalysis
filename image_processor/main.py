import os
from image_processor.models.database_manager import DatabaseManager
from image_processor.pipeline import Pipeline
from image_processor.queue_poll import QueuePoll

if __name__ == "__main__":
    db = DatabaseManager()
    db.create_all_tables()

    qp = QueuePoll(os.environ['IMAGE_PROCESSOR_QUEUE'])

    pipeline = Pipeline()
    pipeline.begin_pipeline()
    db.close_engine()
