from fastapi import APIRouter, HTTPException, Query
from schemas.log import LogsResponse
from services.log_service import LogService
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/logs", response_model=LogsResponse)
async def get_logs(
    task_id: Optional[int] = Query(None, description="任务ID"),
    level: Optional[str] = Query(None, description="日志级别 (info, warning, error)"),
    limit: int = Query(100, description="返回日志数量限制")
):
    """获取同步日志"""
    try:
        logs = LogService.get_logs(task_id=task_id, level=level, limit=limit)
        return LogsResponse(success=True, logs=logs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"无法从数据库获取日志: {str(e)}")