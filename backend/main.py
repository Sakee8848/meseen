import os
import json
import uuid
import ast
import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 引入内部模块
from simulation_engine.domain_manager import DomainManager
from simulation_engine.graph import app as graph_app 
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# 加载环境变量
load_dotenv()

print("\n" + "="*60)
print("🛡️ 正在启动 Meseeing 后端 (V4.4 最终定稿版 - Boolean强类型)...")
print("="*60 + "\n")

# ==========================================
# 1. 核心对象初始化
# ==========================================
domain_mgr = None
try:
    domain_mgr = DomainManager("hr")
    print(f"✅ 大脑加载成功")
except Exception as e:
    print(f"❌ 大脑加载失败: {e}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. 全局状态
# ==========================================
simulation_state = {
    "iterator": None,
    "current_step": 0,
    "thread_id": None,
    "static_context": {}, 
    "last_human_message": "",
    "has_concluded": False 
}

# ==========================================
# 3. 数据模型定义
# ==========================================
class SimStartRequest(BaseModel):
    domain: str = "hr"

class ChatRequest(BaseModel):
    message: str
    domain: str = "hr"

class TaxonomyUpdate(BaseModel):
    category: str
    service: str

class CategoryRename(BaseModel):
    old_name: str
    new_name: str

class CategoryDelete(BaseModel):
    category_name: str

# ==========================================
# 4. 内部工具函数：写入 ETL 数据库
# ==========================================
def _save_to_etl(diagnosis_data):
    try:
        etl_path = Path(__file__).resolve().parent.parent / "etl_factory" / "processing_log.json"
        mission = simulation_state.get("static_context", {}).get("secret_mission", {})
        
        new_record = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending", 
            "domain": "hr",
            "query": mission.get("display_intent", "未知用户意图"), 
            "ground_truth": mission.get("expert_term", "未知标准服务"), 
            "ai_prediction": diagnosis_data.get("matched_service", "未匹配"),
            "ai_reasoning": diagnosis_data.get("diagnosis", "无详细诊断"),
            "confidence": diagnosis_data.get("confidence", 0)
        }

        existing_data = []
        if etl_path.exists():
            with open(etl_path, "r", encoding="utf-8") as f:
                try: existing_data = json.load(f)
                except: existing_data = []
        
        existing_data.append(new_record)
        
        # 确保目录存在
        etl_path.parent.mkdir(parents=True, exist_ok=True)
        with open(etl_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
        print(f"💾 [ETL] 成功保存线索到收件箱: {new_record['query'][:10]}...")
        return True
    except Exception as e:
        print(f"❌ [ETL] 保存失败: {e}")
        return False

# ==========================================
# 5. 接口定义
# ==========================================

# --- [A] 仿真控制接口 ---

@app.post("/api/start")
async def start_simulation(req: SimStartRequest = None):
    """初始化仿真"""
    print(f"\n⚡️ [START] 收到启动请求...")
    if not domain_mgr: raise HTTPException(500, "Domain Manager not ready")

    domain = req.domain if req else "hr"

    true_intent = "我想把不听话的员工开除，但怕赔钱"
    
    roleplay_instruction = f"""
    【角色设定】
    你是一个不懂专业术语的普通用户（小白）。
    你的真实目的是："{true_intent}"。
    
    【行为准则】
    1. **直奔主题**：不要寒暄，直接抛出员工恶劣行为和你的担忧。
    2. **急于成交**：一旦专家指出风险，立刻询问解决方案。
    3. 每次回复不要超过 60 个字。
    """

    mission = {
        "novice_intent": roleplay_instruction,
        "display_intent": true_intent,
        "opening_line": "专家你好，我这边有个员工天天旷工还顶嘴，我想让他立马走人，但听说现在法律保护员工，我怕被讹钱，这事儿咋整？",
        "expert_term": "裁员/辞退合规咨询",
        "category": "劳动关系与合规"
    }

    inputs = {
        "messages": [("user", mission["opening_line"])],
        "domain": domain,
        "taxonomy_context": domain_mgr.get_expert_context(),
        "secret_mission": mission,
        "is_concluded": False, 
        "turn_count": 0 
    }
    
    new_thread_id = f"sim_{uuid.uuid4()}"
    print(f"🧵 [START] 新线程 ID: {new_thread_id}")

    iterator = graph_app.stream(
        inputs, 
        config={
            "configurable": {"thread_id": new_thread_id},
            "recursion_limit": 100
        }, 
        stream_mode="values"
    )
    
    # 重置状态
    simulation_state["iterator"] = iterator
    simulation_state["current_step"] = 0
    simulation_state["thread_id"] = new_thread_id
    simulation_state["last_human_message"] = mission["opening_line"]
    simulation_state["has_concluded"] = False 
    
    context_backup = inputs.copy()
    if "messages" in context_backup:
        del context_backup["messages"]
    simulation_state["static_context"] = context_backup

    response_mission = mission.copy()
    response_mission["novice_intent"] = true_intent 

    return {"status": "started", "mission": response_mission}

@app.post("/api/next")
async def next_step():
    """执行下一步 (V4.4 最终定稿版)"""
    
    # 🚦 1. 绝对刹车 (返回 Boolean True)
    if simulation_state["has_concluded"]:
        print("🏆 [SYSTEM] 流程已完结，发送 Boolean 信号。")
        return {
            "step": -1, 
            "content": "🏁 交易达成：Leads已入库 (Simulation Completed)", 
            "role": "system",
            "raw_state": True # 👈 重点：没有引号！是 Boolean！
        }

    if not simulation_state["iterator"]:
        raise HTTPException(400, "请先点击开始")
    
    if simulation_state["current_step"] > 30:
        return {"step": -1, "content": "🏁 强制终止：对话轮次过多", "role": "system"}

    # --- 内部辅助函数 ---
    def get_safe_content(msg):
        if isinstance(msg, tuple):
            return msg[0], msg[1]
        else:
            return getattr(msg, "type", "unknown"), getattr(msg, "content", str(msg))

    def process_step_data(step_data):
        messages = step_data.get("messages", [])
        if not messages:
            return "system", "Processing..."
        
        last_msg = messages[-1]
        role, content = get_safe_content(last_msg)

        if role == "human" or role == "user":
            simulation_state["last_human_message"] = content

        str_content = str(content)
        parsed_data = None
        
        # 🔥 V4.4 混合解析
        if "{" in str_content:
            try:
                start = str_content.find("{")
                end = str_content.rfind("}") + 1
                json_str = str_content[start:end]
                # 预清洗
                json_str = json_str.replace("'", '"').replace("None", "null").replace("False", "false").replace("True", "true")
                parsed_data = json.loads(json_str)
            except:
                try:
                    # AST 兜底
                    candidate = str_content[start:end]
                    py_candidate = candidate.replace("null", "None").replace("false", "False").replace("true", "True")
                    parsed_data = ast.literal_eval(py_candidate)
                except:
                    pass

        if parsed_data and isinstance(parsed_data, dict):
            if "reply_to_user" in parsed_data:
                content = parsed_data["reply_to_user"]
            
            if "analysis_data" in parsed_data:
                data = parsed_data["analysis_data"]
                print("\n🔍 [MICROSCOPE] 专家思维显微镜:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # 💰 监测胜利条件
                status = data.get("status") or parsed_data.get("status")
                
                if status == "concluded":
                    if not simulation_state["has_concluded"]: 
                        _save_to_etl(data) 
                        simulation_state["has_concluded"] = True 
                    
                    print("\n" + "💰"*20)
                    print("   LEADS CAPTURED -> 数据已入库，发送结束信号")
                    print("💰"*20 + "\n")
                
                print("-" * 40)
        else:
            if not content and not isinstance(last_msg, tuple) and hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                content = f"🛠️ 专家正在查阅知识库... \n(调用工具: {last_msg.tool_calls[0]['name']})"
                role = "tool_call"
            
        return role, content

    try:
        step_data = next(simulation_state["iterator"])
        simulation_state["current_step"] += 1
        
        role, content = process_step_data(step_data)
        print(f"✅ [NEXT] 步骤 {simulation_state['current_step']}: [{role}] {str(content)[:30]}...")

        # 🚦🚦🚦 关键：确保返回 Boolean 🚦🚦🚦
        final_state = step_data.get("is_concluded", False) # 默认 False (bool)
        
        if simulation_state["has_concluded"]:
            final_state = True # 强制 True (bool)

        return {
            "step": simulation_state["current_step"],
            "role": role,
            "content": content,
            "raw_state": final_state # 发送 True/False
        }
        
    except StopIteration:
        # 兜底
        if simulation_state["has_concluded"]:
             return {"step": -1, "content": "🏁 交易达成", "role": "system", "raw_state": True}

        print(f"⚠️ [NEXT] 异常停止。准备复苏...")
        if simulation_state["current_step"] < 20 and simulation_state["thread_id"]:
            try:
                recall_msg = simulation_state["last_human_message"] or "请继续你的建议。"
                nudge_inputs = {
                    "messages": [("user", recall_msg)], 
                    **simulation_state.get("static_context", {})
                }
                new_iterator = graph_app.stream(nudge_inputs, config={"configurable": {"thread_id": simulation_state["thread_id"]}, "recursion_limit": 100}, stream_mode="values")
                simulation_state["iterator"] = new_iterator
                step_data = next(simulation_state["iterator"])
                
                messages = step_data.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    _, last_content = get_safe_content(last_msg)
                    if last_content == recall_msg:
                         step_data = next(simulation_state["iterator"])

                simulation_state["current_step"] += 1
                role, content = process_step_data(step_data)
                
                # 复苏后状态检查
                final_state = step_data.get("is_concluded", False)
                if simulation_state["has_concluded"]: final_state = True

                return {
                    "step": simulation_state["current_step"],
                    "role": role,
                    "content": content,
                    "raw_state": final_state
                }
            except:
                pass
        
        return {"step": -1, "content": "🏁 仿真流程结束", "role": "system", "raw_state": True}
        
    except Exception as e:
        print(f"❌ [NEXT] 错误: {e}")
        return {"step": -1, "content": f"系统内部错误: {str(e)}", "role": "error"}


# --- [B] 聊天接口 ---
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not domain_mgr: return {"response": "System Error"}
    inputs = {
        "messages": [("user", request.message)],
        "domain": request.domain,
        "taxonomy_context": domain_mgr.get_expert_context(),
        "secret_mission": {"category": "u", "expert_term": "u", "novice_intent": "u"},
        "is_concluded": False, "turn_count": 0
    }
    result = graph_app.invoke(inputs, config={"configurable": {"thread_id": "chat_1"}})
    return {"response": result["messages"][-1].content}


# --- [C] 知识库管理接口 ---
@app.get("/api/taxonomy")
async def get_taxonomy():
    return domain_mgr.domain_db if domain_mgr else {"taxonomy": []}

@app.post("/api/taxonomy/add")
async def add_service(update: TaxonomyUpdate):
    if not domain_mgr: raise HTTPException(500, "System Error")
    current_db = domain_mgr.domain_db
    target = next((c for c in current_db["taxonomy"] if c["name"] == update.category), None)
    if not target:
        target = {"name": update.category, "services": []}
        current_db["taxonomy"].append(target)
    if update.service not in target["services"]:
        target["services"].append(update.service)
        _save_db(current_db)
        return {"status": "success"}
    return {"status": "skipped"}

@app.put("/api/taxonomy/category")
async def rename_category(update: CategoryRename):
    if not domain_mgr: raise HTTPException(500, "Domain Manager missing")
    current_db = domain_mgr.domain_db
    target_cat = next((c for c in current_db["taxonomy"] if c["name"] == update.old_name), None)
    if target_cat:
        if any(c["name"] == update.new_name for c in current_db["taxonomy"]): return {"status": "error", "message": "Exists"}
        target_cat["name"] = update.new_name
        _save_db(current_db)
        return {"status": "success"}
    return {"status": "error", "message": "Not found"}

@app.delete("/api/taxonomy/category")
async def delete_category(delete_req: CategoryDelete):
    if not domain_mgr: raise HTTPException(500, "Domain Manager missing")
    current_db = domain_mgr.domain_db
    initial_len = len(current_db["taxonomy"])
    current_db["taxonomy"] = [c for c in current_db["taxonomy"] if c["name"] != delete_req.category_name]
    if len(current_db["taxonomy"]) < initial_len:
        _save_db(current_db)
        return {"status": "success"}
    return {"status": "error", "message": "Not found"}

def _save_db(data):
    path = Path(__file__).parent / "domain_db" / "hr.json"
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)
    domain_mgr.load_domain_data()


# --- [D] 日志接口 ---
@app.get("/api/knowledge/logs")
async def get_logs():
    path = Path(__file__).resolve().parent.parent / "etl_factory" / "processing_log.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            try:
                raw_logs = json.load(f)
                # 去重 & 倒序
                unique_logs = []
                seen_queries = set()
                for log in raw_logs[::-1]:
                    query = log.get("query", "")
                    if query not in seen_queries:
                        unique_logs.append(log)
                        seen_queries.add(query)
                return unique_logs
            except:
                return []
    return []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)