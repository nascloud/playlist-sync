# ---- 前端构建阶段 ----
FROM node:18-alpine AS frontend-builder

# 设置前端工作目录
WORKDIR /usr/src/frontend

# 复制前端项目文件并安装依赖
COPY web/package*.json ./
RUN npm install

# 复制前端所有代码并构建
COPY web/ ./
RUN npm run build

# ---- 后端构建阶段 ----
FROM python:3.9-slim AS backend-builder

# 安装 uv
RUN pip install --no-cache-dir uv

# 设置后端工作目录
WORKDIR /usr/src/app

# 复制后端项目文件并安装依赖
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv pip install --system . --no-cache-dir

# 卸载 uv
RUN pip uninstall -y uv

# 复制后端所有代码
COPY backend/ .

# 从前端构建阶段复制打包好的静态文件
COPY --from=frontend-builder /usr/src/frontend/dist ./static

# 复制并授权入口脚本
COPY backend/docker-entrypoint.sh /usr/local/bin/
RUN sed -i 's/\r$//g' /usr/local/bin/docker-entrypoint.sh && chmod +x /usr/local/bin/docker-entrypoint.sh

# 暴露端口
EXPOSE 3001

# 设置入口点和默认命令
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3001"]
