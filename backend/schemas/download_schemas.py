
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Union
from datetime import datetime
import re

class DownloadSettingsBase(BaseModel):
    """
    下载设置的基础模型
    """
    download_path: str = Field(..., title="下载路径", description="音乐文件保存的根路径")
    preferred_quality: str = Field("high", title="首选音质", description="例如：'standard', 'high', 'lossless'")
    download_lyrics: bool = Field(True, title="下载歌词", description="是否同时下载歌词文件")
    auto_download: bool = Field(False, title="全局自动下载", description="是否在同步后自动下载所有缺失歌曲")
    max_concurrent_downloads: int = Field(3, ge=1, le=10, title="最大并发下载数", description="同时进行的最大下载任务数量")
    log_retention_days: int = Field(30, ge=1, title="日志保留天数", description="下载日志文件保留的最长天数")
    scan_interval_minutes: int = Field(30, ge=5, le=1440, title="扫描间隔（分钟）", description="定期扫描新音乐的间隔时间（分钟）")

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
    last_updated: Optional[datetime] = Field(None, title="最后更新时间")

    class Config:
        from_attributes = True


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

class SearchResultItem(BaseModel):
    """搜索结果项模型"""
    song_id: str = Field(..., title="歌曲ID", description="歌曲的唯一标识")
    title: str = Field(..., title="歌曲标题", description="歌曲的标题")
    artist: str = Field(..., title="歌手", description="歌曲的歌手")
    album: Optional[str] = Field(None, title="专辑", description="歌曲所属的专辑")
    platform: str = Field(..., title="平台", description="音乐平台，如qq、netease等")
    duration: Optional[int] = Field(None, title="时长", description="歌曲时长（秒）")
    quality: Optional[str] = Field(None, title="音质", description="可用的音质选项")
    score: Optional[float] = Field(None, title="匹配度", description="与搜索关键词的匹配度分数")

    @field_validator('duration', mode='before')
    @classmethod
    def parse_duration(cls, v):
        """将 'M分S秒' 格式的字符串转换为总秒数的整数"""
        if v is None:
            return None
        
        # 如果已经是整数，直接返回
        if isinstance(v, int):
            return v
        
        # 如果是字符串，尝试解析
        if isinstance(v, str):
            # 尝试匹配 'M分S秒' 格式
            match = re.match(r'^(\d+)分(\d+)秒$', v)
            if match:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                return minutes * 60 + seconds
            
            # 尝试直接转换为整数
            try:
                return int(v)
            except ValueError:
                pass
        
        # 如果无法解析，返回 None
        return None

    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """搜索响应模型"""
    success: bool = Field(..., title="成功状态", description="搜索是否成功")
    message: str = Field(..., title="消息", description="搜索结果的消息")
    results: List[SearchResultItem] = Field([], title="搜索结果", description="搜索结果列表")
    total: int = Field(0, title="总数", description="搜索结果的总数")
    page: int = Field(1, title="页码", description="当前页码")
    size: int = Field(10, title="每页大小", description="每页的结果数量")


class SessionStatusResponse(BaseModel):
    success: bool
    sessions: List[DownloadSession] = []

