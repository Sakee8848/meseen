# 保险密心前端 - Docker 镜像
# 阶段 1: 构建
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
# 注入后端 API 地址（构建时变量）
ARG NEXT_PUBLIC_API_URL=http://localhost:8001
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build

# 阶段 2: 运行（standalone 模式，镜像更轻量）
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
# 只复制必要产物
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

EXPOSE 3000
CMD ["node", "server.js"]