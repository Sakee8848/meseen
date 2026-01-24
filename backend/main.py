import json
import os
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 引入智谱引擎
from simulation_engine.graph import generate_one_node

app = FastAPI()

# --- 配置 ---
DB_FILE = "knowledge_base.json"
CURRENT_CONTEXT = "通用保险咨询" 

# --- CORS ---
origins = ["http://localhost:3000", "http://localhost:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 数据模型 ---
class Node(BaseModel):
    id: str
    context: str
    question: str
    ai_rationale: str
    confidence: float
    next_nodes: List[str]

class TaskRequest(BaseModel):
    context: str

# --- 辅助函数：数据库操作 ---
def save_to_db(record: dict):
    """将数据追加写入 JSON 文件"""
    data = []
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass 
    
    data.append(record)
    
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.get("/")
def read_root():
    return {"status": "Mixin Brain Online", "current_task": CURRENT_CONTEXT}

@app.post("/api/set_task")
def set_task(task: TaskRequest):
    global CURRENT_CONTEXT
    CURRENT_CONTEXT = task.context
    print(f"🎯 任务目标已切换为: {CURRENT_CONTEXT}")
    return {"status": "updated", "context": CURRENT_CONTEXT}

@app.get("/api/queue", response_model=List[Node])
def get_queue():
    new_nodes = []
    try:
        print(f"🧠 AI 正在针对【{CURRENT_CONTEXT}】进行思考...")
        real_data = generate_one_node(context=CURRENT_CONTEXT)
        
        node = Node(
            id=f"NODE_{int(time.time())}",
            context=f"{CURRENT_CONTEXT} (Focus Mode)",
            question=real_data["question"], 
            ai_rationale=real_data["ai_rationale"], 
            confidence=real_data.get("confidence", 0.95),
            next_nodes=real_data.get("next_nodes", [])
        )
        new_nodes.append(node)
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        new_nodes.append(Node(
            id="ERR", context="系统错误", question=str(e), 
            ai_rationale="请检查后端终端日志", confidence=0.0, next_nodes=[]
        ))

    return new_nodes

@app.post("/api/approve/{node_id}")
def approve_node(node_id: str, node_data: Node):
    print(f"✅ 节点已确认: {node_data.question}")
    record = {
        "action": "APPROVED",
        "timestamp": time.time(),
        "context": node_data.context,
        "question": node_data.question,
        "rationale": node_data.ai_rationale,
        "next_logic": node_data.next_nodes
    }
    save_to_db(record)
    return {"status": "saved"}

# --- 核心新增：修正接口 ---
@app.post("/api/correct/{node_id}")
def correct_node(node_id: str, node_data: Node):
    print(f"💎 专家已修正节点: {node_data.question}")
    record = {
        "action": "CORRECTED",
        "timestamp": time.time(),
        "context": node_data.context,
        "question": node_data.question, # 这是你修改后的新问题
        "rationale": "Expert manually improved this question.",
        "next_logic": node_data.next_nodes
    }
    save_to_db(record)
    return {"status": "corrected_saved"}

@app.post("/api/reject/{node_id}")
def reject_node(node_id: str, node_data: Node):
    print(f"❌ 节点已驳回: {node_data.question}")
    record = {
        "action": "REJECTED",
        "timestamp": time.time(),
        "context": node_data.context,
        "question": node_data.question,
        "rationale": "Expert rejected this logic"
    }
    save_to_db(record)
    return {"status": "rejected_logged"}