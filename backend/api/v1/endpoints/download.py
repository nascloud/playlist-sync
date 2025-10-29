
import asyncio
from fastapi import APIRouter, HTTPException, Depends
from typing import Any, Optional
from datetime import datetime
import logging
import httpx

from schemas.download_schemas import (
    DownloadSettings,
    DownloadSettingsCreate,
    TestConnectionResponse,
    DownloadAllRequest,
    DownloadSingleRequest,
    DownloadActionResponse,
    SessionStatusResponse,
    SearchResponse
)
from services.settings_service import SettingsService
from services.download.download_service import get_download_service, DownloadService
from services.download.downloader_core import downloader
from services.download.download_db_service import download_db_service
from services.download.download_queue_manager import download_queue_manager
from core.logging_config import LOGS_DIR, download_log_manager
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
            download_path=app_settings.DOWNLOAD_PATH or "",
            last_updated=datetime.now()
        )
    return settings

@router.post("/download-settings", response_model=DownloadSettings)
async def save_download_settings(settings_in: DownloadSettingsCreate) -> Any:
    """保存或更新下载设置。"""
    # 保存设置
    saved_settings = SettingsService.save_download_settings(settings_in)
    
    # 如果设置了新的扫描间隔，更新调度器
    if hasattr(settings_in, 'scan_interval_minutes') and settings_in.scan_interval_minutes:
        try:
            from utils.scheduler import get_scheduler
            scheduler = get_scheduler()
            scheduler.update_scan_interval(settings_in.scan_interval_minutes)
        except Exception as e:
            logging.error(f"更新调度器扫描间隔时出错: {e}")
    
    return saved_settings

@router.post("/download-settings/test-api", response_model=TestConnectionResponse)
async def test_api_connection() -> Any:
    """测试与下载API的连接。"""
    try:
        import httpx
        
        # 测试新的API连接
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.vkeys.cn/", timeout=10.0)
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("code") == 0:
                    return TestConnectionResponse(success=True, message="API连接成功！" + response_data.get("message", ""))
                else:
                    return TestConnectionResponse(success=False, message="API连接失败: " + response_data.get("message", "未知错误"))
            else:
                return TestConnectionResponse(success=False, message=f"API连接失败，状态码: {response.status_code}")
    except httpx.TimeoutException:
        return TestConnectionResponse(success=False, message="API连接超时，请检查网络连接")
    except Exception as e:
        return TestConnectionResponse(success=False, message=f"API连接失败: {str(e)}")

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

@router.post("/session/{session_id}/retry-failed", response_model=DownloadActionResponse)
async def retry_failed_items(session_id: int):
    """重试一个会话中所有失败的下载项目。"""
    try:
        count = await download_queue_manager.retry_failed_items_in_session(session_id)
        if count > 0:
            return DownloadActionResponse(
                success=True, 
                message=f"已将 {count} 个失败的项目重新加入下载队列。"
            )
        else:
            # 检查是否是因为计数器不一致导致的问题
            # 修复会话计数器并再次检查
            loop = asyncio.get_running_loop()
            success_count, failed_count = await loop.run_in_executor(
                None, download_db_service.fix_session_counts, session_id
            )
            
            if failed_count > 0:
                # 计数器修复后有失败项目，再次尝试重试
                count = await download_queue_manager.retry_failed_items_in_session(session_id)
                if count > 0:
                    return DownloadActionResponse(
                        success=True, 
                        message=f"已将 {count} 个失败的项目重新加入下载队列。"
                    )
            
            return DownloadActionResponse(
                success=True,
                message="没有失败的项目需要重试。"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重试失败项目时出错: {str(e)}")

@router.post("/session/item/{item_id}/retry", response_model=DownloadActionResponse)
async def retry_single_item(item_id: int):
    """重试单个失败的下载项目。"""
    try:
        success = await download_queue_manager.retry_item(item_id)
        if success:
            return DownloadActionResponse(
                success=True,
                message="项目已重新加入下载队列。"
            )
        else:
            # 检查项目当前状态
            loop = asyncio.get_running_loop()
            item_details = await loop.run_in_executor(
                None, download_db_service.get_item_details, item_id
            )
            
            if item_details and item_details.status == 'failed':
                # 项目状态是失败，但重试失败，可能是会话已完成
                # 尝试修复会话并重新激活
                session_id = item_details.session_id
                await loop.run_in_executor(
                    None, download_db_service.reactivate_session, session_id
                )
                
                # 再次尝试重试
                success = await download_queue_manager.retry_item(item_id)
                if success:
                    return DownloadActionResponse(
                        success=True,
                        message="项目已重新加入下载队列。"
                    )
            
            return DownloadActionResponse(
                success=False,
                message="无法重试该项目。项目可能不是失败状态或会话已完成。"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重试项目时出错: {str(e)}")

@router.get("/search", response_model=SearchResponse)
async def search_songs(
    keyword: str,
    platform: Optional[str] = None,
    page: int = 1,
    size: int = 10,
    download_service: DownloadService = Depends(get_download_service)
) -> Any:
    """搜索歌曲。"""
    try:
        # 验证参数
        if not keyword or not keyword.strip():
            raise HTTPException(status_code=400, detail="搜索关键词不能为空")
        
        if page < 1:
            page = 1
        
        if size < 1 or size > 50:
            size = 10
        
        # 调用搜索服务
        search_result = await download_service.search_songs(
            keyword=keyword.strip(),
            platform=platform,
            page=page,
            size=size
        )
        
        return search_result
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logging.exception(f"搜索歌曲时发生错误:")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


