from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DownloadQueueItemBase(BaseModel):
    song_id: Optional[str] = None
    title: str
    artist: str
    album: Optional[str] = None
    status: str = 'pending'
    quality: Optional[str] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    platform: Optional[str] = None

class DownloadQueueItemCreate(DownloadQueueItemBase):
    pass

class DownloadQueueItem(DownloadQueueItemBase):
    id: int
    session_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
