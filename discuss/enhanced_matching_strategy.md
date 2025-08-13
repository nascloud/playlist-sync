### **方案：基于核心标题搜索与精细化评分的Plex匹配优化**

**1. 目标**

显著提高Plex音乐库中歌曲的匹配成功率，特别是解决多艺术家歌曲匹配失败以及歌曲版本变体（如live, demo, acoustic等）匹配不准确的问题。

**2. 核心思想**

改变搜索策略，从使用原始标题搜索转变为使用**“核心标题”**进行初步搜索，以最大化召回率。然后，利用原始查询信息（标题、艺术家、专辑）和精细化的评分系统（特别是对艺术家信息和版本信息的深度比较）对Plex返回的候选结果进行精确评分和排序，以选出最匹配的歌曲。

**3. 详细设计**

**3.1. 核心匹配流程重构 (`_find_track_with_score_sync`)**

修改 `services/plex_service.py` 中的 `_find_track_with_score_sync` 方法。

*   **步骤**:
    1.  **标准化与核心提取**: 对 `title`, `artist`, `album` 进行 `_normalize_string` (严格标准化) 和 `_extract_core_title` (提取核心标题) 处理。
        *   `norm_title = _normalize_string(title)`
        *   `core_title = _extract_core_title(norm_title)`
        *   `norm_artist = _normalize_string(artist)`
        *   `norm_album = _normalize_string(album)`
    2.  **核心标题搜索**: 使用 `library.search(core_title, libtype='track')` 获取所有标题包含核心部分的候选歌曲。这一步利用Plex服务器的能力进行高效召回。
    3.  **候选评分**: 对每一个Plex返回的候选歌曲，调用精细化评分函数 `_calculate_enhanced_score` 进行打分。此函数将综合考虑 `norm_title`, `norm_artist`, `norm_album`, `core_title` 以及版本信息。
    4.  **排序**: 将所有候选者按 `_calculate_enhanced_score` 计算出的分数从高到低排序。
    5.  **阈值过滤与结果返回**:
        *   设定一个**高置信度阈值**（如85）。
        *   如果最高分超过此阈值，则直接返回该歌曲和分数。
        *   如果最高分未超过阈值，但仍高于一个**低置信度阈值**（如70），则返回分数最高的候选歌曲和其分数（标记为低置信度）。
        *   如果没有候选者或最高分低于低置信度阈值，则返回 `(None, 0)`。

**3.2. 标题预处理增强**

在 `plex_service.py` 中增强或新增标题处理函数。

*   **`_normalize_string(text: str) -> str` (严格标准化)**:
    *   保留现有逻辑：移除括号（特定内容和所有内容）、标点、多余空格，并进行大小写、全角半角统一。
    *   微调 `_remove_keywords`：从移除列表中移除或调整 `live`, `demo`, `acoustic` 等版本相关词，确保严格标准化不会丢失这些信息。或者，创建一个新的、更保守的移除列表用于此函数。
*   **`_extract_core_title(norm_title: str) -> str` (提取核心标题)**:
    *   **目标**: 从一个已严格标准化的标题中提取出“核心”部分，即去除版本、现场、演示等信息。
    *   **实现**:
        *   维护一个“版本关键词列表”：`["live", "demo", "acoustic", "instrumental", "mix", "version", "remix", "edit", "feat", "ft", "radio", "album", "single", "explicit", "clean", "session", "take"]`。
        *   移除括号内容：使用智能的 `_remove_brackets`，它能识别括号内是否仅包含版本关键词或纯数字/小数（如 `0.8x`），如果是则移除整个括号内容。
        *   移除版本关键词：在移除括号后，再次扫描字符串，移除上述列表中的关键词（使用词边界 `\b` 确保准确）。
        *   移除多余空格。
        *   例如：
            *   输入: `"song a (live)"`
            *   `_normalize_string`: `"song a live"` (假设 `live` 未被 `_remove_keywords` 移除)
            *   `_extract_core_title`: `"song a"`
            *   输入: `"song a (feat. b)"`
            *   `_normalize_string`: `"song a feat b"` (括号被移除)
            *   `_extract_core_title`: `"song a"` (假设 `feat` 在版本关键词列表中或通过其他逻辑处理)
            *   输入: `"song a 1.2x"`
            *   `_normalize_string`: `"song a 1.2x"`
            *   `_extract_core_title`: `"song a"`

**3.3. 精细化评分系统增强 (`_calculate_enhanced_score`)**

更新或创建 `_calculate_enhanced_score` 方法来计算每个候选歌曲的综合匹配分数。这是整个匹配流程的核心评分环节。

*   **输入**: 一个 `plexapi.audio.Track` 对象，以及 `norm_title`, `norm_artist`, `norm_album`, `core_title`。
*   **输出**: 一个 0-100 的综合分数。
*   **评分维度与计算**:
    *   **标题相似度 (`title_score`)**:
        *   `plex_norm_title = _normalize_string(track.title)`
        *   `title_score = fuzz.ratio(norm_title, plex_norm_title)` (或 `fuzz.token_sort_ratio` 等)。这衡量了原始输入与Plex标题的直接相似度。
    *   **核心标题相似度 (`core_title_score`)**:
        *   `plex_core_title = _extract_core_title(plex_norm_title)`
        *   `core_title_score = fuzz.ratio(core_title, plex_core_title)`。这衡量了输入核心与Plex标题核心的相似度。
    *   **综合标题分数**:
        *   可以结合 `title_score` 和 `core_title_score`，例如 `combined_title_score = (title_score * 0.7) + (core_title_score * 0.3)`。这样既考虑了完整匹配，也考虑了核心匹配。
        *   **版本惩罚**: 如果输入 `norm_title` 的核心部分 `core_title` 与 `plex_norm_title` 相同，但 `norm_title` 本身与 `plex_norm_title` 不同（意味着Plex标题有额外版本信息），可以对 `combined_title_score` 施加轻微惩罚，例如 `combined_title_score *= 0.95`。
    *   **艺术家相似度 (`artist_score`)**: **(核心改进点，沿用)**
        *   `plex_artist = _normalize_string(track.grandparentTitle or "")`
        *   调用 `_calculate_artist_score(norm_artist, plex_artist)`。
    *   **专辑相似度 (`album_score`)**:
        *   `plex_album = _normalize_string(track.parentTitle or "")`
        *   `album_score = fuzz.ratio(norm_album, plex_album) if norm_album else 70`。
    *   **动态权重**:
        *   `W_TITLE = 0.4` (结合了原始和核心标题)
        *   `W_ARTIST = 0.4`
        *   `W_ALBUM = 0.2`
    *   **综合分数**:
        *   `final_score = (combined_title_score * W_TITLE) + (artist_score * W_ARTIST) + (album_score * W_ALBUM)`
    *   **(可选) Bonus/Penalty**: 可根据特定规则（如主艺术家完全匹配）给予额外加分。

**3.4. 多艺术家评分函数 (`_calculate_artist_score`)**

沿用 `improved_matching_strategy.md` 中的设计。

**4. 实施步骤**

1.  **开发**:
    *   在 `plex_service.py` 中实现或增强 `_normalize_string` 函数（确保不误删版本词）。
    *   实现 `_extract_core_title` 函数。
    *   实现 `_calculate_enhanced_score` 方法，包含核心标题比较和版本惩罚逻辑。
    *   重写 `_find_track_with_score_sync` 方法，采用新的“核心标题搜索 + 精细化评分”逻辑。
2.  **测试**:
    *   利用 `test_artist_matching_analysis.py` 脚本。
    *   修改脚本或创建新的测试用例，重点测试包含版本变体（如live, demo, acoustic）和多艺术家的歌曲匹配情况。
    *   运行测试，对比新旧方案在 `unmatched.json` 上的匹配成功率和准确率。
3.  **部署**:
    *   代码审查无误后，合并到主分支。
    *   在你的Plex环境中部署并观察效果。

**5. 预期效果**

*   **最大化搜索召回率**: 通过核心标题搜索，确保所有相关变体都能被Plex找到。
*   **显著提升多艺术家歌曲匹配率**: 继承自上一版方案。
*   **显著提升歌曲版本变体匹配准确率**: 通过精细化评分，能更好地区分 `歌曲A` 与 `歌曲A（live）`、`歌曲A（demo）` 等，优先返回最符合用户查询意图的版本。
*   **提高整体匹配准确率和鲁棒性**: 结合了Plex服务器的搜索能力和客户端的精细化评分，使匹配结果更准确、更符合用户直觉，并可能提升性能。