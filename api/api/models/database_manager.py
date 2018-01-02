import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from ..log import get_logger
from sqlalchemy.ext.declarative import declarative_base

def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance

@singleton
class DatabaseManager:
    def __init__(self):
        #self.engine = create_engine("sqlite:///test.db", echo=True)
        self.base = declarative_base()
        mysql_user = os.environ['MYSQL_USER']
        mysql_password = os.environ['MYSQL_PASSWORD']
        mysql_container_name = os.environ['MYSQL_CONTAINER_NAME']
        mysql_database = os.environ['MYSQL_DATABASE']
        mysql_connector_str = 'mysql+mysqlconnector'
        mysql_port = '3306'
        engine_credential_str = "{}://{}:{}@{}:{}/{}".format(mysql_connector_str,
                                                             mysql_user,
                                                             mysql_password,
                                                             mysql_container_name,
                                                             mysql_port,
                                                             mysql_database)
        self.engine = create_engine(engine_credential_str,
                                    pool_recycle=3600,
                                    echo=True)
        self.Session = sessionmaker(bind=self.engine)
        self.logger = get_logger(__name__,
                                 'api.log',
                                 os.environ['LOGGING_LEVEL'])

    def create_all_tables(self):
        self.base.metadata.create_all(self.engine)

    def get_base(self):
        return self.base

    def get_session(self):
        return self.Session()

    def safe_commit(self, session):
        try:
            session.commit()
            self.logger.debug("session committed")
        except:
            session.rollback()
            self.logger.debug("session rolled back")
        finally:
            session.close()
            self.logger.debug("session closed")

    def close_engine(self):
        self.logger.debug("engine closed")
        self.engine.dispose()
