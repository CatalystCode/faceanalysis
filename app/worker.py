from faceanalysis.models.database_manager import DatabaseManager
from faceanalysis.models.models import init_models
from faceanalysis.pipeline import Pipeline

if __name__ == "__main__":
    db = DatabaseManager()
    init_models(db.engine)
    pipeline = Pipeline()
    pipeline.begin_pipeline()
    db.close_engine()
