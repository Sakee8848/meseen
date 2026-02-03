#!/bin/bash

# 定义颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔄 开始强制重启保险密心服务...${NC}"

# 1. 强力清理占用端口的进程
echo "🧹 清理端口 8001 (后端) 和 3001 (前端)..."
PIDS_8001=$(lsof -t -i:8001)
if [ -n "$PIDS_8001" ]; then
    echo "   - 停止后端进程: $PIDS_8001"
    kill -9 $PIDS_8001 2>/dev/null
fi

PIDS_3001=$(lsof -t -i:3001)
if [ -n "$PIDS_3001" ]; then
    echo "   - 停止前端进程: $PIDS_3001"
    kill -9 $PIDS_3001 2>/dev/null
fi
sleep 1

# 2. 启动后端 (作为后台守护进程)
echo -e "${GREEN}🚀 启动后端服务 (8001)...${NC}"
cd /Users/tonyyu/Documents/密心/保险密心/backend
source /Users/tonyyu/Documents/密心/venv/bin/activate
# 使用 nohup 彻底脱离终端运行
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ 后端已启动 (PID: $BACKEND_PID)，日志记录在 backend.log"

# 3. 启动前端 (作为后台守护进程)
echo -e "${GREEN}🚀 启动前端服务 (3001)...${NC}"
cd /Users/tonyyu/Documents/密心/保险密心/expert-app
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ 前端已启动 (PID: $FRONTEND_PID)，日志记录在 frontend.log"

echo -e "${GREEN}🎉 所有服务已在后台运行！${NC}"
echo "---------------------------------------------------"
echo "👉 后端接口: http://localhost:8001/docs"
echo "👉 前端页面: http://localhost:3001"
echo "---------------------------------------------------"
