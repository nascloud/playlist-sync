# 歌单解析错误修复方案

## 问题分析

通过分析日志和代码，发现歌单解析错误主要由以下几个问题导致：

1. **PlexService初始化问题**：`create_instance`方法缺少`@classmethod`装饰器
2. **数据库迁移问题**：日志显示列不存在错误
3. **URL解析问题**：无法从QQ音乐URL中提取有效的歌单ID

## 已修复的问题

### 1. PlexService初始化问题

**问题**：在`plex_service.py`中，`create_instance`方法被定义为实例方法而不是类方法，导致调用时出现`'str' object is not callable`错误。

**修复**：为`create_instance`方法添加`@classmethod`装饰器。

```python
# 修复前
async def create_instance(cls, base_url: str, token: str, verify_ssl: bool = True):
    """异步创建PlexService实例"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, cls, base_url, token, verify_ssl)

# 修复后
@classmethod
async def create_instance(cls, base_url: str, token: str, verify_ssl: bool = True):
    """异步创建PlexService实例"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, cls, base_url, token, verify_ssl)
```

### 2. 日志访问问题

**问题**：在`download.py`中，尝试直接访问`LOGS_DIR`，但应该使用`download_log_manager`实例。

**修复**：导入并使用正确的日志管理器。

## 待解决的问题

### 数据库迁移问题

日志中显示以下错误：
- `no such column: status_message`
- `no such column: platform` 
- `no such column: updated_at`

尽管通过`PRAGMA table_info`命令检查发现这些列确实存在于表结构中，但应用程序仍然报告这些列不存在。这可能是由于以下原因：

1. **Alembic迁移未正确应用**：可能需要重新运行Alembic迁移确保所有迁移都已应用。
2. **数据库版本不匹配**：可能存在多个数据库文件或者数据库连接指向了错误的文件。

**解决建议**：
1. 确保所有Alembic迁移都已正确应用：
   ```bash
   alembic upgrade head
   ```

2. 检查数据库连接是否指向正确的文件。

### QQ音乐URL解析问题

日志显示"无法从URL中提取有效的歌单ID"，但正则表达式测试是通过的。这可能是由于：
1. 传递给解析函数的URL格式不正确
2. 平台参数传递错误

**解决建议**：
1. 检查API端点中URL和平台参数的传递
2. 添加更多日志来调试URL解析过程

## 验证步骤

1. 重新启动应用程序
2. 创建一个新的同步任务
3. 检查日志中是否还有`'str' object is not callable`错误
4. 验证任务是否能正确解析歌单并同步到Plex

## 预防措施

1. 添加更全面的单元测试覆盖URL解析和Plex服务初始化
2. 在URL解析失败时提供更详细的错误信息
3. 定期检查和更新Alembic迁移