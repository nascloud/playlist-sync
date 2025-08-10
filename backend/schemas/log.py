from pydantic import BaseModel
from typing import Optional, List

class LogBase(BaseModel):
    task_id: int
    timestamp: str
    level: str
    message: str

class LogCreate(LogBase):
    pass

class LogInDBBase(LogBase):
    id: int
    
    class Config:
        from_attributes = True

class Log(LogInDBBase):
    pass

class LogsResponse(BaseModel):
    success: bool
    logs: List[Log]