#!/bin/bash

echo "🚀 Meseeing 密心全系统一键启动程序..."

# 1. 环境自检：确保 Docker 正在运行
if ! docker info > /dev/null 2>&1; then
  echo "❌ 错误: Docker Desktop 似乎没启动，请先打开它！"
  exit 1
fi

# 2. 清理旧残骸：杀死本地 8000 和 3000 端口占用
echo "清理端口占用..."
kill -9 $(lsof -t -i:8000) 2>/dev/null
kill -9 $(lsof -t -i:3000) 2>/dev/null

# 3. 编排并拉起全系统
echo "🏗️  正在构建镜像并启动全栈服务..."
docker-compose up --build -d

echo "✅ 启动成功！"
echo "🌐 前端界面: http://localhost:3000"
echo "🛠️  后端 API: http://localhost:8000"
echo "📊 查看运行状态: docker-compose ps"