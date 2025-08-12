# Plex Playlist Sync

Plex Playlist Sync 是一个强大的音乐同步工具，可将网易云音乐、QQ音乐等平台的歌单自动同步到您的 Plex 媒体服务器。该工具不仅支持歌单同步，还提供智能下载和播放列表管理功能。

## 🌟 核心功能

### 歌单同步
- **多平台支持**：网易云音乐、QQ音乐
- **定时同步**：可配置的定时任务，自动保持歌单更新
- **智能解析**：自动补全缺失的歌曲信息（如专辑信息）

### 智能下载
- **三种下载方式**：
  - 一键下载全部缺失歌曲
  - 单个歌曲下载
  - 自动下载（同步后自动开始）
- **智能信息补全**：在下载阶段自动补全歌曲信息，避免触发平台风控
- **队列管理**：完整的下载队列管理，支持暂停、重试等操作
- **并发控制**：智能并发下载，避免系统过载

### 智能播放列表
- **自动归类**：新下载或手动添加的音乐自动归类到对应播放列表
- **双重触发**：
  - 下载完成后立即处理
  - 定期扫描（默认每30分钟）
- **智能匹配**：优化的字符串标准化和权重分配算法

## 🏗️ 项目架构

```
plex-playlist-sync/
├── backend/              # FastAPI 后端应用
│   ├── api/              # REST API 端点
│   ├── core/             # 核心配置和数据库
│   ├── models/           # 数据模型
│   ├── schemas/          # Pydantic 数据模式
│   ├── services/         # 核心业务逻辑
│   ├── utils/            # 工具函数
│   └── main.py           # 应用入口
├── web/                  # React 前端应用
├── docs/                 # 项目文档
└── docker-compose.yml    # Docker 部署配置
```

## 🚀 快速开始

### 环境要求
- Git
- Python 3.9+ 及 [uv](https://github.com/astral-sh/uv)
- Node.js 和 npm
- Docker (可选，用于容器化部署)

### 安装步骤

1. **克隆项目**：
   ```bash
   git clone https://github.com/nascloud/playlist-sync.git
   cd playlist-sync
   ```

2. **配置环境变量**：
   ```bash
   cp backend/.env.example backend/.env
   # 编辑 backend/.env 文件，填入必要配置
   ```

3. **后端设置**：
   ```bash
   cd backend
   uv sync
   uv run alembic upgrade head
   ```

4. **前端设置**：
   ```bash
   cd web
   npm install
   ```

### 启动应用

#### 开发模式
```bash
# 后端 (在 backend 目录)
uvicorn main:app --reload --host 0.0.0.0 --port 3001

# 前端 (在 web 目录)
npm run dev
```

#### 生产模式 (Docker)
```bash
docker-compose up --build
```

## 🛠️ 核心服务

### PlaylistService
负责从音乐平台解析歌单信息，支持：
- 网易云音乐歌单解析
- QQ音乐歌单解析（含信息补全）

### DownloadService
提供完整的下载功能：
- 三种下载触发方式
- 并发下载控制
- 下载队列管理
- 错误处理和重试机制

### AutoPlaylistService
智能播放列表管理：
- 新音乐自动归类
- 智能匹配算法
- 双重触发机制

### PlexService
与 Plex 媒体服务器交互：
- 音乐库管理
- 播放列表创建/更新
- 媒体扫描触发

## 📊 数据模型

### 任务管理 (tasks)
- 歌单同步任务
- 定时调度配置
- 同步状态跟踪

### 下载管理
- 下载设置 (download_settings)
- 下载队列 (download_queue)
- 下载会话 (download_sessions)

## 🔧 配置说明

### 必需配置
- `SECRET_KEY`：应用安全密钥
- `APP_PASSWORD`：Web界面登录密码
- `PLEX_URL`：Plex服务器地址
- `PLEX_TOKEN`：Plex访问令牌

### 下载配置
- `DOWNLOADER_API_KEY`：下载器API密钥
- `DOWNLOAD_PATH`：下载文件存储路径
- `preferred_quality`：首选音质
- `max_concurrent_downloads`：最大并发下载数

## 🎯 使用指南

### 1. 创建同步任务
1. 在Web界面添加新任务
2. 输入歌单URL
3. 配置同步计划

### 2. 下载缺失歌曲
1. 查看任务详情中的缺失歌曲列表
2. 选择下载方式：
   - 点击"下载全部缺失"按钮
   - 点击单个歌曲的"下载"按钮
   - 启用自动下载功能

### 3. 智能播放列表
系统会自动将新下载的音乐归类到对应播放列表，无需手动操作。

## 📚 技术文档

详细技术文档请参阅 [docs](./docs) 目录：

- [智能播放列表功能设计](./docs/auto_playlist_feature.md)
- [下载功能完整设计](./docs/download_feature_design.md)
- [QQ音乐歌单解析增强](./docs/qq_playlist_enhancement.md)
- [QQ音乐信息补全](./docs/qq_info_enrichment_during_download.md)
- [字符串标准化和匹配优化](./docs/string_normalization_and_matching_fix.md)

## 🤝 贡献指南

欢迎参与贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](./LICENSE) 文件。

## 🆘 支持

如遇到问题，请：
1. 查看 [Issues](https://github.com/nascloud/playlist-sync/issues)
2. 创建新的 Issue 描述问题
3. 提供详细的错误信息和复现步骤