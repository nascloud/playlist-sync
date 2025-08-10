from typing import Optional
from datetime import datetime

class Task:
    def __init__(
        self,
        id: Optional[int] = None,
        playlist_title: str = "",
        source_url: str = "",
        source_platform: str = "",
        sync_schedule: str = "",
        last_sync_time: Optional[str] = None,
        status: str = "pending",
        unmatched_songs: Optional[str] = None,
        error_message: Optional[str] = None,
        last_sync_total_count: int = 0,
        last_sync_matched_count: int = 0
    ):
        self.id = id
        self.playlist_title = playlist_title
        self.source_url = source_url
        self.source_platform = source_platform
        self.sync_schedule = sync_schedule
        self.last_sync_time = last_sync_time
        self.status = status
        self.unmatched_songs = unmatched_songs
        self.error_message = error_message
        self.last_sync_total_count = last_sync_total_count
        self.last_sync_matched_count = last_sync_matched_count
