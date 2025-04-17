from pydantic import BaseModel, Field
from typing import Optional
import time

from utils import Status, BallLevel, Request, Node

class REQUEST(BaseModel):
    '''Generic request to receive the specified information from a node'''
    request_type: Request 
    machine_id: Optional[int] = None
    session_id: Optional[int] = None

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: Node 
    destination_node: Node 


class CONFIRMATION(BaseModel):
    '''Generic acknowledgement to confirm commands or updates were received'''
    success: bool
    machine_id: Optional[int] = None
    session_id: Optional[int] = None
    status: Optional[Status] = None

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: Node 
    destination_node: Node 

class SESSION(BaseModel):
    '''Session information used to create booking or block off machine, sent to status manager to update schedule'''
    machine_id: Union[int, List[int]]
    session_id: int
    status: Status 
    start_time: float
    duration: Optional[float] = None
    time_created: float = Field(default_factory=lambda: time.time())

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: Node 
    destination_node: Node 

    @validator("machine_id", pre=True)
    def ensure_list(cls, v):
        return v if isinstance(v, list) else [v]

class SCHEDULE(BaseModel):
    '''Schedule which gets sent to booking nodes to check availability and current statuses'''
    date: str = time.time()
    schedule: list     #Create Schedule object type in the future for easy formatting

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: Node 
    destination_node: Node 

class MACHINE(BaseModel):
    machine_id: int
    session_id: Optional[int] = None
    status: Status 
    ball_level: Optional[BallLevel ] = None
    scheduled_until: Optional[float] = None
    last_updated: Optional[float] = None

    exchange_id: Optional[int] = None
    timestamp: float = Field(default_factory=lambda: time.time())
    origin_node: Node 
    destination_node: Node 

