"""
SQLAlchemy ORM models for TrailService
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Country(Base):
    __tablename__ = 'Country'
    __table_args__ = {'schema': 'CW2'}
    
    CountryID = Column(Integer, primary_key=True)
    CountryName = Column(String(100), nullable=False, unique=True)
    
    cities = relationship("City", back_populates="country")
    locations = relationship("Location", back_populates="country")

class City(Base):
    __tablename__ = 'City'
    __table_args__ = {'schema': 'CW2'}
    
    CityID = Column(Integer, primary_key=True)
    CityName = Column(String(100), nullable=False)
    CountryID = Column(Integer, ForeignKey('CW2.Country.CountryID'), nullable=False)
    
    country = relationship("Country", back_populates="cities")
    locations = relationship("Location", back_populates="city")

class Location(Base):
    __tablename__ = 'Location'
    __table_args__ = {'schema': 'CW2'}
    
    LocationID = Column(Integer, primary_key=True)
    LocationName = Column(String(255), nullable=False)
    CityID = Column(Integer, ForeignKey('CW2.City.CityID'))
    CountryID = Column(Integer, ForeignKey('CW2.Country.CountryID'))
    Coordinates = Column(String(100))
    
    city = relationship("City", back_populates="locations")
    country = relationship("Country", back_populates="locations")
    trails = relationship("Trail", back_populates="location")

class User(Base):
    __tablename__ = 'User'
    __table_args__ = {'schema': 'CW2'}
    
    UserID = Column(Integer, primary_key=True)
    Username = Column(String(50), nullable=False)
    Email = Column(String(100), nullable=False, unique=True)
    Role = Column(String(20), default='user')
    CreatedAt = Column(DateTime, default=datetime.now)
    LastLogin = Column(DateTime)
    
    trails = relationship("Trail", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    photos = relationship("Photo", back_populates="user")

class Trail(Base):
    __tablename__ = 'Trail'
    __table_args__ = {'schema': 'CW2'}
    
    TrailID = Column(Integer, primary_key=True)
    TrailName = Column(String(100), nullable=False)
    LocationID = Column(Integer, ForeignKey('CW2.Location.LocationID'))
    Difficulty = Column(String(20), nullable=False)
    Length = Column(Float, nullable=False)
    ElevationGain = Column(Integer)
    EstTimeMin = Column(Integer, nullable=False)
    EstTimeMax = Column(Integer, nullable=False)
    RouteType = Column(String(20), nullable=False)
    Description = Column(Text)
    UserID = Column(Integer, ForeignKey('CW2.User.UserID'), nullable=False)
    IsPublic = Column(Boolean, default=True)
    CreatedAt = Column(DateTime, default=datetime.now)
    UpdatedAt = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    location = relationship("Location", back_populates="trails")
    user = relationship("User", back_populates="trails")
    points = relationship("TrailPoint", back_populates="trail", cascade="all, delete-orphan")
    features = relationship("Feature", secondary="CW2.Trail_Feature", back_populates="trails")
    reviews = relationship("Review", back_populates="trail")
    photos = relationship("Photo", back_populates="trail")

class TrailPoint(Base):
    __tablename__ = 'Trail_Point'
    __table_args__ = {'schema': 'CW2'}
    
    PointID = Column(Integer, primary_key=True)
    TrailID = Column(Integer, ForeignKey('CW2.Trail.TrailID'), nullable=False)
    PointOrder = Column(Integer, nullable=False)
    Latitude = Column(Float, nullable=False)
    Longitude = Column(Float, nullable=False)
    Description = Column(String(255))
    Elevation = Column(Float)
    CreatedAt = Column(DateTime, default=datetime.now)
    
    trail = relationship("Trail", back_populates="points")

class Feature(Base):
    __tablename__ = 'Feature'
    __table_args__ = {'schema': 'CW2'}
    
    FeatureID = Column(Integer, primary_key=True)
    FeatureName = Column(String(50), nullable=False, unique=True)
    Description = Column(String(255))
    IconURL = Column(String(500))
    
    trails = relationship("Trail", secondary="CW2.Trail_Feature", back_populates="features")

class TrailFeature(Base):
    __tablename__ = 'Trail_Feature'
    __table_args__ = {'schema': 'CW2'}
    
    TrailID = Column(Integer, ForeignKey('CW2.Trail.TrailID'), primary_key=True)
    FeatureID = Column(Integer, ForeignKey('CW2.Feature.FeatureID'), primary_key=True)
    AddedBy = Column(Integer, ForeignKey('CW2.User.UserID'))
    AddedAt = Column(DateTime, default=datetime.now)

class Review(Base):
    __tablename__ = 'Review'
    __table_args__ = {'schema': 'CW2'}
    
    ReviewID = Column(Integer, primary_key=True)
    TrailID = Column(Integer, ForeignKey('CW2.Trail.TrailID'), nullable=False)
    UserID = Column(Integer, ForeignKey('CW2.User.UserID'), nullable=False)
    Rating = Column(Integer, nullable=False)
    ReviewText = Column(Text)
    DateReviewed = Column(DateTime, default=datetime.now)
    IsHelpful = Column(Integer, default=0)
    
    trail = relationship("Trail", back_populates="reviews")
    user = relationship("User", back_populates="reviews")

class Photo(Base):
    __tablename__ = 'Photo'
    __table_args__ = {'schema': 'CW2'}
    
    PhotoID = Column(Integer, primary_key=True)
    TrailID = Column(Integer, ForeignKey('CW2.Trail.TrailID'), nullable=False)
    UserID = Column(Integer, ForeignKey('CW2.User.UserID'), nullable=False)
    PhotoURL = Column(String(500), nullable=False)
    Caption = Column(String(255))
    DateUploaded = Column(DateTime, default=datetime.now)
    IsApproved = Column(Boolean, default=True)
    
    trail = relationship("Trail", back_populates="photos")
    user = relationship("User", back_populates="photos")

class TrailLog(Base):
    __tablename__ = 'Trail_Log'
    __table_args__ = {'schema': 'CW2'}
    
    LogID = Column(Integer, primary_key=True)
    TrailID = Column(Integer, ForeignKey('CW2.Trail.TrailID'), nullable=False)
    UserID = Column(Integer, ForeignKey('CW2.User.UserID'), nullable=False)
    Action = Column(String(20), nullable=False)
    ActionDate = Column(DateTime, default=datetime.now)
    Details = Column(String(500))
    IPAddress = Column(String(45))

def init_database(engine):
    """Initialize database with all tables"""
    Base.metadata.create_all(bind=engine)