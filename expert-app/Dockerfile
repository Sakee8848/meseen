# 阶段 1: 构建
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
# 注入后端 API 地址
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
RUN npm run build

# 阶段 2: 运行
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV production
# 只复制必要产物，保持镜像强壮且轻量
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]