#!/bin/bash
# 🐳 保险密心 - Docker 一键启动
# 使用 Docker Compose 启动，避免终端会话阻塞

set -e

cd "$(dirname "$0")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐳 保险密心 - Docker 模式启动"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行"
    echo "   请先启动 Docker Desktop"
    exit 1
fi

# 检查 .env 文件
if [ ! -f "backend/.env" ]; then
    echo "⚠️  未找到 backend/.env"
    if [ -f "backend/.env.example" ]; then
        echo "   正在从模板创建..."
        cp backend/.env.example backend/.env
        echo "   ✅ 已创建，请编辑填入 API 密钥"
    fi
fi

echo ""
echo "🧹 清理旧容器..."
docker-compose down 2>/dev/null || true

echo ""
echo "🚀 启动容器（后台模式）..."
docker-compose up -d --build

echo ""
echo "⏳ 等待服务就绪..."
sleep 5

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Docker 容器已启动！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📌 访问地址："
echo "   • 后端 API : http://localhost:8001/docs"
echo "   • 前端应用 : http://localhost:3001"
echo ""
echo "📊 查看容器状态："
echo "   docker-compose ps"
echo ""
echo "📝 查看日志："
echo "   docker-compose logs -f backend"
echo "   docker-compose logs -f frontend"
echo ""
echo "🛑 停止服务："
echo "   docker-compose down"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
