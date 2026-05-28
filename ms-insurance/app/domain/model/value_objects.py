from enum import Enum


class CoverageStatus(str, Enum):
    COVERED     = "COVERED"
    NOT_COVERED = "NOT_COVERED"
    UNAVAILABLE = "UNAVAILABLE"
