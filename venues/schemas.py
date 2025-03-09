from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, Dict, Any

from .enums import VenueType, VenueStatus


class VenueBase(BaseModel):
    name: str
    description: Optional[str] = None
    venue_type: VenueType
    address: str
    city: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    business_hours: Optional[str] = None
    price_per_hour: Optional[float] = None


class VenueCreate(VenueBase):
    pass


class VenueUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    venue_type: Optional[VenueType] = None
    status: Optional[VenueStatus] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    business_hours: Optional[str] = None
    price_per_hour: Optional[float] = None


class Venue(VenueBase):
    id: int
    owner_id: int
    status: VenueStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class VenuePhotoBase(BaseModel):
    venue_id: int
    caption: Optional[str] = None
    is_primary: Optional[bool] = False


class VenuePhotoCreate(VenuePhotoBase):
    pass


class VenuePhotoUpdate(BaseModel):
    caption: Optional[str] = None
    is_primary: Optional[bool] = None


class VenuePhoto(VenuePhotoBase):
    id: int
    photo_url: str
    uploaded_at: datetime

    class Config:
        orm_mode = True


class VenueReviewBase(BaseModel):
    venue_id: int
    rating: int
    comment: Optional[str] = None


class VenueReviewCreate(VenueReviewBase):
    pass


class VenueReviewUpdate(BaseModel):
    rating: Optional[int] = None
    comment: Optional[str] = None


class VenueReview(VenueReviewBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class VenueDetail(Venue):
    owner: dict
    photos: List[VenuePhoto] = []
    reviews: List[VenueReview] = []
    average_rating: Optional[float] = None
    review_count: int = 0