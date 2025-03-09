from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Table, Boolean, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base
from .enums import TeamStatus, ActivityType, BookingStatus

# Team members association table
team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("joined_at", DateTime, default=datetime.utcnow),
    Column("is_active", Boolean, default=True),
)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default=TeamStatus.ACTIVE)
    team_photo = Column(String)  # S3 link

    # Max team size (2-10 as mentioned in requirements)
    max_members = Column(Integer, default=10)

    # Team leader
    leader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leader = relationship("User", back_populates="teams_leader", foreign_keys=[leader_id])

    # Team members
    members = relationship("User", secondary=team_members, back_populates="teams_member")

    # Team bookings
    bookings = relationship("Booking", back_populates="team")

    # Activity history
    activities = relationship("Activity", back_populates="team")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(String, default=BookingStatus.PENDING)
    total_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    venue = relationship("Venue", back_populates="bookings")
    team = relationship("Team", back_populates="bookings")

    # Payment tracking
    payment_id = Column(String)  # Payment reference
    is_paid = Column(Boolean, default=False)


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=True)
    activity_type = Column(String, default=ActivityType.SPORT)
    description = Column(Text)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="activities")
    venue = relationship("Venue", back_populates="activities")
    photos = relationship("ActivityPhoto", back_populates="activity")


class ActivityPhoto(Base):
    __tablename__ = "activity_photos"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    photo_url = Column(String, nullable=False)  # S3 link
    caption = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    activity = relationship("Activity", back_populates="photos")
    user = relationship("User")