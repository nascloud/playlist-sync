# Plex Playlist Sync 架构设计文档

## 系统架构概览

Plex Playlist Sync 采用前后端分离的架构设计，后端基于 FastAPI 构建，前端使用 React 实现。

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                           │
├─────────────────────────────────────────────────────────────┤
│                    React Web 应用 (web/)                    │
├─────────────────────────────────────────────────────────────┤
│                        API 接口层                           │
├─────────────────────────────────────────────────────────────┤
│                    FastAPI 后端 (backend/)                  │
├─────────────────────────────────────────────────────────────┤
│                    业务逻辑层 (Services)                     │
├─────────────────────────────────────────────────────────────┤
│                    数据访问层 (Models)                       │
├─────────────────────────────────────────────────────────────┤
│                    数据存储层 (SQLite)                       │
└─────────────────────────────────────────────────────────────┘
```

## 后端架构详解

### 目录结构
```
backend/
├── api/              # REST API 端点
├── core/             # 核心配置和数据库
├── models/           # 数据模型
├── schemas/          # Pydantic 数据模式
├── services/         # 核心业务逻辑
├── utils/            # 工具函数
└── main.py           # 应用入口
```

### 核心组件

#### 1. 主应用 (main.py)
- FastAPI 应用实例创建
- 路由注册
- 中间件配置
- 生命周期管理

#### 2. API 层 (api/)
```
api/
├── v1/
│   ├── api.py           # API 路由注册
│   └── endpoints/
│       ├── auth.py      # 认证相关接口
│       ├── tasks.py     # 任务管理接口
│       ├── download.py  # 下载管理接口
│       ├── settings.py  # 系统设置接口
│       └── logs.py      # 日志管理接口
```

#### 3. 服务层 (services/)
```
services/
├── playlist_service.py      # 歌单解析服务
├── download_service.py      # 下载管理服务
├── downloader_core.py       # 核心下载实现
├── download_queue_manager.py # 下载队列管理
├── auto_playlist_service.py # 智能播放列表服务
├── plex_service.py          # Plex 集成服务
├── task_service.py          # 任务管理服务
├── settings_service.py      # 设置管理服务
├── log_service.py           # 日志服务
└── sync_service.py          # 同步服务
```

#### 4. 数据层
```
models/
└── task.py              # 任务数据模型

schemas/
├── tasks.py             # 任务相关数据结构
├── task.py              # 单个任务数据结构
├── playlist.py          # 歌单相关数据结构
├── download.py          # 下载相关数据结构
├── download_schemas.py  # 下载数据结构扩展
├── settings.py          # 设置相关数据结构
├── log.py               # 日志相关数据结构
└── response.py          # 通用响应数据结构
```

#### 5. 核心层 (core/)
```
core/
├── config.py            # 应用配置
├── database.py          # 数据库连接
├── security.py          # 安全相关
└── logging_config.py    # 日志配置
```

#### 6. 工具层 (utils/)
```
utils/
├── scheduler.py         # 任务调度器
├── progress_manager.py  # 进度管理器
└── periodic_track_processor.py # 定期音轨处理器
```

## 数据库设计

### 核心表结构

#### 1. 任务表 (tasks)
存储歌单同步任务信息。

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,              -- 任务名称
    playlist_url VARCHAR NOT NULL,      -- 歌单URL
    platform VARCHAR NOT NULL,          -- 平台类型
    status VARCHAR,                     -- 任务状态
    last_sync_time DATETIME,            -- 最后同步时间
    cron_schedule VARCHAR,              -- 定时计划
    unmatched_songs TEXT,               -- 未匹配歌曲列表
    total_songs INTEGER,                -- 总歌曲数
    matched_songs INTEGER,              -- 已匹配歌曲数
    status_message TEXT,                -- 状态消息
    auto_download BOOLEAN,              -- 自动下载开关
    server_id INTEGER,                  -- 关联服务器ID
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(server_id) REFERENCES settings(id)
);
```

#### 2. 设置表 (settings)
存储 Plex 服务器配置。

```sql
CREATE TABLE settings (
    id INTEGER PRIMARY KEY,
    name VARCHAR NOT NULL,              -- 配置名称
    server_type VARCHAR NOT NULL,       -- 服务器类型
    url VARCHAR NOT NULL,               -- 服务器URL
    token VARCHAR NOT NULL              -- 访问令牌
);
```

#### 3. 下载设置表 (download_settings)
存储下载相关配置。

```sql
CREATE TABLE download_settings (
    id INTEGER PRIMARY KEY,
    key VARCHAR NOT NULL UNIQUE,        -- 配置键
    value VARCHAR NOT NULL,             -- 配置值
    log_retention_days INTEGER DEFAULT 30 -- 日志保留天数
);
```

#### 4. 下载会话表 (download_sessions)
存储下载会话信息。

```sql
CREATE TABLE download_sessions (
    id INTEGER PRIMARY KEY,
    task_id INTEGER NOT NULL,           -- 关联任务ID
    session_type VARCHAR NOT NULL,      -- 会话类型
    total_songs INTEGER NOT NULL,       -- 总歌曲数
    success_count INTEGER DEFAULT 0,    -- 成功数
    failed_count INTEGER DEFAULT 0,     -- 失败数
    status VARCHAR,                     -- 状态
    created_at DATETIME,
    updated_at DATETIME,
    completed_at DATETIME
);
```

#### 5. 下载队列表 (download_queue)
存储下载队列项。

```sql
CREATE TABLE download_queue (
    id INTEGER PRIMARY KEY,
    session_id INTEGER,                 -- 关联会话ID
    task_id INTEGER,                    -- 关联任务ID
    song_id VARCHAR,                    -- 歌曲ID
    title VARCHAR NOT NULL,             -- 标题
    artist VARCHAR NOT NULL,            -- 艺术家
    album VARCHAR,                      -- 专辑
    platform VARCHAR,                   -- 平台
    status VARCHAR,                     -- 状态
    quality VARCHAR,                    -- 音质
    retry_count INTEGER,                -- 重试次数
    error_message TEXT,                 -- 错误信息
    created_at DATETIME,
    updated_at DATETIME,
    FOREIGN KEY(session_id) REFERENCES download_sessions(id)
);
```

#### 6. 日志表 (logs)
存储系统日志。

```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY,
    task_id INTEGER,                    -- 关联任务ID
    timestamp VARCHAR,                  -- 时间戳
    level VARCHAR,                      -- 日志级别
    message TEXT                        -- 日志消息
);
```

## 服务间交互

### 1. 同步流程
```
用户请求同步 → TaskService 创建任务 → PlaylistService 解析歌单 
→ TaskService 更新任务状态 → (可选) DownloadService 下载缺失歌曲
→ AutoPlaylistService 处理新音乐 → PlexService 更新播放列表
```

### 2. 下载流程
```
用户触发下载 → DownloadService 创建下载会话 
→ DownloadQueueManager 管理队列 → DownloaderCore 执行下载
→ AutoPlaylistService 处理新音乐 → PlexService 更新播放列表
```

### 3. 智能播放列表流程
```
定时触发/下载完成 → AutoPlaylistService 查找新音乐
→ 匹配到任务缺失列表 → PlexService 更新播放列表
→ TaskService 更新任务状态
```

## 并发处理

### 1. 异步处理
- 使用 Python asyncio 实现异步操作
- FastAPI 原生支持异步路由
- 数据库操作通过线程池执行

### 2. 并发控制
- 下载并发数限制（默认3个）
- QQ音乐API请求并发限制（避免触发风控）
- 数据库连接池管理

## 安全设计

### 1. 认证授权
- JWT Token 认证
- 密码加密存储
- API访问控制

### 2. 数据安全
- 敏感信息加密存储（Plex Token、下载器API Key）
- 数据库访问权限控制
- 输入验证和过滤

### 3. 通信安全
- HTTPS 支持
- 可配置的SSL验证
- API请求签名（可选）

## 性能优化

### 1. 缓存机制
- QQ音乐歌曲详情缓存
- Plex音乐库缓存
- 配置信息缓存

### 2. 批量处理
- 批量歌单解析
- 批量下载队列处理
- 批量Plex操作

### 3. 异步执行
- 异步HTTP请求
- 异步文件操作
- 异步数据库操作

## 部署架构

### 1. 单机部署
```
┌─────────────────────────────────────┐
│           Docker 容器                │
├─────────────────────────────────────┤
│  Nginx (反向代理)                   │
├─────────────────────────────────────┤
│  FastAPI 后端 + React 前端          │
├─────────────────────────────────────┤
│  SQLite 数据库                      │
└─────────────────────────────────────┘
```

### 2. 分布式部署（规划）
```
┌─────────────────┐    ┌─────────────────┐
│   负载均衡器     │    │   数据库集群     │
└─────────────────┘    └─────────────────┘
        │                       │
┌─────────────────┐    ┌─────────────────┐
│   Web 服务器1   │    │   文件存储       │
├─────────────────┤    └─────────────────┘
│   Web 服务器2   │
├─────────────────┤
│   Web 服务器N   │
└─────────────────┘
```

## 监控和日志

### 1. 日志系统
- 结构化日志记录
- 多级别日志输出
- 日志轮转和清理

### 2. 监控指标
- 任务执行状态
- 下载成功率
- API响应时间
- 系统资源使用

### 3. 告警机制
- 任务失败告警
- 下载失败告警
- 系统异常告警

## 扩展性设计

### 1. 插件化架构
- 平台适配器模式
- 下载器插件化
- 存储后端扩展

### 2. 配置驱动
- 环境变量配置
- 配置文件支持
- 动态配置更新

### 3. 微服务准备
- 服务解耦设计
- API网关集成
- 消息队列支持