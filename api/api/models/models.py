from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, UniqueConstraint
from sqlalchemy.schema import ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class OriginalImage(Base):
    __tablename__ = 'originalimages'
    
    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), unique=True)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    cropped_imgs = relationship('CroppedImage', back_populates='original_img')

class CroppedImage(Base):
    __tablename__ = 'croppedimages'
    
    id = Column(Integer, primary_key=True)
    img_id = Column(String(50), unique=True)
    original_img_id = Column(String(50), ForeignKey('originalimages.img_id'))
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    original_img = relationship('OriginalImage', back_populates='cropped_imgs')
    feature_mappings = relationship('FeatureMapping', back_populates='cropped_img')

class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    this_cropped_img_id = Column(String(50), ForeignKey('croppedimages.img_id'))
    that_cropped_img_id = Column(String(50), ForeignKey('croppedimages.img_id'))
    distance_score = Column(Float)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
    this_cropped_img = relationship('CroppedImage', foreign_keys=[this_cropped_img_id])
    that_cropped_img = relationship('CroppedImage', foreign_keys=[that_cropped_img_id])
    __table_args__ = (UniqueConstraint('this_cropped_img_id', 'that_cropped_img_id', name='_this_that_uc'),)

class FeatureMapping(Base):
    __tablename__ = 'featuremappings'
    
    id = Column(Integer, primary_key=True)
    cropped_img_id = Column(String(50), ForeignKey('croppedimages.img_id'), unique=True)
    features = Column(Text)
    time_created = Column(DateTime(timezone=True), server_default=func.now())
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
