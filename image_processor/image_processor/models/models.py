from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, String, Float, Text, Integer
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
    username = Column(String(32), index=True)
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

    img_id = Column(String(50), primary_key=True)
    cropped_imgs = relationship('CroppedImage', back_populates='original_img')

class CroppedImage(Base):
    __tablename__ = 'croppedimages'
    
    img_id = Column(String(50), primary_key=True)
    original_img_id = Column(String(50), ForeignKey('originalimages.img_id'))
    
    original_img = relationship('OriginalImage', back_populates='cropped_imgs')
    feature_mappings = relationship('FeatureMapping', back_populates='cropped_img')

class Match(Base):
    __tablename__ = 'matches'

    this_cropped_img_id = Column(String(50), ForeignKey('croppedimages.img_id'), primary_key=True)
    that_cropped_img_id = Column(String(50), ForeignKey('croppedimages.img_id'), primary_key=True)
    distance_score = Column(Float)

    this_cropped_img = relationship('CroppedImage', foreign_keys=[this_cropped_img_id])
    that_cropped_img = relationship('CroppedImage', foreign_keys=[that_cropped_img_id])


class FeatureMapping(Base):
    __tablename__ = 'featuremappings'
    
    cropped_img_id = Column(String(50), ForeignKey('croppedimages.img_id'), primary_key=True)
    features = Column(Text)

    cropped_img = relationship('CroppedImage', back_populates='feature_mappings')

if __name__ == '__main__':
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    session = Session()
    original_img1 = OriginalImage(img_id='100')
    original_img2 = OriginalImage(img_id='200')
    this_cropped_img = CroppedImage(img_id='1', original_img_id='100')
    that_cropped_img = CroppedImage(img_id='2', original_img_id='200')
    match = Match(this_cropped_img_id='1', that_cropped_img_id='2')
    fm = FeatureMapping(cropped_img_id='1')
    session.add_all([original_img1, original_img2, this_cropped_img, that_cropped_img, match, fm])
    session.commit()
    session.close()

    session = Session()
    cropped_imgs = session.query(OriginalImage).first().cropped_imgs
    print(cropped_imgs[0].original_img_id)
    session.close()

    session = Session()
    query = session.query(Match).filter(Match.this_cropped_img_id == '1').all()
    print(query[0].that_cropped_img.original_img.img_id)
    session.close()

    session = Session()
    query = session.query(OriginalImage).filter(OriginalImage.img_id == '200').first()
    imgs = list(set([cropped_img.img_id for cropped_img in query.cropped_imgs]))
    print(imgs)
