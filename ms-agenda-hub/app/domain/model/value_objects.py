from enum import Enum


class CoverageStatus(str, Enum):
    COVERED     = "COVERED"
    NOT_COVERED = "NOT_COVERED"
    UNAVAILABLE = "UNAVAILABLE"


class SlotStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BLOCKED   = "BLOCKED"
    CONFIRMED = "CONFIRMED"


class AppointmentStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
