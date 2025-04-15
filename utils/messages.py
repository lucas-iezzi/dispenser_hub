from pydantic import BaseModel
from typing import Optional
import time

class MachineCommand(BaseModel):
    machine_id: str
    status: str
    duration: Optional[float] = None
    timestamp: float = time.time()
    origin_node: str = "unknown"
