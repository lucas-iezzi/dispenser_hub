from enum import Enum

class Status(str, Enum):
    ACTIVE = "active"
    AVAILABLE = "available"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    IDLE = "idle"
    ERROR = "error"
    NULL =  None

class BallLevel(str, Enum):
    FULL = "full"
    MEDIUM = "medium"
    LOW = "low"
    URGENT = "urgent"
    EMPTY = "empty"
    NULL = None

class Request(str, Enum):
    SCHEDULE = "schedule"
    SESSION = "session"
    MACHINE = "machine"

class Node(str, Enum):
    MANAGER = "manager"
    HANDLER = "handler"
    ADMIN = "admin"
    KIOSK = "kiosk"
    RESERVATION = "reservation"
    MACHINE = "machine"