# 低质量音频文件检测与处理策略

本文档描述了在 `backend/services/downloader_core.py` 中处理下载到的低质量歌曲或广告文件的策略，相关功能已在代码中实现。

## 1. 问题描述

在从第三方API下载音乐时，可能会遇到以下问题：

- 下载到的音频文件质量低于预期（如比特率过低）。
- 下载到的文件实际上是广告片段或歌曲试听版。
- API返回了错误的或不完整的文件。

这些问题会严重影响用户体验，因此需要有效的检测和处理机制。

## 2. 已实现的解决方案

功能已在 `backend/services/downloader_core.py` 和新增的 `backend/services/low_quality_detector.py` 中实现。

### 2.1 文件内容分析 (File Content Analysis)

在文件下载完成后，但在正式处理（如嵌入ID3标签）之前，对文件进行一系列自动化检查。

**检查点**:

1. 文件大小 (File Size)

   :

   - **原理**: 合格的音频文件通常具有一定的最小大小。过小的文件（例如小于3MB）很可能是广告或质量极差的音频。
   - **实现**: 使用 `os.path.getsize()` 获取下载文件的大小，并与预设的最小阈值进行比较。
   - **阈值**: 设定为 `2.0 MB`。

2. 文件时长 (Duration)

   :

   - **原理**: 正常歌曲时长通常在几分钟以上，而广告或试听片段往往很短（例如少于90秒）。
   - **实现**: 使用 `mutagen` 库读取音频文件的元数据，获取其时长（秒）。
   - **阈值**: 设定为 `90.0` 秒。

**实现流程**:

- 创建 `backend/services/low_quality_detector.py` 模块，其中包含 `is_file_acceptable(file_path: str, log: logging.Logger) -> bool` 方法。
- 该方法依次执行上述检查。
- 如果任何一项检查失败，则认为文件质量不合格，返回 `False`。
- 如果所有检查都通过，则认为文件合格，返回 `True`。
- 在 `MusicDownloader.download_song` 方法中，在嵌入ID3标签之前调用 `is_file_acceptable`。
- 如果文件不合格，会被立即删除，并抛出 `APIError` 异常，使下载任务失败。

### 2.2 自动重试与备选方案 (Automatic Retry & Fallback)

当检测到下载的文件质量不合格，或下载过程中发生错误时，系统会自动尝试其他下载源。

**实现策略**:

1. **扩展搜索结果**:
   - 修改 `DownloaderCore._find_song_id` 方法，使其不仅返回最佳匹配项，而是返回一个包含多个高匹配度候选的列表（所有匹配分>70的结果）。
   - 返回值从 `(song_id, platform)` 变为 `(song_id, platform, candidates_list)`。
2. **备选下载队列**:
   - 在 `DownloaderCore.download` 方法中，当首选下载项（无论是用户提供的ID还是搜索到的最佳匹配）失败或被标记为低质量后，系统将遍历由 `_find_song_id` 返回的候选列表。
   - 按照匹配分数从高到低的顺序，依次尝试备选的 `song_id` 和 `platform` 组合进行下载。
   - 每次尝试后，都需对新下载的文件执行 `文件内容分析` 流程（即 `is_file_acceptable` 检查）。

### 2.3 专用日志记录 (Dedicated Logging)

为了便于监控和分析低质量问题，所有被识别为低质量或广告的文件信息将被记录到一个独立的、结构化的日志文件中。

**实现细节**:

1. **独立 Logger**:
   - 在 `backend/services/low_quality_detector.py` 中创建一个名为 `low_quality_downloads` 的专用 `logging.Logger` 实例。
   - 为该 logger 配置一个 `logging.FileHandler`，输出到 `logs/low_quality_downloads.log` 文件。
   - 将该 logger 的 `propagate` 属性设置为 `False`，防止日志混入主应用日志。
2. **JSON 格式**:
   - 为 `low_quality_downloads` logger 配置一个 `logging.Formatter`，使用 JSON 格式记录日志。
   - 使用 `python-json-logger` 库。
3. **记录内容**:
   - 当 `is_file_acceptable` 方法检测到文件不合格时，除了在主日志中记录警告外，还会调用 `low_quality_logger` 记录一条结构化的 JSON 日志。
   - 日志内容包含时间戳、日志级别、消息以及结构化数据（如文件路径、文件名、检查类型、文件大小、时长、平台、歌曲ID、元数据等）。