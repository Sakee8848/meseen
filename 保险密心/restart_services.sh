#!/bin/bash
# 🔄 保险密心 - 重启所有服务

cd "$(dirname "$0")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 重启保险密心服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 停止旧服务
bash stop_services.sh

echo ""
echo "⏳ 等待端口释放..."
sleep 2

# 启动新服务
bash quick_start.sh
