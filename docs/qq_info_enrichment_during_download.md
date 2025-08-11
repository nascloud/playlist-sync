# QQ音乐信息补全功能说明（下载阶段实现）

## 功能概述

QQ音乐信息补全功能已调整实现方式，现在在下载阶段检查并补全缺失的歌曲信息，避免在歌单解析阶段频繁调用接口触发风控。

## 实现细节

### 1. 实现位置调整

将信息补全功能从歌单解析阶段移到了下载阶段：
- **原方案**：在`PlaylistService.fetch_qq_playlist`中解析完歌单后立即补全信息
- **新方案**：在`DownloaderCore.download`中下载前检查并补全信息

### 2. 核心功能

#### 2.1 歌曲详情获取
- 方法：`DownloaderCore._fetch_qq_song_detail(songmid, session_logger)`
- 使用QQ音乐的`fcg_play_single_song.fcg`接口
- 支持缓存机制，避免重复请求同一首歌曲的详情
- 完善的错误处理和日志记录

#### 2.2 信息补全逻辑
- 方法：`DownloaderCore._enrich_track_info(item, session_logger)`
- 检查条件：
  - 歌曲平台为QQ音乐
  - 专辑信息为空或为"未知专辑"
  - 存在有效的song_id（包含songmid）
- 补全内容：主要补全专辑信息
- 对象保持：返回与输入相同类型的对象

### 3. 缓存机制

为了避免重复请求，实现了一个简单的缓存机制：
```python
# 在DownloaderCore类中
self._qq_song_detail_cache: Dict[str, Dict] = {}

# 在_fetch_qq_song_detail方法中
if songmid in self._qq_song_detail_cache:
    # 从缓存返回
    return self._qq_song_detail_cache[songmid]
# 请求API并缓存结果
self._qq_song_detail_cache[songmid] = song_data
```

### 4. 风控防护

通过以下方式减少风控风险：
1. **时机调整**：将批量信息补全分散到下载阶段，避免集中请求
2. **缓存机制**：对已获取的歌曲详情进行缓存，避免重复请求
3. **按需获取**：只对确实缺少信息的歌曲进行详情获取

## 技术实现

### 核心代码位置
- `backend/services/downloader_core.py`

### 主要方法
1. `DownloaderCore._fetch_qq_song_detail(songmid, session_logger)` - 获取QQ音乐歌曲详情
2. `DownloaderCore._enrich_track_info(item, session_logger)` - 补全歌曲信息
3. `DownloaderCore.download(item, ...)` - 下载方法中集成信息补全

### 数据结构
- 使用歌曲ID中的songmid部分获取详情：`"songid-songmid"` → 提取 `songmid`

## 使用效果

处理流程：
1. 用户解析QQ音乐歌单（快速，不补全信息）
2. 用户发起下载任务
3. 下载器检查歌曲信息完整性
4. 如发现信息缺失（如专辑为"未知专辑"），调用QQ音乐详情接口补全
5. 使用补全后的信息进行下载和标签嵌入

示例：
```
原始信息:
  标题: 破碎的自己
  艺术家: LBI利比（时柏尘）, 前男友
  专辑: 未知专辑
  平台: qq
  歌曲ID: 563268487-000itqkA4Dqusv

补全后:
  标题: 破碎的自己
  艺术家: LBI利比（时柏尘）, 前男友
  专辑: 破碎的自己
  平台: qq
  歌曲ID: 563268487-000itqkA4Dqusv
```

## 测试验证

相关的测试脚本：
- `backend/test_qq_detail_api.py` - QQ音乐歌曲详情接口测试
- `backend/test_download_enrichment.py` - 下载阶段信息补全流程测试

## 优势对比

| 方案 | 优势 | 劣势 |
|------|------|------|
| 歌单解析阶段补全 | 一次性获取所有信息，下载时信息完整 | 容易触发风控，响应速度慢 |
| 下载阶段补全 | 避免风控，解析速度快，按需获取 | 下载时可能需要额外请求 |

新方案在保证功能完整性的同时，显著降低了触发风控的风险，提升了用户体验。