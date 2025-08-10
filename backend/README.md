# Plex Music Sync API (Python版本)

这是Plex音乐播放列表同步工具的Python后端实现，使用FastAPI框架构建。

## 功能特性

- 使用FastAPI提供高性能的RESTful API
- 集成plexapi库与Plex服务器交互
- 支持网易云音乐和QQ音乐播放列表解析
- 定时同步任务调度
- SQLite数据库存储配置和任务信息
- 自动API文档生成（Swagger UI / ReDoc）

## 技术栈

- **FastAPI**: 现代、快速（高性能）的Python Web框架
- **plexapi**: 非官方的Python Plex API库
- **SQLite**: 轻量级数据库
- **APScheduler**: 任务调度库
- **httpx**: 异步HTTP客户端

## 安装和运行

### 本地开发

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 启动开发服务器：
   ```bash
   uvicorn main:app --reload
   ```

   服务器将在 `http://localhost:3000` 上运行。

### 环境变量

- `SECRET_KEY`: 用于加密Plex令牌的密钥
- `PORT`: 服务器端口（默认：3000）

## API文档

启动服务器后，可以通过以下URL访问自动生成的API文档：

- Swagger UI: http://localhost:3000/docs
- ReDoc: http://localhost:3000/redoc

## 项目结构

```
api/
├── main.py                 # 应用入口
├── core/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   └── security.py        # 安全相关功能
├── models/                 # 数据模型
├── schemas/                # Pydantic模型（请求/响应）
├── api/                    # API路由
│   └── v1/                # API v1版本
│       ├── api.py         # API路由聚合
│       └── endpoints/     # API端点
├── services/               # 业务逻辑层
├── utils/                  # 工具函数
└── tests/                  # 测试文件
```

## Docker部署

使用Docker运行：

```bash
docker build -t plex-music-sync-api .
docker run -p 3000:3000 plex-music-sync-api
```

或使用docker-compose（在项目根目录）：

```bash
docker-compose up
```