# 匹配策略优化方案

根据 `analysis_results_round3.md` 的分析和 `plex_service.py` 的代码审查，针对当前匹配策略存在的问题，特别是`Baby, Don't Cry（人鱼的眼泪） (Chinese Ver.)`这类歌曲匹配失败的问题，提出以下优化方案。

## 问题核心

1.  **核心标题提取不精确**: `Baby, Don't Cry（人鱼的眼泪） (Chinese Ver.)` 被提取为 `baby don t cry`，丢失了关键的 `'` 符号，导致在Plex库中无法搜索到。
2.  **版本关键词处理不完善**: `Ver.` (带点) 未被完全匹配和处理。

## 优化方案

### 1. 修复核心标题提取逻辑

**问题点**:
- 在 `_normalize_string` 函数中，`_remove_punctuation` 会移除所有标点符号，包括歌曲名中至关重要的 `'` (如 `Don't`)。
- 这导致 `Baby, Don't Cry` 被错误地标准化为 `baby don t cry`。

**解决方案**:
- 修改 `_remove_punctuation` 函数，使其不移除单引号 `'`。
- 或者，在 `_normalize_string` 中，调整处理顺序，先提取核心标题，再进行其他标准化操作。

**推荐做法 (修改 `_remove_punctuation`)**:
```python
def _remove_punctuation(text: str) -> str:
    """移除标点符号，但保留单引号"""
    # 保留单引号，移除其他标点
    return re.sub(r"[^\\w\\s']", ' ', text)
```
这样可以确保 `Don't` 在标准化后仍为 `don't`，从而在核心标题 `baby don't cry` 中保留 `'`。

### 2. 完善版本关键词处理

**问题点**:
- `VERSION_KEYWORDS` 列表中包含 `ver`, `Ver`, `Ver.`。
- 但在 `_extract_core_title` 中，使用 `re.sub(rf"\\b{re.escape(keyword)}\\b", "", core_title, flags=re.IGNORECASE)` 进行替换。
- `re.escape(keyword)` 会将 `Ver.` 转义为 `Ver\\.`，然后 `\\b` 与 `\\.` 的边界可能不匹配，导致 `Ver.` 未被正确移除。

**解决方案**:
- 确保 `_extract_core_title` 中的正则表达式能正确处理 `Ver.`。
- 或者，在 `VERSION_KEYWORDS` 中使用更通用的模式，如 `ver\\.?` 来匹配 `ver` 和 `ver.`。

**推荐做法 (修改 `_extract_core_title` 的正则逻辑)**:
```python
# 在 _extract_core_title 函数内部
# 构建一个更健壮的正则表达式来移除版本关键词
# 注意：需要对特殊字符进行转义，并处理可选的点
escaped_keywords = [re.escape(kw) for kw in VERSION_KEYWORDS]
# 将 kw\\.? 模式替换为 kw 或 kw. (例如 ver\\.? 匹配 ver 或 ver.)
pattern_parts = []
for kw in escaped_keywords:
    if kw.endswith(r'\\.'): # 如果关键词以转义的点结尾 (如 Ver\\.)
        # 匹配 Ver 或 Ver. (原 kw 是 Ver.)
        base_kw = kw[:-2] # 去掉 \\.
        pattern_parts.append(f"{base_kw}\\.?")
    else:
        # 对于其他关键词，直接匹配
        pattern_parts.append(kw)

# 使用一个大的正则表达式一次性移除所有关键词
# 注意：需要按长度降序排列，以避免短关键词先匹配了长关键词的一部分
pattern_parts.sort(key=len, reverse=True)
pattern = r'\\b(?:' + '|'.join(pattern_parts) + r')\\b'
core_title = re.sub(pattern, "", core_title, flags=re.IGNORECASE)
```

### 3. 验证与测试

1.  **打印调试信息**: 在 `_find_track_with_score_sync` 中，打印 `norm_title` 和 `core_title`，确认 `Baby, Don't Cry` 的处理结果。
2.  **单元测试**: 更新或编写针对 `_normalize_string` 和 `_extract_core_title` 的单元测试，覆盖 `Don't`, `Ver.`, `feat.`, `ft.` 等边界情况。
3.  **运行完整测试**: 应用修改后，重新运行 `test_enhanced_matching.py`，观察 `Baby, Don't Cry` 是否能被正确搜索到，并检查其他歌曲的匹配情况是否受到影响。

## 结论

通过以上两项关键修改，特别是对 `_remove_punctuation` 的调整，可以有效解决 `Baby, Don't Cry` 因核心标题提取错误而导致的匹配失败问题。同时，完善版本关键词的处理逻辑，可以提升整体匹配策略的鲁棒性。