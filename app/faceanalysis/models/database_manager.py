from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from faceanalysis.log import get_logger
from faceanalysis.settings import SQLALCHEMY_CONNECTION_STRING


class DatabaseManager:
    def __init__(self):
        self.engine = create_engine(SQLALCHEMY_CONNECTION_STRING,
                                    pool_recycle=3600)

        self.session_factory = sessionmaker(bind=self.engine)
        self.logger = get_logger(__name__)

    def get_session(self):
        return self.session_factory()

    def safe_commit(self, session):
        try:
            session.commit()
            self.logger.debug("session committed")
        except SQLAlchemyError:
            session.rollback()
            self.logger.debug("session rolled back")
        finally:
            session.close()
            self.logger.debug("session closed")

    def close_engine(self):
        self.logger.debug("engine closed")
        self.engine.dispose()


@lru_cache(maxsize=1)
def get_database_manager():
    return DatabaseManager()
