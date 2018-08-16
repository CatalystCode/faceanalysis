from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey
from sqlalchemy.sql import func

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


def init_models(database_engine):
    try:
        Base.metadata.create_all(database_engine)
    except ProgrammingError:
        pass


def delete_models(database_engine):
    Base.metadata.drop_all(database_engine)
