# QQ音乐歌单解析增强功能说明

## 功能概述

QQ音乐歌单解析功能已增强，现在可以在解析完歌单后自动从歌曲详情接口补全缺失的信息，特别是专辑信息。

## 实现细节

### 1. 歌曲详情接口集成

新增了`fetch_qq_song_detail`方法，用于通过歌曲MID获取详细的歌曲信息：
- 使用QQ音乐的`fcg_play_single_song.fcg`接口
- 支持通过`songs_mid`参数获取单首歌曲的详细信息
- 提取专辑名称等详细信息

### 2. 信息补全机制

在`fetch_qq_playlist`方法中增加了自动补全机制：
1. 解析歌单时，首先从歌单接口获取基础信息
2. 识别缺少专辑信息的歌曲（专辑字段为"未知专辑"）
3. 对这些歌曲并发调用歌曲详情接口补全信息
4. 使用信号量限制并发数，避免对服务器造成过大压力

### 3. 错误处理

- 对歌曲详情接口的调用进行了完善的错误处理
- 即使部分歌曲详情获取失败，也不会影响整体解析流程
- 记录详细的日志信息，便于问题排查

## 使用效果

增强前：
```
1. 标题: 破碎的自己
   艺术家: LBI利比（时柏尘）, 前男友
   专辑: 未知专辑
   歌曲ID: 563268487-000itqkA4Dqusv
```

增强后：
```
1. 标题: 破碎的自己
   艺术家: LBI利比（时柏尘）, 前男友
   专辑: 破碎的自己
   歌曲ID: 563268487-000itqkA4Dqusv
```

## 技术实现

### 核心代码位置
- `backend/services/playlist_service.py`

### 主要方法
1. `fetch_qq_song_detail(songmid)` - 获取单首歌曲详情
2. `fetch_qq_playlist(playlist_id)` - 解析歌单并自动补全信息

### 并发控制
使用`asyncio.Semaphore(10)`限制并发请求数，避免对QQ音乐服务器造成过大压力。

## 测试验证

相关的测试脚本：
- `backend/test_qq_playlist.py` - 基础功能测试
- `backend/test_qq_playlist_enhanced.py` - 增强功能测试
- `backend/test_qq_song_detail.py` - 歌曲详情接口测试
- `backend/test_qq_detail_parsing.py` - 歌曲详情解析测试