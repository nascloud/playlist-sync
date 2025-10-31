# 数据库迁移指南

## 问题描述

当应用代码中引用了数据库中不存在的列时，会出现以下错误：
```
sqlite3.OperationalError: no such column: download_lyrics
```

## 解决方案

### 1. 使用 Alembic 进行数据库迁移（推荐）

在开发和部署过程中，应始终使用 Alembic 来管理数据库模式变更：

```bash
# 升级数据库到最新版本
alembic upgrade head

# 检查当前数据库版本
alembic current

# 查看迁移历史
alembic history
```

### 2. 手动修复（临时方案）

如果遇到数据库模式不匹配的问题，可以手动添加缺失的列：

```sql
-- 例如添加 download_lyrics 列
ALTER TABLE download_sessions ADD COLUMN download_lyrics BOOLEAN DEFAULT 0;
```

### 3. Docker 部署中的自动迁移

在 Docker 环境中，应在启动脚本中自动执行数据库迁移：

```yaml
# 在 docker-compose.yml 中
command: >
  sh -c "
    alembic upgrade head &&
    uvicorn main:app --host 0.0.0.0 --port 8000
  "
```

## 最佳实践

1. 每当代码中有数据库模式变更时，确保同时创建并应用相应的 Alembic 迁移
2. 在部署新版本前，先备份数据库
3. 在 CI/CD 流程中自动执行数据库迁移
4. 开发人员同步代码后，应执行 `alembic upgrade head` 来更新本地数据库结构

## 相关文件

- 迁移文件存储在 `backend/alembic/versions/` 目录中
- Alembic 配置文件为 `backend/alembic.ini`
- 数据库连接配置在 `backend/core/database.py` 中