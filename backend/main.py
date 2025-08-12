from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
from contextlib import asynccontextmanager
import os
import logging

from api.v1.api import api_router
from api.v1.endpoints import auth
from core.config import settings
from utils.scheduler import set_scheduler, TaskScheduler
from services.download_service import set_download_service, DownloadService, get_download_service
from services.settings_service import SettingsService
from services.sync_service import SyncService
from core.logging_config import setup_logging
from core import security
from jose import JWTError


# ... (其他导入)

logger = logging.getLogger(__name__)

def check_security_prerequisites():
    """检查并确保关键的安全环境变量已设置。"""
    missing_vars = []
    if not settings.SECRET_KEY:
        missing_vars.append("SECRET_KEY")
    if not settings.APP_PASSWORD:
        missing_vars.append("APP_PASSWORD")
    
    if missing_vars:
        error_message = (
            f"错误：缺少必要的安全环境变量: {', '.join(missing_vars)}。\n"
            "请在 .env 文件或您的运行环境中设置这些变量。\n"
            "SECRET_KEY 可以通过运行 'openssl rand -hex 32' 生成。"
        )
        logger.critical(error_message)
        raise ValueError(error_message)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时的初始化代码
    check_security_prerequisites()
    setup_logging()
    
    # 1. 创建服务实例 (依赖顺序: Download -> Sync -> Scheduler)
    settings_service = SettingsService()
    download_service_instance = DownloadService(settings_service=settings_service)
    sync_service_instance = SyncService(download_service=download_service_instance)
    scheduler_instance = TaskScheduler(sync_service=sync_service_instance)
    
    # 2. 初始化下载器
    await download_service_instance.initialize_downloader()
    
    # 3. 初始化AutoPlaylistService
    await sync_service_instance.initialize_auto_playlist_service()
    
    # 4. 将完全初始化的实例设置为全局单例
    set_download_service(download_service_instance)
    set_scheduler(scheduler_instance)
    
    # 5. 启动调度器
    scheduler_instance.start()
    
    logger.info("应用启动完成，所有服务已初始化。")
    
    yield
    
    # 关闭时的清理代码
    scheduler_instance.shutdown()
    logger.info("应用已关闭。")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import JSONResponse

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    # 放行登录接口和SSE流
    if request.url.path == f"{settings.API_V1_STR}/auth/login" or "/sync/stream" in request.url.path:
        return await call_next(request)

    # 仅保护API路由
    if not request.url.path.startswith(settings.API_V1_STR):
        return await call_next(request)

    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
    
    # 对于 EventSource, token可能在查询参数中
    if not token and 'token' in request.query_params:
        token = request.query_params['token']
        
    if token:
        try:
            payload = security.jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            request.state.user = payload.get("sub")
        except JWTError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})
    else:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    
    response = await call_next(request)
    return response



app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(api_router, prefix=settings.API_V1_STR)


# 挂载静态文件
STATIC_DIR = "static"
STATIC_ASSETS_DIR = os.path.join(STATIC_DIR, "assets")

# 确保静态文件目录存在
os.makedirs(STATIC_ASSETS_DIR, exist_ok=True)

app.mount("/assets", StaticFiles(directory=STATIC_ASSETS_DIR), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(request: Request, full_path: str):
    # API请求不应由此处理器处理
    if full_path.startswith("api/"):
        return Response("Not Found", status_code=404)

    # 尝试提供请求的静态文件
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 对于所有其他路径，返回index.html以支持SPA路由
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return Response("Frontend not found. Please build the frontend.", status_code=404)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
