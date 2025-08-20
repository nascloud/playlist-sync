#!/bin/sh
# 确保脚本在任何命令失败时都退出
set -e

# 应用数据库迁移
echo "Running database migrations..."
python -m alembic upgrade head

# 执行传递给脚本的任何命令（例如，Dockerfile中的CMD）
# 如果没有命令，则 docker-compose.yml 中的 command 将被执行
echo "Starting application..."
echo "--- DIAGNOSTICS ---"
echo "Current directory: $(pwd)"
echo "Directory listing:"
ls -la
echo "--- END DIAGNOSTICS ---"
exec python -m "$@"
