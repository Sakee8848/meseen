#!/bin/bash

echo "🚀 开始自动化部署流程..."

# 1. 停止并删除旧容器
echo "🛑 正在停止旧容器..."
docker stop meseeing-app || true
docker rm meseeing-app || true

# 2. 构建新镜像
echo "🏗️ 正在构建新镜像 v1..."
docker build -t meseeing:v1 .

# 3. 启动新容器
echo "🚢 正在启动容器，映射端口 8000..."
docker run -d \
  --name meseeing-app \
  -p 8000:8000 \
  -v $(pwd)/etl_factory:/app/etl_factory \
  -v $(pwd)/backend/domain_db:/app/backend/domain_db \
  meseeing:v1

echo "✅ 部署完成！后端已在容器中稳定运行。"