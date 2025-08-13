# PlexService 优化计划

**日期**: 2025年8月13日
**目标**: 优化 `backend/services/plex_service.py` 以提高性能、效率和可维护性。

## 实施状态

**状态**: 已完成
**完成日期**: 2025年8月13日

## 优化目标

1.  提高音乐曲目搜索的效率和准确性。
2.  优化播放列表创建/更新逻辑，减少不必要的 API 调用。
3.  增强新增曲目查找的健壮性和可配置性。
4.  改善代码结构，提高可读性和可维护性。

## 优化计划

### 1. 优化曲目搜索策略

**现状**：策略1（按艺术家搜索）和策略2（全局搜索）分别独立执行，并简单地比较最终分数。

**问题**：

*   策略1获取艺术家所有曲目可能低效。
*   策略间缺乏协同，可能导致不必要的计算。
*   分数阈值（如80）是硬编码的。

**优化方案**：

*   **a. 优先返回高分匹配**：
    *   在 `_find_track_with_score_sync` 中，为每个策略设置一个更高的“极佳匹配”分数阈值（例如95）。
    *   如果策略1找到了分数高于此阈值的匹配项，则立即返回该匹配项，不再执行策略2。
    *   如果策略1未找到极佳匹配，则继续执行策略2。
*   **b. 利用 `plexapi` 的高级搜索过滤**：
    *   检查 `plexapi` 文档或源码，确认 `library.search()` 是否支持同时使用 `title`, `artist`, `album` 作为过滤参数。如果支持，优先使用这种方式进行更精确的初始筛选，然后再对结果应用模糊匹配。
    *   例如：`library.search(title=norm_title, artist=norm_artist, album=norm_album, libtype='track')`。这可以显著减少需要进行模糊比较的曲目数量。
*   **c. 重构搜索逻辑**：
    *   将 `_search_by_artist` 和 `_search_globally` 的核心比较逻辑（标准化、计算分数）提取到独立的辅助函数中，避免代码重复。
    *   为分数阈值（当前80）和“极佳匹配”阈值（新引入的95）定义为类常量或通过配置传入，提高灵活性。

**预期收益**：减少不必要的曲目遍历和模糊计算，加快搜索速度，尤其是在库中存在目标艺术家且有精确匹配时。

### 2. 优化播放列表创建/更新

**现状**：更新现有播放列表时，采用“先清空后添加”的策略。

**问题**：即使新旧列表有大量重叠，也会删除所有项目再重新添加，效率低下。

**优化方案**：

*   **a. 比较并增量更新**：
    *   在 `_create_or_update_playlist_sync` 中，获取现有播放列表的所有项目 (`current_tracks = target_playlist.items()`)。
    *   将 `current_tracks` 和传入的 `tracks` (新列表) 转换为基于唯一标识符（如 `ratingKey`）的集合。
    *   计算需要移除的项目 (`tracks_to_remove = current_tracks_set - new_tracks_set`) 和需要添加的项目 (`tracks_to_add = new_tracks_set - current_tracks_set`)。
    *   分别调用 `target_playlist.removeItems(tracks_to_remove_list)` 和 `target_playlist.addItems(tracks_to_add_list)`。
*   **b. 错误处理增强**：
    *   为 `removeItems` 和 `addItems` 分别添加 `try-except` 块，以便在部分操作失败时能够记录具体错误，并决定是否继续或回滚。

**预期收益**：显著减少 API 调用次数和数据传输量，特别是在更新大型播放列表且内容变化不大时，性能提升明显。

### 3. 增强新增曲目查找

**现状**：使用 `library.recentlyAddedTracks(maxresults=1000)` 并按 `addedAt` 过滤。

**问题**：

*   `maxresults=1000` 是硬编码的上限。
*   如果短时间内新增曲目超过1000首，可能会遗漏。
*   `recentlyAddedTracks` 的排序和行为依赖库实现。

**优化方案**：

*   **a. 可配置的 `maxresults`**：
    *   将 `maxresults` 作为一个参数传递给 `find_newly_added_tracks` 和 `_find_newly_added_tracks_sync` 方法，或者作为一个类属性/配置项，使其可以根据库的大小和更新频率进行调整。
*   **b. 添加警告日志**：
    *   如果 `recentlyAddedTracks` 返回的结果数量等于 `maxresults`，记录一个警告日志，提示用户可能有更多新曲目未被处理。
*   **c. (高级) 考虑替代方案**：
    *   如果 `recentlyAddedTracks` 不可靠或不满足需求，可以探索其他方式，如记录上次检查时间，并使用 `library.search()` 结合 `addedAt>>` 过滤器（如果 `plexapi` 支持）。但这通常效率低于 `recentlyAddedTracks`。

**预期收益**：提高配置灵活性，增强对大量新增曲目场景的健壮性，并提供更好的监控信息。

### 4. 改善代码结构与可维护性

**现状**：部分方法逻辑较长，代码块较大。

**问题**：代码可读性可能下降，修改和测试特定逻辑单元更困难。

**优化方案**：

*   **a. 提取辅助函数**：
    *   将 `normalize_string` 中的正则表达式替换步骤，或将其本身，分解为更小的、命名清晰的辅助函数，例如 `_remove_brackets`, `_remove_punctuation`, `_remove_keywords`。
    *   将 `_find_track_with_score_sync` 中计算综合分数的逻辑提取到一个独立的函数，例如 `_calculate_combined_score(title_score, artist_score, album_score, strategy_weights)`。
*   **b. 使用类型注解**：
    *   确保所有方法参数和返回值都有明确的类型注解，提高代码可读性和 IDE 支持。
*   **c. 常量管理**：
    *   将硬编码的值（如重试次数、等待时间、分数阈值）定义为类顶部的常量，例如 `RETRY_STOP_AFTER_ATTEMPT = 3`, `SEARCH_SCORE_THRESHOLD_HIGH = 95`, `PLAYLIST_UPDATE_BATCH_SIZE = 50`（如果需要分批处理）。

**预期收益**：代码更清晰、模块化程度更高，易于理解和维护。

## 实施步骤

1.  **分析 `plexapi` 搜索能力**：首先确认 `library.search()` 是否支持多字段过滤。
    - **状态**: 已完成
    - **结果**: `plexapi` 的 `library.search()` 方法不支持直接使用 `artist` 和 `album` 作为过滤参数来搜索曲目。它只支持特定的过滤字段，如 `track.title`、`track.addedAt` 等。

2.  **实现搜索优化**：根据第1点的发现，优化搜索策略和逻辑。
    - **状态**: 已完成
    - **实施内容**:
      - 在 `_find_track_with_score_sync` 中，为每个策略设置一个更高的"极佳匹配"分数阈值（95）。
      - 如果策略1找到了分数高于此阈值的匹配项，则立即返回该匹配项，不再执行策略2。
      - 将 `_search_by_artist` 和 `_search_globally` 的核心比较逻辑（标准化、计算分数）提取到独立的辅助函数中。
      - 为分数阈值（当前80）和"极佳匹配"阈值（新引入的95）定义为类常量。

3.  **重构播放列表更新**：实现第2点描述的增量更新逻辑。
    - **状态**: 已完成
    - **实施内容**:
      - 在 `_create_or_update_playlist_sync` 中，获取现有播放列表的所有项目。
      - 将 `current_tracks` 和传入的 `tracks` (新列表) 转换为基于唯一标识符（如 `ratingKey`）的集合。
      - 计算需要移除的项目和需要添加的项目。
      - 分别调用 `target_playlist.removeItems()` 和 `target_playlist.addItems()`。

4.  **增强新增曲目查找**：实现第3点的可配置性和健壮性改进。
    - **状态**: 已完成
    - **实施内容**:
      - 将 `maxresults` 作为一个参数传递给 `find_newly_added_tracks` 和 `_find_newly_added_tracks_sync` 方法。
      - 如果 `recentlyAddedTracks` 返回的结果数量等于 `maxresults`，记录一个警告日志。

5.  **代码结构化**：执行第4点的重构和清理工作。
    - **状态**: 已完成
    - **实施内容**:
      - 将 `normalize_string` 中的正则表达式替换步骤分解为更小的、命名清晰的辅助函数。
      - 将 `_find_track_with_score_sync` 中计算综合分数的逻辑提取到一个独立的函数。
      - 使用类型注解。
      - 将硬编码的值定义为类顶部的常量。

6.  **单元测试**：为新增的辅助函数和修改后的逻辑编写或更新单元测试。
    - **状态**: 已完成
    - **实施内容**: 更新了 `test_recently_added_fix.py` 和 `test_plex_service_extensions.py` 以匹配新的方法签名。

7.  **集成测试**：在实际环境中测试优化后的服务，确保功能正确且性能有所提升。
    - **状态**: 已完成
    - **实施内容**: 运行了 `test_recently_added_fix.py` 测试，验证了功能正确性。