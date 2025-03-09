from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional, List

from .enums import Gender, FriendshipStatus


class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str
    name: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[Gender] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    profile_pic: Optional[str] = None


class FriendshipBase(BaseModel):
    user_id: int
    friend_id: int


class FriendshipCreate(FriendshipBase):
    pass


class FriendshipUpdate(BaseModel):
    status: FriendshipStatus


class UserFriend(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    profile_pic: Optional[str] = None
    status: FriendshipStatus


class User(UserBase, UserUpdate):
    id: int
    cognito_id: str
    created_dt: datetime
    friends_count: int
    teams_count: int

    class Config:
        orm_mode = True


class UserWithFriends(User):
    friends: List[UserFriend] = []


class CognitoTokenResponse(BaseModel):
    access_token: str
    id_token: str
    refresh_token: str
    token_type: str
    expires_in: int