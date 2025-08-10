from pydantic import BaseModel
from typing import List, Optional

class Track(BaseModel):
    title: str
    artist: str
    album: Optional[str] = None
    song_id: Optional[str] = None
    platform: Optional[str] = None

class Playlist(BaseModel):
    title: str
    tracks: List[Track]

class PlaylistParseRequest(BaseModel):
    url: str
    platform: str

class PlaylistParseResponse(BaseModel):
    success: bool
    title: str
    tracks: List[Track]
    message: str = None

class PlaylistImportRequest(BaseModel):
    sourceUrl: str
    sourcePlatform: str
    syncSchedule: str

class PlaylistImportResponse(BaseModel):
    success: bool
    message: str
    taskId: int = None

class PlaylistPreviewRequest(BaseModel):
    sourceUrl: str
    sourcePlatform: str

class PlaylistPreviewData(BaseModel):
    title: str
    track_count: int

class PlaylistPreviewResponse(BaseModel):
    success: bool
    data: PlaylistPreviewData

class MatchedTrack(Track):
    plex_title: str
    plex_artist: str
    score: int
