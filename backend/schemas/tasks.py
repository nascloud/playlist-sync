from pydantic import BaseModel, validator
from croniter import croniter
from typing import Optional, List
from datetime import datetime

class TaskBase(BaseModel):
    name: str
    playlist_url: str
    platform: str
    cron_schedule: Optional[str] = '0 2 * * *'  # 默认每天2点
    server_id: int

    @validator('cron_schedule')
    def validate_cron_schedule(cls, v):
        if v is None:
            return v
        if not croniter.is_valid(v):
            raise ValueError('无效的Cron表达式')
        return v

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    cron_schedule: str

    @validator('cron_schedule')
    def validate_cron_schedule(cls, v):
        if not croniter.is_valid(v):
            raise ValueError('无效的Cron表达式')
        return v

class Task(TaskBase):
    id: int
    status: str
    last_sync_time: Optional[datetime] = None
    unmatched_songs: Optional[str] = None
    total_songs: int
    matched_songs: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskList(BaseModel):
    success: bool
    tasks: List[Task]
