from image_processor.models.database_manager import DatabaseManager
from image_processor.models.models import init_models
from image_processor.pipeline import Pipeline

if __name__ == "__main__":
    db = DatabaseManager()
    init_models(db.engine)
    pipeline = Pipeline()
    pipeline.begin_pipeline()
    db.close_engine()
