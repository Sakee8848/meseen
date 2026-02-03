#!/bin/bash
# 保险密心后端启动脚本

cd /Users/tonyyu/Documents/密心/保险密心/backend

# 激活虚拟环境
source /Users/tonyyu/Documents/密心/venv/bin/activate

# 启动后端服务
echo "🚀 启动保险密心后端服务 (端口 8001)..."
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
