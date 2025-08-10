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

### 安全配置

在首次启动应用前，您必须设置以下环境变量以确保应用安全：

- `SECRET_KEY`: 用于保护会话和 token 的一个长而随机的字符串。您可以使用以下命令生成一个安全的密钥：
  ```bash
  openssl rand -hex 32
  ```
- `APP_PASSWORD`: 用于登录 Web 界面的密码。

您可以将这些变量添加到后端目录下的一个 `.env` 文件中：

```
# backend/.env
SECRET_KEY=您生成的随机字符串
APP_PASSWORD=您选择的强密码
```

> **重要提示**: 没有这些配置，应用将无法启动。

### 后端设置

1.  克隆仓库:
    ```bash
    git clone https://your-repository-url/plex-playlist-sync.git
    cd plex-playlist-sync/backend
    ```

2.  使用 uv 安装 Python 依赖:
    ```bash
    uv sync
    ```

### 前端设置

1.  进入 `web` 目录:
    ```bash
    cd ./web
    ```

2.  安装 Node.js 依赖:
    ```bash
    npm install
    ```

## 使用方法

### 启动后端服务

在 `backend` 目录下，运行以下命令启动 FastAPI 服务:

```bash
uv run main.py
```

API 将在 `http://localhost:3000` 上可用。

### 启动前端应用

在 `web` 目录下，运行以下命令启动 React 开发服务器:

```bash
npm run dev
```

Web 界面将在 `http://localhost:5173` 上可用。

### 使用 Docker

使用 Docker Compose 运行整个应用:

```bash
docker-compose up --build
```

这将同时启动后端和前端服务。

## 贡献指南

欢迎参与贡献！如果您有任何想法、建议或发现 bug，请随时开启一个 Issue 或提交 Pull Request。

1.  Fork 本仓库。
2.  创建您的新分支 (`git checkout -b feature/AmazingFeature`)。
3.  提交您的更改 (`git commit -m 'Add some AmazingFeature'`)。
4.  将代码推送到您的分支 (`git push origin feature/AmazingFeature`)。
5.  开启一个 Pull Request。

## 许可证

本项目采用 MIT 许可证。详情请参阅 `LICENSE` 文件。
