from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
class FaceImage(Base):
    __tablename__ = 'faceimages'
    
    id = Column(Integer, primary_key=True)
    original_img_id = Column(String(50))
    cropped_img_id = Column(String(50), unique=True)

class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    cropped_img_id_1 = Column(String(50))
    cropped_img_id_2 = Column(String(50))
    distance_score = Column(Float)

class Feature(Base):
    __tablename__ = 'features'
    
    id = Column(Integer, primary_key=True)
    cropped_img_id = Column(String(50))
    features = Column(Text)

class PendingFaceImage(Base):
    __tablename__ = 'pendingfaceimages'

    id = Column(Integer, primary_key=True)
    original_img_id = Column(String(50))
