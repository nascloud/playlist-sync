# 智能播放列表功能设计文档

## 概述

本文档描述了 Plex Playlist Sync 项目中新添加的智能播放列表功能。该功能旨在自动化地将新下载或手动添加的音乐文件归类到对应的 Plex 播放列表中，提升用户体验。

## 功能特性

### 1. 下载后自动归类
- **触发时机**：当一个下载任务完成时。
- **处理流程**：
  1. 触发 Plex 服务器扫描新文件。
  2. 获取最近添加的音轨。
  3. 将新音轨与对应任务的缺失歌曲列表进行匹配。
  4. 将匹配成功的音轨添加到任务对应的 Plex 播放列表中。
  5. 更新任务状态，从缺失列表中移除已匹配的歌曲。

### 2. 定期扫描归类
- **触发时机**：通过调度器每30分钟执行一次。
- **处理流程**：
  1. 获取最近1小时内添加的音轨。
  2. 将新音轨与所有任务的缺失歌曲列表进行匹配。
  3. 将匹配成功的音轨添加到对应任务的 Plex 播放列表中。
  4. 更新所有相关任务的状态。

## 核心组件

### AutoPlaylistService
- **职责**：核心服务，负责智能地将新音乐添加到对应的 Plex 播放列表中。
- **主要方法**：
  - `process_tracks_for_task`: 处理特定任务下载后的新音轨。
  - `process_newly_added_tracks`: 处理定期扫描发现的新音轨。
  - `_match_track_to_missing_song`: 将 Plex 音轨与缺失歌曲进行匹配。

### PlexService 增强
- **新增方法**：
  - `find_newly_added_tracks`: 查找自指定时间以来新添加的音轨。
  - `scan_and_refresh`: 触发 Plex 扫描新文件。

### TaskService 增强
- **新增方法**：
  - `remove_matched_songs_from_task`: 从任务的缺失歌曲列表中移除已匹配的歌曲。

## 集成与流程

### 下载后处理流程
1. `DownloadQueueManager` 在下载完成后调用 `AutoPlaylistService.process_tracks_for_task`。
2. `AutoPlaylistService` 获取 Plex 音乐库并查找新添加的音轨。
3. 匹配新音轨与任务缺失列表。
4. 更新 Plex 播放列表。
5. 更新任务状态。

### 定期扫描流程
1. `TaskScheduler` 每30分钟调用 `periodic_new_track_processing`。
2. `periodic_new_track_processing` 调用 `AutoPlaylistService.process_newly_added_tracks`。
3. `AutoPlaylistService` 获取 Plex 音乐库并查找新添加的音轨。
4. 匹配新音轨与所有任务的缺失列表。
5. 更新所有相关的 Plex 播放列表。
6. 更新所有相关任务的状态。

## 配置

该功能无需特殊配置，它会自动工作。定期扫描任务默认每30分钟执行一次。

## 未来优化

1. **可配置的扫描间隔**：允许用户自定义定期扫描的频率。
2. **更复杂的匹配规则**：支持基于文件路径、标签等更多信息的匹配规则。
3. **Webhook 支持**：支持通过 Webhook 触发处理流程。