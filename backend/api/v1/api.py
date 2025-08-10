from fastapi import APIRouter
from api.v1.endpoints import settings, tasks, logs, download

api_router = APIRouter()

# 包含所有API端点
api_router.include_router(settings.router)
api_router.include_router(tasks.router)
api_router.include_router(logs.router)
api_router.include_router(download.router, prefix="/download", tags=["Download"])
