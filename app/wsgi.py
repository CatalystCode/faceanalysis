from faceanalysis.api import app as application
from faceanalysis.models.database_manager import get_database_manager
from faceanalysis.models.models import init_models


def _main():
    db = get_database_manager()
    init_models(db.engine)
    application.run()


if __name__ == '__main__':
    _main()
