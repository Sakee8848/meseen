# 🔧 保险密心 - 启动问题诊断与解决方案

## 问题描述

当尝试访问 `localhost:3001` 时显示 `ERR_CONNECTION_REFUSED`，说明前端服务未运行。

## 根本原因分析

### 1. **Agent 终端阻塞问题**
- 当使用 `uvicorn` 或 `npm run dev` 等**前台运行**的命令时，这些进程会持续占用终端会话
- IDE 的 Agent 在执行新命令时会等待之前的会话释放资源
- 如果有多个长时间运行的命令（如您的元数据显示有2个运行了17分钟和10分钟的命令），会导致所有后续命令被阻塞
- 表现为：点击 Accept 后一直显示 "Running"，命令实际上从未真正开始执行

### 2. **解决原理**
必须使用**后台守护进程**模式启动服务：
```bash
nohup <命令> > 日志文件 2>&1 &
```
这样命令会立即返回，服务在后台运行，不占用终端会话。

---

## ✅ 立即解决方案（5步搞定）

### 第1步：打开新终端
在 VS Code 中点击顶部菜单 `Terminal` → `New Terminal`（或按 `Ctrl+Shift+\``）

### 第2步：执行一键启动脚本
复制以下命令并粘贴到终端：

```bash
bash /Users/tonyyu/Documents/密心/保险密心/quick_start.sh
```

### 第3步：等待3-5秒
脚本会自动完成：
- ✅ 清理端口占用
- ✅ 启动后端（8001）
- ✅ 启动前端（3001）

### 第4步：验证服务
打开浏览器访问：
- 后端 API 文档：http://localhost:8001/docs
- 前端应用：http://localhost:3001

### 第5步：查看日志（如果有问题）
```bash
# 查看后端日志
tail -f /Users/tonyyu/Documents/密心/保险密心/backend.log

# 查看前端日志
tail -f /Users/tonyyu/Documents/密心/保险密心/frontend.log
```

---

## 🛑 停止服务

```bash
bash /Users/tonyyu/Documents/密心/保险密心/stop_services.sh
```

---

## 📊 检查服务状态

```bash
# 查看端口占用情况
lsof -i :8001 -i :3001

# 查看进程
ps aux | grep -E "uvicorn|next" | grep -v grep
```

---

## 🚨 紧急修复（如果脚本也失败）

### 手动清理端口
```bash
# 强制杀掉 8001 端口进程
kill -9 $(lsof -t -i:8001) 2>/dev/null

# 强制杀掉 3001 端口进程
kill -9 $(lsof -t -i:3001) 2>/dev/null
```

### 手动启动后端
```bash
cd /Users/tonyyu/Documents/密心/保险密心/backend
source /Users/tonyyu/Documents/密心/venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --reload > ../backend.log 2>&1 &
```

### 手动启动前端
```bash
cd /Users/tonyyu/Documents/密心/保险密心/expert-app
nohup npm run dev > ../frontend.log 2>&1 &
```

---

## 💡 预防未来问题

### 使用专用启动/停止脚本
我已为您创建：
- `quick_start.sh` - 一键启动（推荐）
- `stop_services.sh` - 一键停止
- `restart_services.sh` - 一键重启

### 避免使用前台命令
❌ **不要这样启动**：
```bash
uvicorn main:app --reload  # 会占用终端
npm run dev  # 会占用终端
```

✅ **应该这样启动**：
```bash
nohup uvicorn main:app --reload > backend.log 2>&1 &
nohup npm run dev > frontend.log 2>&1 &
```

---

## 🔍 为什么 Agent 命令会卡住？

Agent 通过 IDE 的终端执行命令时：
1. 如果之前有**前台长运行命令**（uvicorn/npm），它们会一直占用会话
2. 新命令需要等待会话空闲才能执行
3. 如果有多个僵尸会话，会形成**资源死锁**
4. 表现为：命令永远停在 "Running" 状态

**解决方案**：
- 始终使用 `nohup ... &` 后台模式
- 定期清理僵尸进程
- 使用专用脚本管理服务生命周期

---

## 📞 仍有问题？

1. 检查虚拟环境是否激活：
   ```bash
   which python
   # 应该输出：/Users/tonyyu/Documents/密心/venv/bin/python
   ```

2. 检查依赖是否安装：
   ```bash
   cd /Users/tonyyu/Documents/密心/保险密心/backend
   source /Users/tonyyu/Documents/密心/venv/bin/activate
   pip list | grep -E "uvicorn|fastapi"
   ```

3. 检查前端依赖：
   ```bash
   cd /Users/tonyyu/Documents/密心/保险密心/expert-app
   npm list next
   ```

4. 重新安装依赖：
   ```bash
   # 后端
   pip install -r requirements.txt
   
   # 前端
   npm install
   ```
