from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from api.v1.api import api_router
from api.v1.endpoints import auth
from core.config import settings
from utils.scheduler import scheduler
from services.download_service import download_service
from core.logging_config import setup_logging
from core import security
from jose import JWTError


import logging

# ... (其他导入)

logger = logging.getLogger(__name__)

def check_security_prerequisites():
    """检查并确保关键的安全环境变量已设置。"""
    missing_vars = []
    if not settings.auth.SECRET_KEY:
        missing_vars.append("SECRET_KEY")
    if not settings.auth.APP_PASSWORD:
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
    scheduler.start()
    await download_service.initialize_downloader()
    yield
    # 关闭时的清理代码
    scheduler.shutdown()

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

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if not request.url.path.startswith(f"{settings.API_V1_STR}/"):
        return await call_next(request)
    
    # 放行登录接口和SSE流
    if request.url.path == f"{settings.API_V1_STR}/auth/login" or "/sync/stream" in request.url.path:
        return await call_next(request)

    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
    
    # 对于 EventSource, token可能在查询参数中
    if not token and 'token' in request.query_params:
        token = request.query_params['token']
        
    if token:
        try:
            payload = security.jwt.decode(token, settings.auth.SECRET_KEY, algorithms=[settings.auth.ALGORITHM])
            request.state.user = payload.get("sub")
        except JWTError:
            return Response("Invalid token", status_code=401)
    else:
        return Response("Not authenticated", status_code=401)
    
    response = await call_next(request)
    return response


app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(api_router, prefix=settings.API_V1_STR)



@app.get("/")
async def root():
    return {"message": "Plex Music Sync API is running."}

@app.get("/api/health")
async def health_check():
    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
