# 保险密心后端 - Docker 镜像
FROM python:3.11-slim

WORKDIR /app

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 安装依赖（利用 Docker 缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 设置 Python 路径
ENV PYTHONPATH=/app

# 暴露端口 (使用8001，与HR密心的8000区分)
EXPOSE 8001

# 启动服务
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
