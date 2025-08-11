
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Optional
from datetime import datetime
import logging

from schemas.download_schemas import (
    DownloadSettings, 
    DownloadSettingsCreate, 
    TestConnectionRequest,
    TestConnectionResponse,
    DownloadAllRequest,
    DownloadSingleRequest,
    DownloadActionResponse,
    SessionStatusResponse
)
from services.settings_service import SettingsService
from services.download_service import get_download_service, DownloadService
from services.downloader_core import downloader
from services.download_db_service import download_db_service
from services.download_queue_manager import download_queue_manager
from core.logging_config import LOGS_DIR
from core.config import settings as app_settings

router = APIRouter()


@router.get("/session/{session_id}/logs")
async def get_session_logs(session_id: int):
    """获取指定下载会话的日志内容。"""
    try:
        # 我们直接从文件系统读取日志，这比通过logger对象操作更直接
        log_dir = LOGS_DIR / "downloads"
        log_file = log_dir / f"session_{session_id}.log"

        if not log_file.exists():
            raise HTTPException(status_code=404, detail="该会话的日志文件未找到。")

        # 为防止读取过大的日志文件导致内存问题，可以只读取最后N行
        # 这里我们暂时先读取全部内容，后续可优化
        return {"success": True, "logs": log_file.read_text(encoding='utf-8')}
    except Exception as e:
        logging.exception(f"获取会话 {session_id} 的日志时发生错误:")
        raise HTTPException(status_code=500, detail=f"获取日志失败: {str(e)}")



@router.get("/status", response_model=SessionStatusResponse)
async def get_sessions_status():
    """获取所有下载会话及其包含的项目的完整层级状态。"""
    try:
        loop = asyncio.get_running_loop()
        status_data = await loop.run_in_executor(None, download_db_service.get_full_queue_status)
        return SessionStatusResponse(success=True, sessions=status_data.get("sessions", []))
    except Exception as e:
        logging.exception("获取会话状态时发生错误：")
        raise HTTPException(status_code=500, detail=f"获取会话状态失败: {str(e)}")

@router.get("/download-settings", response_model=DownloadSettings)
async def get_download_settings() -> Any:
    """获取当前的下载设置。"""
    settings = SettingsService.get_download_settings()
    if not settings:
        # 如果数据库中没有设置，返回环境变量中的默认值
        return DownloadSettings(
            api_key=app_settings.DOWNLOADER_API_KEY or "",
            download_path=app_settings.DOWNLOAD_PATH or "",
            last_updated=datetime.now()
        )
    return settings

@router.post("/download-settings", response_model=DownloadSettings)
async def save_download_settings(settings_in: DownloadSettingsCreate) -> Any:
    """保存或更新下载设置。"""
    return SettingsService.save_download_settings(settings_in)

@router.post("/download-settings/test", response_model=TestConnectionResponse)
async def test_download_connection(request: TestConnectionRequest) -> Any:
    """测试与下载源的连接。"""
    try:
        loop = asyncio.get_running_loop()
        settings = await loop.run_in_executor(None, SettingsService.get_download_settings)

        if not settings:
             raise HTTPException(status_code=404, detail="请先保存下载设置")
        
        # 使用传入的API Key进行测试，并使用已保存的路径
        await loop.run_in_executor(
            None,
            downloader.initialize,
            request.api_key,
            settings.download_path
        )
        # 可以在 downloader.initialize 中加入一个实际的连接测试，如查询 key info
        return TestConnectionResponse(success=True, message="连接成功！")
    except Exception as e:
        return TestConnectionResponse(success=False, message=f"连接失败: {str(e)}")

@router.post("/all-missing", response_model=DownloadActionResponse)
async def download_all_missing(request: DownloadAllRequest, download_service: DownloadService = Depends(get_download_service)) -> Any:
    """一键下载指定任务中所有缺失的歌曲。"""
    try:
        session_id = await download_service.download_all_missing(task_id=request.task_id)
        if session_id > 0:
            return DownloadActionResponse(
                success=True, 
                session_id=session_id,
                message=f"已为任务 {request.task_id} 创建批量下载会话。"
            )
        else:
            return DownloadActionResponse(
                success=False, 
                session_id=0,
                message=f"任务 {request.task_id} 没有需要下载的歌曲。"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建批量下载失败: {str(e)}")

@router.post("/single", response_model=DownloadActionResponse)
async def download_single_song(request: DownloadSingleRequest, download_service: DownloadService = Depends(get_download_service)) -> Any:
    """下载单个指定的歌曲。"""
    logging.info(
        f"接收到单曲下载请求: task_id={request.task_id}, song_id={request.song_id}, "
        f"title='{request.title}', artist='{request.artist}'"
    )
    try:
        session_id = await download_service.download_single_song(
            task_id=request.task_id,
            song_info=request  # 传递 Pydantic 模型实例
        )
        if session_id > 0:
            return DownloadActionResponse(success=True, session_id=session_id, message=f"歌曲 '{request.title}' 已加入下载队列。")
        else:
            raise HTTPException(status_code=500, detail="无法将歌曲加入下载队列。")
    except Exception as e:
        logging.exception(f"下载单曲 '{request.title}' 时发生错误:")
        raise HTTPException(status_code=500, detail=f"下载单曲失败: {str(e)}")

@router.post("/session/{session_id}/pause", response_model=DownloadActionResponse)
async def pause_download_session(session_id: int):
    """暂停一个下载会话。"""
    await download_queue_manager.pause_session(session_id)
    return DownloadActionResponse(success=True, message=f"会话 {session_id} 已暂停。")

@router.post("/session/{session_id}/resume", response_model=DownloadActionResponse)
async def resume_download_session(session_id: int):
    """恢复一个下载会话。"""
    await download_queue_manager.resume_session(session_id)
    return DownloadActionResponse(success=True, message=f"会话 {session_id} 已恢复。")

@router.delete("/session/{session_id}", response_model=DownloadActionResponse)
async def delete_download_session(session_id: int):
    """删除一个下载会话及其所有项目。"""
    await download_queue_manager.delete_session(session_id)
    return DownloadActionResponse(success=True, message=f"会话 {session_id} 已删除。")

@router.post("/clear-completed", response_model=DownloadActionResponse)
async def clear_completed_downloads(_: dict = {}):
    """清除所有已完成的下载项（成功、失败、已取消）。"""
    count = await download_queue_manager.clear_completed()
    return DownloadActionResponse(success=True, message=f"成功清除了 {count} 个已完成的项目。")


