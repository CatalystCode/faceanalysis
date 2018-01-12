from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, String, Float, Text, Integer, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.schema import ForeignKey
from .database_manager import DatabaseManager
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
import os
import datetime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
   
    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, index=True)
    password_hash = Column(String(128))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration=int(os.environ['DEFAULT_TOKEN_EXPIRATION_SECS'])):
        s = Serializer(os.environ['TOKEN_SECRET_KEY'], expires_in=expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(os.environ['TOKEN_SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        session = DatabaseManager().get_session()
        user = session.query(User).filter(User.id == data['id']).first()
        session.close()
        return user

class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), unique=True)
    feature_mappings = relationship('FeatureMapping', back_populates='img')
    time_created = Column(DateTime(timezone=True), server_default=func.now())

class FeatureMapping(Base):
    __tablename__ = 'featuremappings'
    
    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), ForeignKey('images.img_id'))
    features = Column(Text)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    img = relationship('Image', back_populates='feature_mappings')

class Match(Base):
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True)
    this_img_id = Column(String(50), ForeignKey('images.img_id'))
    that_img_id = Column(String(50), ForeignKey('images.img_id'))
    distance_score = Column(Float)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    this_img = relationship('Image', foreign_keys=[this_img_id])
    that_img = relationship('Image', foreign_keys=[that_img_id])
    __table_args__ = (UniqueConstraint('this_img_id', 'that_img_id', name='_this_that_uc'),)

def init_models(database_engine):
    Base.metadata.create_all(database_engine)
