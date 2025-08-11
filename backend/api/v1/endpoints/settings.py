from fastapi import APIRouter, HTTPException, Depends
from schemas.settings import (
    Server, ServerCreate, ServerUpdate, ServersResponse, ServerResponse,
    TestConnectionRequest, TestConnectionResponse, ServerType
)
from services.settings_service import SettingsService
from services.plex_service import PlexService
from typing import List

router = APIRouter()

@router.post("/settings/test", response_model=TestConnectionResponse)
async def test_server_connection(req: TestConnectionRequest):
    """测试服务器连接"""
    if req.server_type == ServerType.PLEX:
        success, message = PlexService.test_connection(req.url, req.token, req.verify_ssl)
        return TestConnectionResponse(success=success, message=message)
    # 为Jellyfin/Emby等其他服务器类型添加逻辑
    raise HTTPException(status_code=400, detail=f"不支持的服务器类型: {req.server_type}")


@router.post("/settings/{server_id}/test", response_model=TestConnectionResponse)
async def test_existing_server_connection(server_id: int):
    """测试已保存服务器的连接"""
    server = SettingsService.get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="服务器未找到。")

    # The decrypted token is attached to the server object by get_server_by_id
    token = getattr(server, 'decrypted_token', None)
    if not token:
        raise HTTPException(status_code=500, detail="无法获取服务器令牌。")

    if server.server_type == ServerType.PLEX:
        # 正确地传递 verify_ssl 参数
        verify_ssl = getattr(server, 'verify_ssl', True)
        success, message = PlexService.test_connection(server.url, token, verify_ssl)
        return TestConnectionResponse(success=success, message=message)
    
    raise HTTPException(status_code=400, detail=f"不支持的服务器类型: {server.server_type}")
    

@router.get("/settings", response_model=ServersResponse)
async def get_all_servers():
    """获取所有服务器设置"""
    servers = SettingsService.get_all_servers()
    return ServersResponse(success=True, servers=servers)

@router.post("/settings", response_model=ServerResponse)
async def add_server(server: ServerCreate):
    """添加一个新的服务器"""
    new_server = SettingsService.add_server(server)
    return ServerResponse(success=True, server=new_server, message="服务器已成功添加。")

@router.put("/settings/{server_id}", response_model=ServerResponse)
async def update_server(server_id: int, server_update: ServerUpdate):
    """更新一个已存在的服务器"""
    updated_server = SettingsService.update_server(server_id, server_update)
    if not updated_server:
        raise HTTPException(status_code=404, detail="服务器未找到。")
    return ServerResponse(success=True, server=updated_server, message="服务器已成功更新。")

@router.delete("/settings/{server_id}", response_model=ServerResponse)
async def delete_server(server_id: int):
    """删除一个服务器"""
    success = SettingsService.delete_server(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="服务器未找到。")
    return ServerResponse(success=True, message="服务器已成功删除。")
