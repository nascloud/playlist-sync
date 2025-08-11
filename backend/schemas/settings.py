from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class ServerType(str, Enum):
    PLEX = "plex"
    JELLYFIN = "jellyfin"
    EMBY = "emby"

class ServerBase(BaseModel):
    name: str = Field(..., description="服务器名称")
    server_type: ServerType = Field(..., description="服务器类型")
    url: str = Field(..., description="服务器 URL")
    verify_ssl: bool = Field(True, description="是否验证SSL证书")

class ServerCreate(ServerBase):
    token: str = Field(..., description="API Token")

class ServerUpdate(BaseModel):
    name: Optional[str] = None
    server_type: Optional[ServerType] = None
    url: Optional[str] = None
    token: Optional[str] = None
    verify_ssl: Optional[bool] = None

class Server(ServerBase):
    id: int

    class Config:
        from_attributes = True
        extra = 'allow'

class ServersResponse(BaseModel):
    success: bool
    servers: List[Server] = []
    message: Optional[str] = None

class ServerResponse(BaseModel):
    success: bool
    server: Optional[Server] = None
    message: Optional[str] = None

class TestConnectionRequest(BaseModel):
    url: str
    token: str
    server_type: ServerType
    verify_ssl: bool = True

class TestConnectionResponse(BaseModel):
    success: bool
    message: str
