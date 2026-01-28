# 使用官方轻量级 Python 环境
FROM python:3.11-slim

# 设置容器内的工作目录
WORKDIR /app

# 先安装依赖（利用 Docker 缓存机制加速构建）
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有内容
COPY . .

# 设置 Python 路径，确保 backend 下的模块能被正确引用
ENV PYTHONPATH=/app/backend

# 暴露 FastAPI 的 8000 端口
EXPOSE 8000

# 启动命令：启动后端服务器
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]