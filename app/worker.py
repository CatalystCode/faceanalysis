from faceanalysis.models.database_manager import get_database_manager
from faceanalysis.models.models import init_models
from faceanalysis.pipeline import begin_pipeline

if __name__ == "__main__":
    db = get_database_manager()
    init_models(db.engine)
    begin_pipeline()
    db.close_engine()
