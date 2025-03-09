from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

from .enums import TeamStatus, ActivityType, BookingStatus


class TeamBase(BaseModel):
    name: str
    description: Optional[str] = None
    max_members: Optional[int] = 10


class TeamCreate(TeamBase):
    pass


class TeamUpdate(TeamBase):
    status: Optional[TeamStatus] = None
    team_photo: Optional[str] = None


class TeamMember(BaseModel):
    user_id: int
    username: str
    name: Optional[str] = None
    profile_pic: Optional[str] = None
    joined_at: datetime


class Team(TeamBase):
    id: int
    leader_id: int
    created_at: datetime
    status: TeamStatus
    team_photo: Optional[str] = None

    class Config:
        orm_mode = True


class TeamDetail(Team):
    leader: dict
    members: List[TeamMember] = []
    members_count: int


class BookingBase(BaseModel):
    venue_id: int
    team_id: int
    start_time: datetime
    end_time: datetime


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    status: Optional[BookingStatus] = None
    total_cost: Optional[float] = None
    is_paid: Optional[bool] = None


class Booking(BookingBase):
    id: int
    status: BookingStatus
    total_cost: Optional[float] = None
    created_at: datetime
    is_paid: bool

    class Config:
        orm_mode = True


class BookingDetail(Booking):
    venue: dict
    team: dict


class ActivityBase(BaseModel):
    team_id: int
    venue_id: Optional[int] = None
    activity_type: ActivityType
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    venue_id: Optional[int] = None
    activity_type: Optional[ActivityType] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class Activity(ActivityBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class PhotoBase(BaseModel):
    activity_id: int
    caption: Optional[str] = None


class PhotoCreate(PhotoBase):
    pass


class PhotoUpdate(BaseModel):
    caption: Optional[str] = None


class ActivityPhoto(PhotoBase):
    id: int
    user_id: int
    photo_url: str
    uploaded_at: datetime

    class Config:
        orm_mode = True


class ActivityDetail(Activity):
    team: dict
    venue: Optional[dict] = None
    photos: List[ActivityPhoto] = []