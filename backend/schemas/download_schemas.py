
from pydantic import BaseModel, Field
from typing import Optional, Literal

class DownloadSettingsBase(BaseModel):
    """
    下载设置的基础模型
    """
    api_key: Optional[str] = Field(None, title="API Key", description="用于访问下载服务的API Key")
    download_path: str = Field(..., title="下载路径", description="音乐文件保存的根路径")
    preferred_quality: str = Field("high", title="首选音质", description="例如：'standard', 'high', 'lossless'")
    download_lyrics: bool = Field(True, title="下载歌词", description="是否同时下载歌词文件")
    auto_download: bool = Field(False, title="全局自动下载", description="是否在同步后自动下载所有缺失歌曲")
    max_concurrent_downloads: int = Field(3, ge=1, le=10, title="最大并发下载数", description="同时进行的最大下载任务数量")
    log_retention_days: int = Field(30, ge=1, title="日志保留天数", description="下载日志文件保留的最长天数")

class DownloadSettingsCreate(DownloadSettingsBase):
    """
    用于创建或更新下载设置的模型
    """
    pass

class DownloadSettings(DownloadSettingsBase):
    """
    用于从API返回下载设置的模型
    """
    id: Literal[1] = Field(1, title="配置ID", description="固定为1，确保单行配置")

    class Config:
        from_attributes = True


class TestConnectionRequest(BaseModel):
    """
    测试下载连接请求体
    """
    api_key: str = Field(..., title="API Key", description="需要测试的API Key")


class TestConnectionResponse(BaseModel):
    """
    测试下载连接响应体
    """
    success: bool
    message: str


class DownloadAllRequest(BaseModel):
    """
    一键下载全部缺失歌曲的请求体
    """
    task_id: int = Field(..., title="同步任务ID")


class DownloadSingleRequest(BaseModel):
    """
    下载单个歌曲的请求体
    """
    task_id: int = Field(..., title="同步任务ID")
    song_id: str = Field(..., title="歌曲唯一标识")
    title: str
    artist: str
    album: Optional[str] = None


class DownloadActionResponse(BaseModel):
    """
    下载操作的通用响应体
    """
    session_id: Optional[int] = None
    success: bool
    message: str


from datetime import datetime
from typing import Optional, List, Any

class DownloadQueueItem(BaseModel):
    id: int
    session_id: int
    song_id: str
    title: str
    artist: str
    album: Optional[str] = None
    quality: str
    status: str
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class DownloadSession(BaseModel):
    id: int
    task_id: int
    task_name: Optional[str] = None
    session_type: str
    total_songs: int
    success_count: int
    failed_count: int
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    items: List[DownloadQueueItem] = []

    class Config:
        from_attributes = True

class SessionStatusResponse(BaseModel):
    success: bool
    sessions: List[DownloadSession] = []

