---
description: 创建新的密心领域项目（如法律密心、医疗密心等）
---

# 🆕 创建新领域项目工作流

当用户需要创建新的领域项目时，请遵循以下步骤：

## 前置检查

1. **查看现有端口分配**
   ```bash
   cat /Users/tonyyu/Documents/密心/domains.yaml
   ```
   确认下一个可用的端口偏移量（当前已使用：0=HR, 1=保险）

2. **确认领域信息**
   - 领域 ID（英文小写，如 `legal`, `medical`, `finance`）
   - 中文名称（如 `法律密心`, `医疗密心`）
   - 端口偏移量（下一个未使用的数字）

## 执行创建

// turbo
3. **运行初始化脚本**
   ```bash
   cd /Users/tonyyu/Documents/密心
   ./init-domain.sh <领域ID> <中文名> <端口偏移>
   ```
   示例：`./init-domain.sh legal 法律密心 2`

## 后续配置

4. **复制业务代码模板**（可选）
   ```bash
   cp -r backend/simulation_engine/* <新项目>/backend/simulation_engine/
   ```

5. **配置 API Key**
   编辑 `<新项目>/backend/.env` 添加智谱 API Key

6. **启动测试**
   ```bash
   cd <新项目>
   ./start.sh
   ```

## 端口参考表

| 领域 | 后端 | 前端 | 状态 |
|------|------|------|------|
| HR (主项目) | 8000 | 3000 | ✅ |
| 保险 | 8001 | 3001 | ✅ |
| 法律 | 8002 | 3002 | 📋 预留 |
| 医疗 | 8003 | 3003 | 📋 预留 |
| 金融 | 8004 | 3004 | 📋 预留 |
