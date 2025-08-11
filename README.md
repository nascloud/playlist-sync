# Plex Playlist Sync

Plex Playlist Sync 是一个用于将网易云音乐、QQ音乐等外部音乐平台的歌单自动同步到您的 Plex 媒体服务器的工具。本项目由一个 FastAPI 后端和一个 React 前端组成。

## 功能特性

- 支持从网易云音乐和QQ音乐同步歌单。
- 自动、定时同步播放列表。
- 提供 Web 界面，方便管理。
- 安全存储您的 Plex 凭据。

## 项目结构

```
plex-playlist-sync/
├── backend/              # FastAPI 后端应用
├── web/                  # React 前端应用
├── docs/                 # 项目文档
└── docker-compose.yml    # Docker Compose 配置
```

## 安装指南

### 环境准备

- Git
- Python 3.9+ 及 [uv](https://github.com/astral-sh/uv)
- Node.js 和 npm
- Docker (用于容器化部署)

### 安全与环境配置

在首次启动应用前，您必须配置必要的环境变量。我们提供了一个模板文件 `backend/.env.example` 来帮助您完成配置。

1.  **创建您的 `.env` 文件**:
    将模板文件复制一份，并重命名为 `.env`：
    ```bash
    cp backend/.env.example backend/.env
    ```

2.  **编辑 `.env` 文件**:
    打开 `backend/.env` 文件，并根据指引填入您的个人信息。

    - `SECRET_KEY`: 用于保护会话和 token 的一个长而随机的字符串。您可以使用以下命令生成一个安全的密钥：
      ```bash
      openssl rand -hex 32
      ```
    - `APP_PASSWORD`: 用于登录 Web 界面的密码。
    - `PLEX_URL`: 您的 Plex 服务器的完整 URL。
    - `PLEX_TOKEN`: 您的 Plex 访问令牌。
    - `DOWNLOADER_API_KEY`: 下载器所需的 API 密钥。
    - `DOWNLOAD_PATH`: 下载文件的存放路径。

> **重要提示**: 必须将 `SECRET_KEY` 和 `APP_PASSWORD` 填写完整，否则应用将无法启动。

### 后端设置

1.  **进入 `backend` 目录**:
    ```bash
    cd backend
    ```

2.  **安装 Python 依赖**:
    ```bash
    uv sync
    ```

3.  **数据库迁移**:
    在首次启动或数据库模型更新后，运行迁移命令：
    ```bash
    uv run alembic upgrade head
    ```

### 前端设置

1.  **进入 `web` 目录**:
    ```bash
    cd web
    ```

2.  **安装 Node.js 依赖**:
    ```bash
    npm install
    ```

## 使用方法

### 启动开发服务器

- **后端服务** (在 `backend` 目录下):
  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 3001
  ```
  API 将在 `http://localhost:3001` 上可用。

- **前端应用** (在 `web` 目录下):
  ```bash
  npm run dev
  ```
  Web 界面将在 `http://localhost:5173` 上可用。

### 使用 Docker

使用 Docker Compose 可以一键启动整个应用:

```bash
docker-compose up --build
```
> **注意**: 请确保您已经在 `backend/.env` 文件中完成了所有必要的配置。Docker Compose 会自动加载这些配置。


## 贡献指南

欢迎参与贡献！如果您有任何想法、建议或发现 bug，请随时开启一个 Issue 或提交 Pull Request。

1.  Fork 本仓库。
2.  创建您的新分支 (`git checkout -b feature/AmazingFeature`)。
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4.  将代码推送到您的分支 (`git push origin feature/AmazingFeature`)。
5.  开启一个 Pull Request。

## 许可证

本项目采用 MIT 许可证。详情请参阅 `LICENSE` 文件。
