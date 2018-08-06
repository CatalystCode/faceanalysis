from api.models.database_manager import DatabaseManager
from api.models.models import init_models
from api.pipeline import Pipeline

if __name__ == "__main__":
    db = DatabaseManager()
    init_models(db.engine)
    pipeline = Pipeline()
    pipeline.begin_pipeline()
    db.close_engine()
