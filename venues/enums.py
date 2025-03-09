from enum import Enum


class VenueType(str, Enum):
    SPORTS_FACILITY = "sports_facility"
    STADIUM = "stadium"
    GYM = "gym"
    COURT = "court"
    FIELD = "field"
    POOL = "pool"
    OTHER = "other"


class VenueStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_MAINTENANCE = "under_maintenance"
    CLOSED = "closed"