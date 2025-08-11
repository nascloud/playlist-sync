from fastapi import APIRouter, HTTPException, Path, Depends, Body
from fastapi.responses import StreamingResponse
from schemas.tasks import Task, TaskCreate, TaskList, TaskUpdate
from schemas.response import SuccessResponse
from services.task_service import TaskService
from services.sync_service import SyncService
from services.download_service import get_download_service, DownloadService
from services.log_service import LogService
from utils.scheduler import get_scheduler, TaskScheduler
from pydantic import BaseModel, HttpUrl
import logging
import json
import asyncio
from utils.progress_manager import progress_manager
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/tasks", response_model=TaskList)
async def get_tasks():
    """获取所有同步任务"""
    try:
        tasks = TaskService.get_all_tasks()
        return TaskList(success=True, tasks=tasks)
    except Exception as e:
        logger.error(f"获取任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取任务时发生内部错误。")

@router.post("/tasks", response_model=Task, status_code=201)
async def create_task(task_data: TaskCreate, download_service: DownloadService = Depends(get_download_service), scheduler: TaskScheduler = Depends(get_scheduler)):
    """
    创建一个新的同步任务。
    如果未提供名称，将尝试从URL解析标题。
    """
    try:
        # 如果用户没有提供歌单名，则尝试从URL解析
        if not task_data.name:
            try:
                sync_service = SyncService(download_service=download_service)
                playlist_info = await sync_service.preview_playlist(
                    playlist_url=str(task_data.playlist_url), 
                    platform=task_data.platform
                )
                # 使用解析出的标题，如果标题为空则使用默认值
                task_data.name = playlist_info.get('title') or '新歌单'
            except Exception as e:
                logger.error(f"为URL {task_data.playlist_url} 解析标题失败: {e}", exc_info=True)
                raise HTTPException(status_code=400, detail="无法解析歌单链接，请检查链接是否正确或稍后再试。")

        task_id = TaskService.create_task(task_data)
        new_task = TaskService.get_task_by_id(task_id)
        if not new_task:
            raise HTTPException(status_code=500, detail="创建任务后无法找到该任务。")
        
        # 安排新任务
        scheduler.reload_task_schedule(new_task.id)

        return new_task
    except HTTPException:
        # 重新抛出已处理的HTTP异常，以便FastAPI可以正确处理
        raise
    except Exception as e:
        logger.error(f"创建任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建任务时发生未知错误: {str(e)}")



@router.put("/tasks/{task_id}", response_model=SuccessResponse)
async def update_task_schedule(task_id: int = Path(..., title="任务ID"), task_update: TaskUpdate = Body(...), scheduler: TaskScheduler = Depends(get_scheduler)):
    """更新任务的同步计划"""
    try:
        success = TaskService.update_task_schedule(task_id, task_update.cron_schedule)
        if success:
            # 重新加载任务调度
            scheduler.reload_task_schedule(task_id)
            return SuccessResponse(success=True, message="任务计划已成功更新。")
        else:
            raise HTTPException(status_code=404, detail="未找到指定ID的任务。")
    except Exception as e:
        logger.error(f"更新任务计划失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新任务计划失败: {str(e)}")

@router.delete("/tasks/{task_id}", response_model=SuccessResponse)
async def delete_task(task_id: int = Path(..., title="任务ID"), scheduler: TaskScheduler = Depends(get_scheduler)):
    """删除任务"""
    try:
        # 在删除前，先从调度器中移除
        scheduler.remove_task_from_schedule(task_id)
        
        success = TaskService.delete_task(task_id)
        if success:
            return SuccessResponse(success=True, message="任务已成功删除。")
        else:
            raise HTTPException(status_code=404, detail="未找到指定ID的任务。")
    except Exception as e:
        logger.error(f"删除任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"删除任务失败: {str(e)}")

@router.get("/tasks/{task_id}/sync/stream")
async def sync_task_stream(task_id: int = Path(..., title="任务ID"), download_service: DownloadService = Depends(get_download_service)):
    """
    通过 Server-Sent Events (SSE) 实时流式传输同步进度。
    """
    # 立即在后台启动同步任务
    asyncio.create_task(run_sync_in_background(task_id, download_service))
    
    # 返回一个流式响应
    return StreamingResponse(
        progress_manager.get_stream(task_id),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no' # 对 Nginx 代理友好
        }
    )

async def run_sync_in_background(task_id: int, download_service: DownloadService):
    """一个在后台运行同步任务的辅助函数。"""
    try:
        task = TaskService.get_task_by_id(task_id)
        if not task:
            await progress_manager.send_message(task_id, json.dumps({"status": "error", "message": "未找到任务"}), event="error")
            return

        sync_service = SyncService(download_service=download_service)
        await sync_service.sync_playlist(
            task_id=task.id,
            server_id=task.server_id,
            playlist_url=task.playlist_url,
            platform=task.platform,
            playlist_name=task.name,
            log_callback=lambda level, msg: LogService.log_activity(task_id, level, msg)
        )
    except Exception as e:
        logger.error(f"后台同步任务 {task_id} 失败: {e}", exc_info=True)
        error_message = f"同步时发生意外错误: {e}"
        TaskService.update_task_status(task_id, 'failed', error_message)
        await progress_manager.send_message(task_id, json.dumps({"status": "failed", "message": str(e)}), event="error")

class UnmatchedSongsResponse(BaseModel):
    success: bool
    unmatched_songs: list

@router.get("/tasks/{task_id}/unmatched", response_model=UnmatchedSongsResponse)
async def get_unmatched_songs(task_id: int = Path(..., title="任务ID")):
    """获取任务的不匹配歌曲"""
    try:
        unmatched_songs = TaskService.get_unmatched_songs_for_task(task_id)
        return UnmatchedSongsResponse(success=True, unmatched_songs=unmatched_songs)
    except Exception as e:
        logger.error(f"获取任务 {task_id} 的不匹配歌曲时发生错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取不匹配歌曲失败: {str(e)}")

