from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine, Column, String, Float, Text, Integer, UniqueConstraint
from sqlalchemy.schema import ForeignKey
from .database_manager import DatabaseManager
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
import os

Base = DatabaseManager().get_base()
SECRET_KEY = os.environ['FLASK_SECRET_KEY']

class User(Base):
    __tablename__ = 'users'
   
    id = Column(Integer, primary_key=True)
    username = Column(String(32), unique=True, index=True)
    password_hash = Column(String(128))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def generate_auth_token(self, expiration = 600):
        s = Serializer(SECRET_KEY, expires_in = expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(SECRET_KEY)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        session = DatabaseManager().get_session()
        user = session.query(User).filter(User.id == data['id']).first()
        session.close()
        return user

class OriginalImage(Base):
    __tablename__ = 'originalimages'

    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), unique=True)
    feature_mappings = relationship('FeatureMapping', back_populates='original_img')

class FeatureMapping(Base):
    __tablename__ = 'featuremappings'
    
    id = Column(Integer, primary_key=True)
    original_img_id = Column(String(50), ForeignKey('originalimages.img_id'))
    features = Column(Text)
    original_img = relationship('OriginalImage', back_populates='feature_mappings')

class Match(Base):
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True)
    this_original_img_id = Column(String(50), ForeignKey('originalimages.img_id'))
    that_original_img_id = Column(String(50), ForeignKey('originalimages.img_id'))
    distance_score = Column(Float)

    this_original_img = relationship('OriginalImage', foreign_keys=[this_original_img_id])
    that_original_img = relationship('OriginalImage', foreign_keys=[that_original_img_id])
    __table_args__ = (UniqueConstraint('this_original_img_id', 'that_original_img_id', name='_this_that_uc'),)

