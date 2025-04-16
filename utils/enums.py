# utils/status_enum.py
from enum import Enum

class StatusEnum(str, Enum):
    ACTIVE = "active"
    AVAILABLE = "available"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    IDLE = "idle"
    ERROR = "error"
    NULL =  None

class BallLevelEnum(str, Enum):
    FULL = "full"
    MEDIUM = "medium"
    LOW = "low"
    URGENT = "urgent"
    EMPTY = "empty"
    NULL = None

class RequestEnum(str, Enum):
    SCHEDULE = "schedule"
    SESSION = "session"
    MACHINE = "machine"