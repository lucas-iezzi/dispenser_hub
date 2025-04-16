from pydantic import BaseModel, Field
from typing import Optional
import time

from utils import StatusEnum, BallLevelEnum, RequestEnum

class Request(BaseModel):
    '''Generic request to receive the specified information from a node'''
    request_type: RequestEnum
    machine_id = Optional[int] = None
    session_id: Optional[int] = None

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: str
    destination_node: str


class Confirm(BaseModel):
    '''Generic acknowledgement to confirm commands or updates were received'''
    success: bool
    session_id: int
    status: Optional[StatusEnum] = None

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: str
    destination_node: str

class Session(BaseModel):
    '''Session information used to create booking or block off machine, sent to status manager to update schedule'''
    machine_id: Union[int, List[int]]
    session_id: int
    status: StatusEnum
    start_time: float
    duration: Optional[float] = None
    time_created: float = Field(default_factory=lambda: time.time())

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: str
    destination_node: str

    @validator("machine_id", pre=True)
    def ensure_list(cls, v):
        return v if isinstance(v, list) else [v]

class Schedule(BaseModel):
    '''Schedule which gets sent to booking nodes to check availability and current statuses'''
    date: str = time.time()
    schedule: list     #Create Schedule object type in the future for easy formatting

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: str = "schedule_manager.py"
    destination_node: str

class Machine(BaseModel):
    machine_id: int
    session_id: Optional[int] = None
    status: StatusEnum
    ball_level: Optional[BallLevelEnum] = None
    scheduled_until: Optional[float] = None
    last_updated: Optional[float] = None

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: str
    destination_node: str

