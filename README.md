# Plex Playlist Sync

**Plex Playlist Sync** 是一个简单易用的音乐同步工具，可以自动将网易云音乐、QQ音乐等平台的歌单同步到你的 Plex 媒体服务器。你只需配置一次，之后它会自动帮你下载和整理音乐到正确的播放列表中。

## 🎵 功能介绍

### 🔄 歌单同步
- **支持多个音乐平台**：网易云音乐、QQ音乐
- **自动同步**：设置好后，系统会自动更新你的歌单
- **智能补全**：自动查找缺失的歌曲信息，如专辑封面等

### 📥 智能下载
- **多种下载方式**：
  - 一键下载所有缺失歌曲
  - 选择下载单首歌曲
  - 自动下载（同步后自动开始）
- **下载队列管理**：支持暂停、重试等功能
- **防过载**：智能控制下载速度，避免影响你的网络

### 🗂️ 智能播放列表
- **自动分类**：新下载的音乐会自动归类到对应播放列表
- **双重保障**：下载完成后立即处理，或定期扫描确保不遗漏

## 🚀 快速开始

最简单的使用方式是使用预构建的 Docker 镜像，只需要几个步骤即可完成安装和配置：

### 第一步：安装 Docker

1. **Windows / Mac 用户**：下载并安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. **Linux 用户**：安装 Docker 
   - Ubuntu/Debian: `sudo apt install docker.io`
   - CentOS/RHEL: `sudo yum install docker`

> **注意**：安装完成后请重启电脑，确保 Docker 服务已启动。

### 第二步：创建项目文件夹

创建一个新的文件夹（例如：D:/playlist-sync），然后在该文件夹内创建一个名为 `docker-compose.yml` 的文件，内容如下：

```yaml
services:
  playlist_sync-app:
    image: econome/playlist-sync-app
    container_name: playlist_sync-app
    dns:
      - 223.5.5.5
      - 114.114.114.114
    ports:
      - "5173:3001"
    restart: always
    networks:
      - app-network
    volumes:
      # 挂载数据库文件以实现数据持久化
      - ./data:/usr/src/app/data
      # 挂载日志目录
      - ./logs:/usr/src/app/logs
      # 挂载下载目录
      - ./downloads:/usr/src/app/Downloads
    env_file:
      - ./.env

networks:
  app-network:
    driver: bridge
```

> **注意**：请根据你的实际路径修改上面的下载目录路径。示例中使用的是 `/vol3/1000/Media/音乐/plexdownloads`，请将其修改为你想存放音乐的路径。

### 第三步：配置设置

1. 在项目文件夹中创建一个名为 `.env` 的文件（注意前面有个点）
2. 用文本编辑器（如记事本）打开 `.env` 文件
3. 添加并修改以下配置：

```
PLEX_URL=你的Plex服务器地址
PLEX_TOKEN=你的Plex访问令牌
APP_PASSWORD=设置一个登录密码
DOWNLOAD_PATH=Downloads
```

详细说明：
   - `PLEX_URL`: 你的 Plex 服务器地址（例如：http://192.168.1.100:32400）
   - `PLEX_TOKEN`: 你的 Plex 访问令牌（获取方法见下方 "重要配置说明"）
   - `APP_PASSWORD`: 设置一个登录密码（例如：mypass123）
   - `DOWNLOAD_PATH`: Docker容器内的下载路径（保持默认值即可）

### 第四步：启动服务

1. 打开命令行工具：
   - Windows 用户：按 Win+R，输入 `cmd`，回车
   - Mac/Linux 用户：打开终端

2. 切换到项目目录（例如，如果项目在 D:/playlist-sync）：
   ```bash
   cd D:/playlist-sync
   ```

3. 启动服务（首次运行会下载镜像，可能需要几分钟）：
   ```bash
   docker-compose up -d
   ```

4. 等待服务启动完成，访问 `http://localhost:5173` 即可开始使用

> **小提示**：如果不想看实时日志，使用 `docker-compose up -d`（后台运行）；如果想看实时日志，使用 `docker-compose up`

### 第五步：开始同步

1. 打开浏览器，访问 `http://localhost:5173`
2. 使用你在 `.env` 中设置的密码登录
3. 添加歌单链接（从网易云音乐或 QQ 音乐复制分享链接）
4. 点击同步，系统会自动查找并下载缺失的歌曲
5. 等待同步完成，音乐将自动出现在你的 Plex 播放列表中

## 🔧 重要配置说明

### 如何获取 Plex Token
1. 在浏览器中打开你的 Plex 服务器地址（例如：http://192.168.1.100:32400）
2. 登录到 Plex Web 界面
3. 按 F12 打开浏览器的开发者工具
4. 点击 Network（网络）标签
5. 刷新页面，在请求列表中找到任意一个请求，查看 Headers（请求头）
6. 找到 "X-Plex-Token" 或 "X-Plex-Token="，复制后面的值

### Docker 数据持久化
- 数据库文件和下载的音乐将保存在项目目录下的 `./data` 和 `./logs` 中
- 即使删除容器，数据也不会丢失
- 备份时只需备份整个项目目录

### 下载路径映射
- 容器内的 `/usr/src/app/Downloads` 目录会映射到你在 `docker-compose.yml` 中指定的主机路径
- 确保映射的主机路径存在且有写入权限

## ❓ 常见问题解答

### Q: 为什么有些歌曲下载不了？
A: 可能是因为：
- 歌曲在源平台已下架
- 版权问题，无法下载
- 网络连接问题，稍后重试即可

### Q: 同步后音乐没出现在 Plex 中？
A: 请检查：
- Plex 服务器是否正常运行
- 音乐下载路径是否正确设置（需要设置为Plex库的音乐目录）
- Plex 是否开启了自动扫描功能（在 Plex 设置中启用）

### Q: 如何停止服务？
A: 在项目目录下运行：
```bash
docker-compose down
```

### Q: 如何更新到最新版本？
A: 
1. 停止当前服务：`docker-compose down`
2. 拉取最新镜像：`docker pull econome/playlist-sync-app`
3. 重新启动服务：`docker-compose up -d`

### Q: 如何查看服务日志？
A: 在项目目录下运行：
```bash
docker-compose logs -f
```

### Q: 端口 5173 被占用怎么办？
A: 修改 `docker-compose.yml` 文件中的端口映射，例如改为 "5174:3001"，然后通过 `http://localhost:5174` 访问。

## 🤝 如何寻求帮助

如果你在使用过程中遇到问题：

1. 查看 [GitHub Issues](https://github.com/nascloud/playlist-sync/issues) 是否有类似问题
2. 如果没有找到解决方案，可以创建一个新的 Issue
3. 描述问题时请提供详细的错误信息和复现步骤

## 📄 开源许可证

本项目采用 MIT 许可证，欢迎使用和修改。