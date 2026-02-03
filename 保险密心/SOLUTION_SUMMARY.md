# ✅ 保险密心 - 启动问题解决方案汇总

## 🎯 问题回顾
在 VS Code Agent 环境下，直接运行 `uvicorn` 或 `npm run dev` 等前台命令会导致：
1.  终端会话被持续占用
2.  Agent 无法执行后续指令（一直在 "Running" 状态）
3.  服务启动看似失败或卡死

## 🛠 已交付的解决方案

### 方案 A：Docker 容器化启动（⭐ 强烈推荐）
这是最稳定、最干净的方案，完全隔离环境，不占用本地终端。

- **启动**: `bash docker_start.sh`
- **停止**: `bash docker_stop.sh`
- **查看日志**: `docker-compose logs -f`
- **指南**: [DOCKER_GUIDE.md](./DOCKER_GUIDE.md)

### 方案 B：本地后台启动（已验证可用）
如果您不想使用 Docker，可以使用这个优化过的脚本。它使用 `nohup` 将服务放入后台运行。

- **启动**: `bash quick_start.sh`
- **停止**: `bash stop_services.sh`
- **重启**: `bash restart_services.sh`
- **排查**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

---

## 🔍 当前状态检查
如果您想随时查看当前运行的服务，请使用以下命令：

**检查本地服务 (PID)**:
```bash
lsof -i :8001 -i :3001
```

**检查 Docker 容器**:
```bash
docker-compose ps
```

## 💡 最佳实践建议
1.  **优先使用 Docker**：它能解决 99% 的环境依赖和终端占用问题。
2.  **避免在 Agent 终端运行长进程**：始终使用 `nohup ... &` 或 Docker。
3.  **定期清理**：如果发现端口冲突，运行 `bash stop_services.sh` 或 `bash docker_stop.sh`。

---
*文档生成时间: 2026-02-02*
