# 🚀 保险密心 - 快速参考

## 常用命令

```bash
# 一键启动（推荐）
bash /Users/tonyyu/Documents/密心/保险密心/quick_start.sh

# 停止服务
bash /Users/tonyyu/Documents/密心/保险密心/stop_services.sh

# 重启服务
bash /Users/tonyyu/Documents/密心/保险密心/restart_services.sh

# 查看后端日志
tail -f /Users/tonyyu/Documents/密心/保险密心/backend.log

# 查看前端日志
tail -f /Users/tonyyu/Documents/密心/保险密心/frontend.log

# 检查服务状态
lsof -i :8001 -i :3001
```

## 访问地址

- **前端应用**: http://localhost:3001
- **后端 API 文档**: http://localhost:8001/docs
- **后端健康检查**: http://localhost:8001/health

## 故障排查

详见 `TROUBLESHOOTING.md`

## 项目结构

```
保险密心/
├── backend/              # FastAPI 后端
│   ├── main.py          # 主入口
│   ├── .env             # 环境变量配置
│   └── domain_db/       # 知识库
├── expert-app/          # Next.js 前端
│   └── .env.local       # 前端环境变量
├── etl_factory/         # ETL 数据处理
├── quick_start.sh       # 一键启动 ⭐
├── stop_services.sh     # 停止服务
├── restart_services.sh  # 重启服务
└── TROUBLESHOOTING.md   # 故障排查指南
```
