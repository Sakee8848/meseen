#!/bin/bash
# 🚀 保险密心 - 极速启动脚本
# 使用方法: bash quick_start.sh

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏦 保险密心 - 一键启动"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 进入项目根目录
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# 1. 清理旧进程
echo ""
echo "🧹 清理旧进程..."
for port in 8001 3001; do
    PIDS=$(lsof -t -i:$port 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        echo "   • 停止端口 $port 的进程: $PIDS"
        kill -9 $PIDS 2>/dev/null || true
    fi
done

sleep 1

# 2. 启动后端
echo ""
echo "🚀 启动后端服务 (端口 8001)..."
cd "$PROJECT_ROOT/backend"

# 检查虚拟环境
if [ ! -d "/Users/tonyyu/Documents/密心/venv" ]; then
    echo "❌ 错误: 虚拟环境不存在"
    echo "   请先运行: python3 -m venv /Users/tonyyu/Documents/密心/venv"
    exit 1
fi

# 激活虚拟环境并启动
source /Users/tonyyu/Documents/密心/venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --reload \
    > "$PROJECT_ROOT/backend.log" 2>&1 &
BACKEND_PID=$!

echo "   ✅ 后端已启动"
echo "      • PID: $BACKEND_PID"
echo "      • 日志: $PROJECT_ROOT/backend.log"

# 3. 启动前端
echo ""
echo "🚀 启动前端服务 (端口 3001)..."
cd "$PROJECT_ROOT/expert-app"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "   ⚠️  首次运行，正在安装依赖..."
    npm install --silent
fi

nohup npm run dev > "$PROJECT_ROOT/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo "   ✅ 前端已启动"
echo "      • PID: $FRONTEND_PID"
echo "      • 日志: $PROJECT_ROOT/frontend.log"

# 4. 等待服务就绪
echo ""
echo "⏳ 等待服务启动完成..."
sleep 3

# 5. 检查服务状态
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 服务启动完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 访问地址："
echo "   • 后端 API : http://localhost:8001/docs"
echo "   • 前端应用 : http://localhost:3001"
echo ""
echo "📊 查看日志："
echo "   • 后端: tail -f $PROJECT_ROOT/backend.log"
echo "   • 前端: tail -f $PROJECT_ROOT/frontend.log"
echo ""
echo "🛑 停止服务："
echo "   bash $PROJECT_ROOT/stop_services.sh"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
