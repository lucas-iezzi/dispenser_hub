from pydantic import BaseModel, Field, validator
from typing import Optional, Union, List
import time

from utils.enums import Status, BallLevel, Request, Node

class REQUEST(BaseModel):
    '''Generic request to receive the specified information from a node'''
    request_type: Request  # The type of request (e.g., SCHEDULE, SESSION, MACHINE)
    date: Optional[str] = None  # The date for which the schedule is being requested (optional)
    machine_id: Optional[int] = None  # The ID of the machine being requested (if applicable)
    session_id: Optional[int] = None  # The ID of the session being requested (if applicable)

    exchange_id: Optional[int] = None  # Unique ID for tracking the request/response exchange
    timestamp: float = Field(default_factory=lambda: time.time())  # Time when the request was created
    origin_node: Optional[Node] = None  # The node that initiated the request
    destination_node: Optional[Node] = None  # The node that should handle the request


class ACKNOWLEDGE(BaseModel):
    '''Generic acknowledgement to confirm commands or updates were received'''
    success: bool  # Indicates whether the operation was successful
    message: Optional[str] = None  # Optional message providing additional information about the confirmation
    machine_id: Optional[int] = None  # The ID of the machine related to the confirmation (if applicable)
    session_id: Optional[int] = None  # The ID of the session related to the confirmation (if applicable)
    status: Optional[Status] = None  # The status of the machine or session being confirmed

    exchange_id: Optional[int] = None  # Unique ID for tracking the confirmation exchange
    timestamp: float = Field(default_factory=lambda: time.time())  # Time when the confirmation was created
    origin_node: Optional[Node] = None  # The node that sent the confirmation
    destination_node: Optional[Node] = None  # The node that should receive the confirmation


class SESSION(BaseModel):
    '''Session information used to create booking or block off machine, sent to status manager to update schedule'''
    machine_id: Union[int, List[int]]  # The ID(s) of the machine(s) involved in the session
    session_id: int  # The unique ID of the session
    status: Status  # The status of the session (e.g., RESERVED, ACTIVE)
    start_time: float  # The start time of the session (in epoch time)
    duration: Optional[float] = None  # The duration of the session (in seconds)
    time_created: float = Field(default_factory=lambda: time.time())  # Time when the session was created

    exchange_id: Optional[int] = None  # Unique ID for tracking the session exchange
    timestamp: float = Field(default_factory=lambda: time.time())  # Time when the session message was created
    origin_node: Optional[Node] = None  # The node that created the session
    destination_node: Optional[Node] = None  # The node that should handle the session

    @validator("machine_id", pre=True)
    def ensure_list(cls, v):
        # Ensures that machine_id is always a list, even if a single ID is provided
        return v if isinstance(v, list) else [v]


class SCHEDULE(BaseModel):
    '''Schedule which gets sent to booking nodes to check availability and current statuses'''
    date: str = time.time()  # The date of the schedule (in epoch time)
    schedule: list  # A list representing the schedule (format to be defined in the future)

    exchange_id: Optional[int] = None  # Unique ID for tracking the schedule exchange
    timestamp: float = Field(default_factory=lambda: time.time())  # Time when the schedule message was created
    origin_node: Optional[Node] = None  # The node that created the schedule
    destination_node: Optional[Node] = None  # The node that should handle the schedule


class MACHINE(BaseModel):
    '''Represents the status of a machine'''
    machine_id: int  # The unique ID of the machine
    session_id: Optional[int] = None  # The ID of the session currently associated with the machine (if any)
    status: Status  # The current status of the machine (e.g., ACTIVE, IDLE)
    ball_level: Optional[BallLevel] = None  # The current ball level of the machine (e.g., FULL, LOW)
    scheduled_until: Optional[float] = None  # The time until the machine is scheduled (in epoch time)
    last_updated: Optional[float] = None  # The last time the machine's status was updated (in epoch time)

    exchange_id: Optional[int] = None  # Unique ID for tracking the machine status exchange
    timestamp: float = Field(default_factory=lambda: time.time())  # Time when the machine message was created
    origin_node: Optional[Node] = None  # The node that sent the machine status
    destination_node: Optional[Node] = None  # The node that should handle the machine status
