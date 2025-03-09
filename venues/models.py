from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Table, Boolean, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from ..s3_database import Base
from .enums import VenueType, VenueStatus

# Venue like association table
venue_likes = Table(
    "venue_likes",
    Base.metadata,
    Column("venue_id", Integer, ForeignKey("venues.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow),
)


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    venue_type = Column(String, default=VenueType.SPORTS_FACILITY)
    status = Column(String, default=VenueStatus.ACTIVE)

    # Location info
    address = Column(String)
    city = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)

    # Owner info
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="venues_owned")

    # Business info
    contact_email = Column(String)
    contact_phone = Column(String)
    business_hours = Column(String)  # Could be JSON string
    price_per_hour = Column(Float)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    liked_by = relationship("User", secondary=venue_likes, back_populates="venues_liked")
    photos = relationship("VenuePhoto", back_populates="venue")
    reviews = relationship("VenueReview", back_populates="venue")
    bookings = relationship("Booking", back_populates="venue")
    activities = relationship("Activity", back_populates="venue")


class VenuePhoto(Base):
    __tablename__ = "venue_photos"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    photo_url = Column(String, nullable=False)
    caption = Column(String)
    is_primary = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    venue = relationship("Venue", back_populates="photos")


class VenueReview(Base):
    __tablename__ = "venue_reviews"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rating = Column(Integer)  # 1-5 stars
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    venue = relationship("Venue", back_populates="reviews")
    user = relationship("User")