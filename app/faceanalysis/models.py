from contextlib import contextmanager
from enum import Enum
from enum import auto
from functools import lru_cache

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func

from faceanalysis.log import get_logger
from faceanalysis.settings import SQLALCHEMY_CONNECTION_STRING

logger = get_logger(__name__)
Base = declarative_base()


# pylint: disable=too-few-public-methods
class User(Base):  # type: ignore
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, index=True)
    password_hash = Column(String(128))


class ImageStatus(Base):  # type: ignore
    __tablename__ = 'imagestatuses'

    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), unique=True)
    status = Column(String(50))
    error_msg = Column(String(50), default=None)


class Image(Base):  # type: ignore
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), unique=True)
    feature_mappings = relationship('FeatureMapping', back_populates='img')
    time_created = Column(DateTime(timezone=True), server_default=func.now())


class FeatureMapping(Base):  # type: ignore
    __tablename__ = 'featuremappings'

    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), ForeignKey('images.img_id'))
    features = Column(Text)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    img = relationship('Image', back_populates='feature_mappings')


class Match(Base):  # type: ignore
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    this_img_id = Column(String(50), ForeignKey('images.img_id'))
    that_img_id = Column(String(50), ForeignKey('images.img_id'))
    distance_score = Column(Float)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    this_img = relationship('Image', foreign_keys=[this_img_id])
    that_img = relationship('Image', foreign_keys=[that_img_id])
    __table_args__ = (UniqueConstraint(
        'this_img_id', 'that_img_id', name='_this_that_uc'),)


class FaceApiMapping(Base):  # type: ignore
    __tablename__ = 'faceapimappings'

    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), index=True, unique=True)
    face_id = Column(String(50), index=True, unique=True)
# pylint: enable=too-few-public-methods


class ImageStatusEnum(Enum):
    finished_processing = auto()
    processing = auto()
    uploaded = auto()
    face_vector_computed = auto()


@lru_cache(maxsize=1)
def _connect():
    engine = create_engine(SQLALCHEMY_CONNECTION_STRING, pool_recycle=3600)
    session_factory = sessionmaker(bind=engine)
    return engine, session_factory


def init_models():
    engine, _ = _connect()
    Base.metadata.create_all(engine)


def delete_models():
    engine, _ = _connect()
    Base.metadata.drop_all(engine)


# pylint: disable=broad-except
@contextmanager
def get_db_session(commit=False) -> Session:
    _, session_factory = _connect()
    session = session_factory()
    try:
        yield session
    except Exception:
        logger.exception('Error during session, rolling back')
        session.rollback()
    else:
        if commit:
            try:
                session.commit()
            except SQLAlchemyError:
                logger.exception('Error during session commit, rolling back')
                session.rollback()
            else:
                logger.debug('Session committed successfully')
    finally:
        session.close()
# pylint: enable=broad-except
