#!/bin/bash
# =============================================================================
# 🚀 密心新领域项目初始化脚本 / Meseeing New Domain Initializer
# =============================================================================
# 使用方法: ./init-domain.sh <领域ID> <中文名> <端口偏移>
# 示例: ./init-domain.sh legal 法律密心 2
# 这将创建一个使用端口 8002/3002 的法律领域项目
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

print_banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║          🧠 密心多领域项目初始化工具                         ║${NC}"
    echo -e "${CYAN}║          Meseeing Multi-Domain Project Initializer           ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }

show_help() {
    print_banner
    echo "用法: ./init-domain.sh <领域ID> <中文名> <端口偏移>"
    echo ""
    echo "参数说明:"
    echo "  <领域ID>     项目标识符，使用小写英文，如: legal, medical, finance"
    echo "  <中文名>     项目中文名称，如: 法律密心, 医疗密心"
    echo "  <端口偏移>   相对于基础端口 8000/3000 的偏移量"
    echo ""
    echo "示例:"
    echo "  ./init-domain.sh legal 法律密心 2    # 创建法律项目，端口 8002/3002"
    echo "  ./init-domain.sh medical 医疗密心 3  # 创建医疗项目，端口 8003/3003"
    echo ""
    echo "⚠️  创建前请检查 domains.yaml 确保端口未被占用！"
    echo ""
    
    # 显示当前已使用的端口
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}当前已注册的领域:${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ -f "domains.yaml" ]; then
        grep -E "^\s+- id:" domains.yaml | sed 's/.*id: "/  • /; s/"$//'
    fi
    echo ""
}

# 参数检查
if [ "$1" == "help" ] || [ "$1" == "--help" ] || [ "$1" == "-h" ] || [ -z "$1" ]; then
    show_help
    exit 0
fi

if [ -z "$2" ] || [ -z "$3" ]; then
    print_error "参数不完整！"
    show_help
    exit 1
fi

DOMAIN_ID="$1"
DOMAIN_NAME="$2"
PORT_OFFSET="$3"

BACKEND_PORT=$((8000 + PORT_OFFSET))
FRONTEND_PORT=$((3000 + PORT_OFFSET))
PROJECT_DIR="${SCRIPT_DIR}/${DOMAIN_NAME}"

print_banner

# 检查目录是否已存在
if [ -d "$PROJECT_DIR" ]; then
    print_error "目录已存在: $PROJECT_DIR"
    exit 1
fi

# 检查端口是否已被注册
if grep -q "backend: $BACKEND_PORT" domains.yaml 2>/dev/null; then
    print_error "端口 $BACKEND_PORT 已在 domains.yaml 中注册！"
    exit 1
fi

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "  领域 ID:     ${GREEN}$DOMAIN_ID${NC}"
echo -e "  项目名称:   ${GREEN}$DOMAIN_NAME${NC}"
echo -e "  后端端口:   ${GREEN}$BACKEND_PORT${NC}"
echo -e "  前端端口:   ${GREEN}$FRONTEND_PORT${NC}"
echo -e "  项目目录:   ${GREEN}$PROJECT_DIR${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

read -p "确认创建? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "已取消"
    exit 0
fi

echo ""
print_info "正在创建项目结构..."

# 创建目录结构
mkdir -p "$PROJECT_DIR"/{backend/simulation_engine,backend/domain_db,expert-app,etl_factory}

# ---------------------------------------------------------------------------
# 创建后端 Dockerfile
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/backend/Dockerfile" << EOF
# 使用官方轻量级 Python 环境
FROM python:3.11-slim

# 设置容器内的工作目录
WORKDIR /app

# 安装 curl 用于健康检查
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# 先安装依赖（利用 Docker 缓存机制加速构建）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目所有内容
COPY . .

# 设置 Python 路径
ENV PYTHONPATH=/app

# 暴露端口 - ${DOMAIN_NAME}
EXPOSE $BACKEND_PORT

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$BACKEND_PORT"]
EOF

# ---------------------------------------------------------------------------
# 创建后端 requirements.txt
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/backend/requirements.txt" << 'EOF'
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
langchain-core==0.1.10
langchain-openai==0.0.2
python-dotenv==1.0.0
EOF

# ---------------------------------------------------------------------------
# 创建后端 .env
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/backend/.env" << 'EOF'
# 智谱 API Key
OPENAI_API_KEY=your-api-key-here

# 智谱的 OpenAI 兼容接口地址
OPENAI_API_BASE=https://open.bigmodel.cn/api/paas/v4/
EOF

# ---------------------------------------------------------------------------
# 创建基础 main.py
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/backend/main.py" << EOF
"""
${DOMAIN_NAME} 后端 API
端口: ${BACKEND_PORT}
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="${DOMAIN_NAME} API",
    description="${DOMAIN_NAME}的专家知识逆向工程系统 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:${FRONTEND_PORT}", "http://127.0.0.1:${FRONTEND_PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "domain": "${DOMAIN_ID}"}

@app.get("/")
async def root():
    return {"message": "Welcome to ${DOMAIN_NAME} API", "port": ${BACKEND_PORT}}
EOF

# ---------------------------------------------------------------------------
# 创建前端 Dockerfile
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/expert-app/Dockerfile" << EOF
# 阶段 1: 构建
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
ARG NEXT_PUBLIC_API_URL=http://localhost:${BACKEND_PORT}
ENV NEXT_PUBLIC_API_URL=\${NEXT_PUBLIC_API_URL}
RUN npm run build

# 阶段 2: 运行
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]
EOF

# ---------------------------------------------------------------------------
# 创建 docker-compose.yml
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/docker-compose.yml" << EOF
name: meseeing-${DOMAIN_ID}  # ${DOMAIN_NAME}

services:
  ${DOMAIN_ID}-backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: meseeing-${DOMAIN_ID}-backend
    ports:
      - "${BACKEND_PORT}:${BACKEND_PORT}"
    volumes:
      - ./backend:/app
      - ./etl_factory:/app/../etl_factory
    env_file:
      - ./backend/.env
    restart: unless-stopped
    networks:
      - ${DOMAIN_ID}-meseeing-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${BACKEND_PORT}/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ${DOMAIN_ID}-frontend:
    build:
      context: ./expert-app
      dockerfile: Dockerfile
    container_name: meseeing-${DOMAIN_ID}-frontend
    ports:
      - "${FRONTEND_PORT}:3000"
    depends_on:
      - ${DOMAIN_ID}-backend
    environment:
      - NEXT_PUBLIC_API_URL=http://${DOMAIN_ID}-backend:${BACKEND_PORT}
    restart: unless-stopped
    networks:
      - ${DOMAIN_ID}-meseeing-net

networks:
  ${DOMAIN_ID}-meseeing-net:
    driver: bridge
EOF

# ---------------------------------------------------------------------------
# 创建启动脚本
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/start.sh" << EOF
#!/bin/bash
# ${DOMAIN_NAME} 启动脚本

echo "🚀 启动 ${DOMAIN_NAME}..."
echo "   后端: http://localhost:${BACKEND_PORT}"
echo "   前端: http://localhost:${FRONTEND_PORT}"
echo ""

# 启动后端
cd backend
source ../venv/bin/activate 2>/dev/null || python3 -m venv ../venv && source ../venv/bin/activate
pip install -r requirements.txt -q
uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT} --reload &

# 启动前端
cd ../expert-app
npm run dev -- -p ${FRONTEND_PORT} &

wait
EOF

chmod +x "$PROJECT_DIR/start.sh"

# ---------------------------------------------------------------------------
# 创建 README
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/README.md" << EOF
# 🧠 ${DOMAIN_NAME}

> ${DOMAIN_NAME}专家知识逆向工程系统

## 📍 端口配置

| 服务 | 端口 |
|------|------|
| 后端 API | ${BACKEND_PORT} |
| 前端应用 | ${FRONTEND_PORT} |

## 🚀 快速启动

### 本地开发
\`\`\`bash
./start.sh
\`\`\`

### Docker 部署
\`\`\`bash
docker compose up -d
\`\`\`

## 🔗 访问地址

- 前端应用: http://localhost:${FRONTEND_PORT}
- 后端 API: http://localhost:${BACKEND_PORT}
- API 文档: http://localhost:${BACKEND_PORT}/docs
EOF

# ---------------------------------------------------------------------------
# 创建 .gitignore
# ---------------------------------------------------------------------------
cat > "$PROJECT_DIR/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
venv/
.venv/
*.egg-info/

# Node
node_modules/
.next/
out/

# Environment
.env.local
*.local

# IDE
.idea/
.vscode/

# OS
.DS_Store
EOF

print_success "项目结构创建完成！"
echo ""

# ---------------------------------------------------------------------------
# 更新 domains.yaml
# ---------------------------------------------------------------------------
print_info "正在更新 domains.yaml..."

# 在文件末尾添加新领域（在预留槽位注释之前）
cat >> "$SCRIPT_DIR/domains.yaml" << EOF

  # ---------------------------------------------------------------------------
  # ${DOMAIN_NAME} (自动生成于 $(date +%Y-%m-%d))
  # ---------------------------------------------------------------------------
  - id: "${DOMAIN_ID}"
    name: "${DOMAIN_NAME}"
    name_en: "Meseeing ${DOMAIN_ID^}"
    description: "${DOMAIN_ID}领域的专家知识逆向工程系统"
    path: "./${DOMAIN_NAME}"
    ports:
      backend: ${BACKEND_PORT}
      frontend: ${FRONTEND_PORT}
    docker:
      project_name: "meseeing-${DOMAIN_ID}"
      network: "${DOMAIN_ID}-meseeing-net"
    status: "active"
    created_at: "$(date +%Y-%m-%d)"
EOF

print_success "domains.yaml 已更新！"

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  🎉 ${DOMAIN_NAME} 项目创建成功！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "下一步操作:"
echo ""
echo "  1. 进入项目目录:"
echo -e "     ${CYAN}cd ${PROJECT_DIR}${NC}"
echo ""
echo "  2. 本地启动:"
echo -e "     ${CYAN}./start.sh${NC}"
echo ""
echo "  3. Docker 启动:"
echo -e "     ${CYAN}docker compose up -d${NC}"
echo ""
echo "  4. 从主项目复制业务代码 (可选):"
echo -e "     ${CYAN}cp -r ../backend/simulation_engine/* backend/simulation_engine/${NC}"
echo ""
