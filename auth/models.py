from sqlalchemy import Column, Date, DateTime, Integer, String, Enum, ForeignKey, Table, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..s3_database import Base
from .enums import Gender, FriendshipStatus

# Friendship association table
friendship = Table(
    "friendships",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("friend_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("status", Enum(FriendshipStatus), default=FriendshipStatus.PENDING),
    Column("created_at", DateTime, default=datetime.utcnow),
)


class User(Base):
    __tablename__ = "users"

    # basic details
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    name = Column(String)
    cognito_id = Column(String, unique=True)  # Stores AWS Cognito user ID
    created_dt = Column(DateTime, default=datetime.utcnow())

    # profile
    dob = Column(Date)
    gender = Column(Enum(Gender))
    profile_pic = Column(String)  # link to S3 for profile picture
    bio = Column(String)
    location = Column(String)

    # relationships
    friends = relationship(
        "User",
        secondary=friendship,
        primaryjoin=(id == friendship.c.user_id),
        secondaryjoin=(id == friendship.c.friend_id),
        backref="friended_by"
    )

    # team relationships
    teams_member = relationship("Team", secondary="team_members", back_populates="members")
    teams_leader = relationship("Team", back_populates="leader")

    # venue relationships
    venues_liked = relationship("Venue", secondary="venue_likes", back_populates="liked_by")
    venues_owned = relationship("Venue", back_populates="owner")

    # stats
    friends_count = Column(Integer, default=0)
    teams_count = Column(Integer, default=0)