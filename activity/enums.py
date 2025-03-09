from enum import Enum


class TeamStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class ActivityType(str, Enum):
    SPORT = "sport"
    SOCIAL = "social"
    TRAINING = "training"
    COMPETITION = "competition"
    OTHER = "other"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"