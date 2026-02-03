#!/bin/bash
# 🏦 保险密心 - 一键启动脚本
# ================================
# 独立于 HR 密心运行，使用端口 8001/3001

set -e

echo "🏦 正在启动保险密心系统..."

# 检查 .env 文件
if [ ! -f "backend/.env" ]; then
    echo "⚠️  未找到 backend/.env，正在从模板创建..."
    cp backend/.env.example backend/.env
    echo "📝 请编辑 backend/.env 填入您的 API 密钥"
fi

# 启动方式选择
if command -v docker-compose &> /dev/null; then
    echo "🐳 使用 Docker Compose 启动..."
    docker-compose -p insurance-meseeing up -d
    echo ""
    echo "✅ 保险密心已启动"
    echo "   后端 API: http://localhost:8001"
    echo "   前端应用: http://localhost:3001 (如已配置)"
else
    echo "📦 使用本地 Python 启动后端..."
    cd backend
    
    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        echo "🔧 创建虚拟环境..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt -q
    
    echo "🚀 启动后端服务 (端口 8001)..."
    uvicorn main:app --host 0.0.0.0 --port 8001 --reload &
    
    echo ""
    echo "✅ 保险密心后端已启动: http://localhost:8001"
fi
