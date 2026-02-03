#!/bin/bash
# 🐳 保险密心 Docker 控制脚本 / Insurance Meseeing Docker Control

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

show_help() {
    echo ""
    echo -e "${BLUE}🐳 保险密心 Docker 控制脚本${NC}"
    echo ""
    echo "用法: ./docker.sh [命令]"
    echo ""
    echo "命令:"
    echo "  build     构建 Docker 镜像"
    echo "  up        启动所有服务（后台运行）"
    echo "  down      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  logs      查看服务日志"
    echo "  status    查看服务状态"
    echo "  clean     清理无用镜像和容器"
    echo "  shell     进入后端容器 shell"
    echo "  help      显示帮助信息"
    echo ""
}

check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker 未运行，请先启动 Docker Desktop"
        exit 1
    fi
}

build() {
    print_info "正在构建 Docker 镜像..."
    docker compose build --no-cache
    print_success "镜像构建完成！"
}

up() {
    print_info "正在启动服务..."
    docker compose up -d
    print_success "服务已启动！"
    echo ""
    print_info "后端 API: http://localhost:8001"
    print_info "前端应用: http://localhost:3001"
    print_info "API 文档: http://localhost:8001/docs"
    echo ""
}

down() {
    print_info "正在停止服务..."
    docker compose down
    print_success "服务已停止！"
}

restart() {
    print_info "正在重启服务..."
    docker compose restart
    print_success "服务已重启！"
}

logs() {
    docker compose logs -f --tail=100
}

status() {
    echo ""
    print_info "服务状态："
    docker compose ps
    echo ""
}

clean() {
    print_warning "正在清理无用的 Docker 资源..."
    docker system prune -f
    print_success "清理完成！"
}

shell() {
    print_info "进入后端容器..."
    docker compose exec insurance-backend /bin/bash
}

check_docker

case "${1:-help}" in
    build)   build ;;
    up)      up ;;
    down)    down ;;
    restart) restart ;;
    logs)    logs ;;
    status)  status ;;
    clean)   clean ;;
    shell)   shell ;;
    help)    show_help ;;
    *)
        print_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac
