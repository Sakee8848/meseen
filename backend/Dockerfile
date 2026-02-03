# 使用官方轻量级 Python 环境
FROM python:3.11-slim

# 设置容器内的工作目录
WORKDIR /app

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 先安装依赖（利用 Docker 缓存机制加速构建）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有内容
COPY . .

# 设置 Python 路径
ENV PYTHONPATH=/app

# 暴露 FastAPI 的 8000 端口 (HR 密心)
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]