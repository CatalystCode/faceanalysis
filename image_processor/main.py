import os
from image_processor.models.database_manager import DatabaseManager
from image_processor.models.models import init_models
from image_processor.pipeline import Pipeline
from image_processor.queue_poll import QueuePoll

if __name__ == "__main__":
    db = DatabaseManager()
    init_models(db.engine)

    qp = QueuePoll(os.environ['IMAGE_PROCESSOR_QUEUE'])

    pipeline = Pipeline()
    pipeline.begin_pipeline()
    db.close_engine()
