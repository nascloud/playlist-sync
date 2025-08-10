# 使用官方 Python 镜像作为基础
FROM python:3.9-slim

# 安装 uv
RUN pip install --no-cache-dir uv

# 创建工作目录
WORKDIR /usr/src/app

# 复制项目配置文件
COPY pyproject.toml uv.lock ./

# 安装依赖
RUN uv sync --no-cache

# 复制应用源代码
COPY . .

# 暴露端口
EXPOSE 3001

# 复制入口脚本并给予执行权限
COPY docker-entrypoint.sh /usr/local/bin/
RUN sed -i 's/\r$//g' /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 设置入口点
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3001"]

