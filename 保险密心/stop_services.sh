#!/bin/bash
# 🛑 保险密心 - 停止所有服务

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🛑 停止保险密心服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

STOPPED=0

for port in 8001 3001; do
    PIDS=$(lsof -t -i:$port 2>/dev/null || true)
    if [ -n "$PIDS" ]; then
        SERVICE_NAME="后端"
        if [ "$port" = "3001" ]; then
            SERVICE_NAME="前端"
        fi
        
        echo "   • 停止 $SERVICE_NAME 服务 (端口 $port, PID: $PIDS)"
        kill -9 $PIDS 2>/dev/null || true
        STOPPED=$((STOPPED + 1))
    fi
done

echo ""
if [ $STOPPED -eq 0 ]; then
    echo "✅ 没有运行中的服务"
else
    echo "✅ 已停止 $STOPPED 个服务"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
