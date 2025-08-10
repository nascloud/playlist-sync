from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .playlist import Track

class TaskBase(BaseModel):
    playlist_title: str
    source_url: str
    source_platform: str
    sync_schedule: str

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    sync_schedule: str

class TaskInDBBase(TaskBase):
    id: int
    last_sync_time: Optional[str] = None
    status: str = "idle"
    unmatched_songs: Optional[str] = None
    last_sync_total_count: int = 0
    last_sync_matched_count: int = 0
    auto_download: bool = False
    
    class Config:
        from_attributes = True

class Task(TaskInDBBase):
    pass

class TaskSyncResponse(BaseModel):
    success: bool
    message: str

class TasksResponse(BaseModel):
    success: bool
    tasks: List[Task]

class TaskDeleteResponse(BaseModel):
    success: bool
    message: str

class UnmatchedSongsResponse(BaseModel):
    success: bool
    unmatched_songs: List[Track]