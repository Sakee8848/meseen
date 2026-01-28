import json
import os
import uuid
import random
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage

# 尝试引入仿真引擎，如果失败则打印警告
try:
    from simulation_engine.domain_manager import DomainManager
    from simulation_engine.graph import app as graph_app, SimulationState
    SIMULATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: simulation_engine components not found: {e}")
    SIMULATION_AVAILABLE = False

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 🌟 绝对路径锚定：彻底解决“文件找不着”的问题
BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
ETL_LOG = ROOT_DIR / "etl_factory" / "processing_log.json"
DB_DIR = BASE_DIR / "domain_db"

# 🔧 仿真会话状态存储 (简化版：单会话)
current_simulation = {
    "state": None,
    "step_count": 0,
    "mission": None,
    "domain": "hr"
}

# ==========================================
# 🎮 逆向工程：接口垫片 (兼容所有前端路径)
# ==========================================
@app.post("/api/start")           
@app.post("/api/simulation/start") 
async def start_simulation(data: Dict[str, Any] = None):
    global current_simulation
    domain = data.get("domain", "hr") if data else "hr"
    missions = [
        {"intent": "员工怀孕了，我想让她辞职。", "term": "孕期合规", "cat": "劳动关系"},
        {"intent": "技术主管带走核心代码去竞对公司。", "term": "竞业限制管理", "cat": "员工关系"}
    ]
    selected = random.choice(missions)
    mission = {"novice_intent": selected["intent"], "expert_term": selected["term"], "category": selected["cat"]}
    
    # 初始化仿真状态
    taxonomy_context = DomainManager(domain).get_expert_context() if SIMULATION_AVAILABLE else ""
    current_simulation = {
        "state": {
            "messages": [],
            "domain": domain,
            "taxonomy_context": taxonomy_context,
            "secret_mission": mission,
            "is_concluded": False,
            "turn_count": 0
        },
        "step_count": 0,
        "mission": mission,
        "domain": domain
    }
    
    return {
        "status": "started",
        "thread_id": str(uuid.uuid4()),
        "mission": mission,
        "taxonomy": taxonomy_context
    }

# ==========================================
# 🚀 仿真引擎：逐步执行 (核心新增)
# ==========================================
@app.post("/api/next")
@app.post("/api/simulation/next")
async def next_step():
    global current_simulation
    
    if not current_simulation["state"]:
        raise HTTPException(status_code=400, detail="请先调用 /api/start 开始仿真")
    
    state = current_simulation["state"]
    step = current_simulation["step_count"]
    
    # 检查是否已结束
    if state.get("is_concluded", False):
        return {
            "step": -1,
            "role": "system",
            "content": "🎉 仿真已完成！专家已成功识别用户意图。",
            "raw_state": True
        }
    
    if not SIMULATION_AVAILABLE:
        # 模拟模式：无 LangGraph 时返回模拟数据
        step += 1
        current_simulation["step_count"] = step
        
        # 记录对话历史
        if "dialogue_history" not in current_simulation:
            current_simulation["dialogue_history"] = []
        
        if step == 1:
            msg = {"step": step, "role": "ai", "content": "您好，请问您遇到了什么人力资源方面的问题？我可以帮您分析。"}
            current_simulation["dialogue_history"].append(msg)
            return {**msg, "raw_state": False}
        elif step == 2:
            intent = current_simulation["mission"]["novice_intent"]
            msg = {"step": step, "role": "human", "content": intent}
            current_simulation["dialogue_history"].append(msg)
            return {**msg, "raw_state": False}
        elif step == 3:
            term = current_simulation["mission"]["expert_term"]
            msg = {"step": step, "role": "ai", "content": f"根据您描述的情况，这属于「{term}」领域的问题。我来为您详细分析..."}
            current_simulation["dialogue_history"].append(msg)
            return {**msg, "raw_state": False}
        else:
            state["is_concluded"] = True
            # 🔧 保存到 ETL 数据库
            save_simulation_to_etl(current_simulation)
            return {"step": -1, "role": "system", "content": f"🎉 仿真完成！专家成功识别：{current_simulation['mission']['expert_term']}\n\n✅ 已自动保存到 ETL 数据库", "raw_state": True}
    
    # 真实模式：调用 LangGraph 引擎
    try:
        # 执行一步仿真
        result = graph_app.invoke(state)
        
        # 更新状态
        current_simulation["state"] = result
        current_simulation["step_count"] += 1
        step = current_simulation["step_count"]
        
        # 记录对话历史
        if "dialogue_history" not in current_simulation:
            current_simulation["dialogue_history"] = []
        
        # 提取最新消息
        messages = result.get("messages", [])
        if messages:
            last_msg = messages[-1]
            role = "ai" if isinstance(last_msg, AIMessage) else "human"
            content = last_msg.content
            current_simulation["dialogue_history"].append({"step": step, "role": role, "content": content})
        else:
            role = "system"
            content = "无响应"
        
        is_done = result.get("is_concluded", False)
        
        if is_done:
            # 🔧 保存到 ETL 数据库
            save_simulation_to_etl(current_simulation)
            return {
                "step": -1,
                "role": "system", 
                "content": f"🎉 仿真完成！专家成功识别用户意图。\n\n目标术语: {current_simulation['mission']['expert_term']}\n\n✅ 已自动保存到 ETL 数据库",
                "raw_state": True
            }
        
        return {
            "step": step,
            "role": role,
            "content": content,
            "raw_state": False
        }
        
    except Exception as e:
        return {
            "step": step,
            "role": "error",
            "content": f"仿真引擎错误: {str(e)}",
            "raw_state": False
        }

# ==========================================
# 💾 保存仿真结果到 ETL 数据库
# ==========================================
def save_simulation_to_etl(simulation_data: dict):
    """将完成的仿真保存到 ETL 收件箱"""
    from datetime import datetime
    
    mission = simulation_data.get("mission", {})
    dialogue = simulation_data.get("dialogue_history", [])
    
    # 构建 ETL 记录
    etl_record = {
        "id": f"sim_{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.now().isoformat(),
        "status": "pending",
        "domain": simulation_data.get("domain", "hr"),
        "query": mission.get("novice_intent", ""),
        "ai_prediction": mission.get("expert_term", ""),
        "category": mission.get("category", ""),
        "confidence": 0.95,  # 仿真验证的置信度较高
        "source": "simulation_workbench",
        "dialogue_path": [
            {"step": d["step"], "role": d["role"], "content": d["content"][:500]}  # 限制长度
            for d in dialogue
        ]
    }
    
    # 读取现有数据
    try:
        if ETL_LOG.exists():
            with open(ETL_LOG, 'r', encoding='utf-8') as f:
                inbox = json.load(f)
                if not isinstance(inbox, list):
                    inbox = []
        else:
            inbox = []
    except:
        inbox = []
    
    # 添加新记录
    inbox.insert(0, etl_record)  # 插入到最前面
    
    # 保存
    try:
        ETL_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(ETL_LOG, 'w', encoding='utf-8') as f:
            json.dump(inbox, f, ensure_ascii=False, indent=2)
        print(f"✅ ETL: 已保存仿真记录 {etl_record['id']}")
    except Exception as e:
        print(f"❌ ETL 保存失败: {e}")

# ==========================================
# 📥 ETL 库：全兼容入库 (支持单选/全选)
# ==========================================
@app.get("/api/knowledge/logs")
@app.get("/api/etl/inbox")
async def get_etl_inbox():
    if not ETL_LOG.exists(): return []
    try:
        with open(ETL_LOG, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except: return []


@app.post("/api/taxonomy/add")    
@app.post("/api/knowledge/ingest")
@app.post("/api/etl/batch_ingest")
async def universal_ingest(request: Request):
    if not ETL_LOG.exists(): 
        return {"status": "error", "message": "ETL log file not found"}
    
    # 🔧 修复：使用 Request 对象正确解析 JSON body
    try:
        body = await request.json()
    except Exception as e:
        return {"status": "error", "message": f"Invalid JSON: {str(e)}"}
    
    # 统一解析数据格式
    items = []
    if "items" in body: 
        items = body["items"]
    else: 
        items = [{"id": body.get("id"), "domain": body.get("domain", "hr")}]
    
    print(f"📥 ETL 入库请求: {len(items)} 条记录")

    with open(ETL_LOG, 'r', encoding='utf-8') as f:
        inbox = json.load(f)

    db_cache = {}
    success_ids = []

    for item in items:
        rid, dom = item.get("id"), item.get("domain", "hr")
        record = next((r for r in inbox if r["id"] == rid), None)
        if not record: 
            print(f"⚠️ 未找到记录: {rid}")
            continue
        
        if dom not in db_cache:
            p = DB_DIR / f"{dom}.json"
            if p.exists():
                with open(p, 'r', encoding='utf-8') as f: 
                    db_cache[dom] = json.load(f)
            else:
                print(f"⚠️ 知识库文件不存在: {p}")
                continue

        if dom in db_cache:
            ai_pred = record.get("ai_prediction", "")
            matched = False
            
            # 🔧 修复：在 taxonomy 的 services 中查找匹配的服务
            for category in db_cache[dom].get("taxonomy", []):
                services = category.get("services", [])
                
                # 检查 ai_prediction 是否在服务列表中（支持模糊匹配）
                for idx, service in enumerate(services):
                    if ai_pred in service or service in ai_pred or ai_pred == service:
                        # 找到匹配的服务，添加追踪记录
                        if "trace_records" not in category:
                            category["trace_records"] = {}
                        if service not in category["trace_records"]:
                            category["trace_records"][service] = []
                        
                        # 添加记录
                        trace_entry = {
                            "id": record.get("id"),
                            "timestamp": record.get("timestamp"),
                            "query": record.get("query", ""),
                            "ai_prediction": ai_pred,
                            "confidence": record.get("confidence", 0),
                            "source": record.get("source", "etl_inbox")
                        }
                        category["trace_records"][service].append(trace_entry)
                        success_ids.append(rid)
                        matched = True
                        print(f"✅ 入库成功: {ai_pred} → {category['name']}/{service}")
                        break
                
                if matched:
                    break
            
            if not matched:
                # 如果没有精确匹配，尝试添加到对应的 category
                for category in db_cache[dom].get("taxonomy", []):
                    cat_name = category.get("name", "")
                    record_cat = record.get("category", "")
                    
                    # 检查类别是否匹配
                    if record_cat and (record_cat in cat_name or cat_name in record_cat):
                        # 动态添加新服务到 services 列表
                        if ai_pred not in category.get("services", []):
                            if "services" not in category:
                                category["services"] = []
                            category["services"].append(ai_pred)
                        
                        # 添加追踪记录
                        if "trace_records" not in category:
                            category["trace_records"] = {}
                        if ai_pred not in category["trace_records"]:
                            category["trace_records"][ai_pred] = []
                        
                        trace_entry = {
                            "id": record.get("id"),
                            "timestamp": record.get("timestamp"),
                            "query": record.get("query", ""),
                            "ai_prediction": ai_pred,
                            "confidence": record.get("confidence", 0),
                            "source": record.get("source", "etl_inbox")
                        }
                        category["trace_records"][ai_pred].append(trace_entry)
                        success_ids.append(rid)
                        print(f"✅ 入库成功 (新增服务): {ai_pred} → {cat_name}")
                        break
    
    # 保存更新后的知识库
    for d, content in db_cache.items():
        with open(DB_DIR / f"{d}.json", 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)

    # 成功后从收件箱移除
    new_inbox = [r for r in inbox if r["id"] not in success_ids]
    with open(ETL_LOG, 'w', encoding='utf-8') as f:
        json.dump(new_inbox, f, ensure_ascii=False, indent=2)

    print(f"📊 ETL 入库完成: 成功 {len(success_ids)} 条")
    return {"status": "success", "count": len(success_ids)}

@app.get("/api/taxonomy")
async def get_taxonomy(domain: str = "hr"):
    p = DB_DIR / f"{domain}.json"
    if not p.exists(): return {"service_nodes": []}
    with open(p, 'r', encoding='utf-8') as f: return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)