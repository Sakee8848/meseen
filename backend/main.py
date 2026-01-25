import json
import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage

# 引入核心模块
from simulation_engine.domain_manager import DomainManager
from simulation_engine.graph import app as graph_app

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}

# =========================================================================
#  KnowledgeRecorder
# =========================================================================
class KnowledgeRecorder:
    def __init__(self, filename="knowledge_base.json"):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def save_run(self, domain, secret_mission, history):
        path = []
        for i in range(0, len(history) - 1, 2):
            if i+1 < len(history):
                expert_msg = history[i].content
                novice_msg = history[i+1].content
                path.append({
                    "step": (i // 2) + 1,
                    "expert_question": expert_msg,
                    "novice_response": novice_msg
                })

        final_conclusion = history[-1].content if history else ""
        expert_diagnosis = secret_mission.get("expert_term", "未分类服务")
        secret_intent = secret_mission.get("novice_intent", "未知用户需求")

        record = {
            "id": f"sim_{int(time.time())}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "domain": domain,
            "secret_intent": secret_intent,
            "expert_diagnosis": expert_diagnosis,
            "dialogue_path": path,
            "final_conclusion": final_conclusion
        }

        with open(self.filename, 'r+', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            
            data.append(record)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ [Recorder] 成功保存案例: {expert_diagnosis}")

    def get_all(self):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return []

recorder = KnowledgeRecorder()

# =========================================================================
#  API 接口
# =========================================================================

class StartReq(BaseModel):
    domain: str = "hr"

@app.post("/api/start")
def start_simulation(req: StartReq):
    try:
        dm = DomainManager(req.domain)
        secret = dm.generate_secret_mission()
        expert_ctx = dm.get_expert_context()
        
        session_id = "sim_demo"
        
        sessions[session_id] = {
            "messages": [HumanMessage(content="你好，我想咨询一些业务问题。")],
            "domain": req.domain,
            "taxonomy_context": expert_ctx,
            "secret_mission": secret,
            "is_concluded": False,
            "turn_count": 0
        }
        
        print(f"🚀 [Start] 新任务目标: {secret['expert_term']}")
        
        return {
            "msg": "Simulation Started", 
            "secret_preview": secret['novice_intent'], 
            "expert_map": expert_ctx
        }
    except Exception as e:
        print(f"❌ Start Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/next")
def next_turn():
    session_id = "sim_demo"
    state = sessions.get(session_id)
    
    if not state:
        return {"error": "Please start simulation first"}
    
    current_secret = state.get("secret_mission", {})
    
    # --- 情况 A: 已经是结束状态 (用户看完了诊断消息，再次点击“下一步”) ---
    # 这时候我们才真正告诉前端：结束了！
    if state["is_concluded"]:
        diagnosis = current_secret.get("expert_term", "Unknown")
        return {
            "status": "Finished", 
            "concluded": True,
            "history": _format_history(state["messages"]),
            "final_diagnosis": diagnosis,
            "expert_diagnosis": diagnosis,
            "diagnosis": diagnosis, 
            "final_conclusion": state["messages"][-1].content
        }

    # --- 情况 B: 还在运行中，计算下一轮 ---
    try:
        result = graph_app.invoke(state)
        
        # 补丁：防止 secret 丢失
        if "secret_mission" not in result:
             result["secret_mission"] = current_secret
             
        sessions[session_id] = result # 更新内存状态

        # --- 核心逻辑：刚刚触发了结束 ---
        if result["is_concluded"]:
            diagnosis = current_secret.get("expert_term", "未分类服务")
            
            # 1. 保存数据 (确保星图更新)
            recorder.save_run(
                domain=result["domain"],
                secret_mission=current_secret, 
                history=result["messages"][1:] 
            )
            print(f"🏁 [Finish] 确诊结果: {diagnosis}")

            # 2. 【关键欺骗】构造系统消息
            system_msg = AIMessage(content=f"✅ 【系统诊断完成】\n\n经过多轮分析，专家为您匹配的最佳服务是：\n\n👉 **{diagnosis}**\n\n(该案例已自动归档至知识星图)")
            
            # 3. 将这条消息追加到内存历史中 (为了下一次点击能读到)
            result["messages"].append(system_msg)
            sessions[session_id] = result 

            # 4. 【欺骗前端】告诉它“还没结束” (concluded=False)
            # 这样它就会乖乖渲染上面那条 system_msg 气泡！
            
            new_latest = result["messages"][-2:]
            formatted_latest = []
            for m in new_latest:
                role = "expert" if isinstance(m, AIMessage) else "novice"
                formatted_latest.append({"role": role, "content": m.content})

            return {
                "status": "Running", # <--- 假装还在跑
                "concluded": False,  # <--- 假装没结束 !!!
                "turn": result["turn_count"] + 1, # 强制刷新
                "latest_exchange": formatted_latest
            }

        # --- 正常对话中 ---
        latest_msgs = result["messages"][-2:]
        formatted_exchange = []
        for m in latest_msgs:
            role = "expert" if isinstance(m, AIMessage) else "novice"
            formatted_exchange.append({"role": role, "content": m.content})

        return {
            "status": "Running",
            "turn": result["turn_count"],
            "concluded": False,
            "latest_exchange": formatted_exchange
        }

    except Exception as e:
        print(f"❌ Graph Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/knowledge")
def get_knowledge_graph():
    data = recorder.get_all()
    return {"total": len(data), "records": data}

def _format_history(msgs):
    logs = []
    for m in msgs:
        role = "Expert (AI)" if isinstance(m, AIMessage) else "Novice (User)"
        logs.append(f"[{role}]: {m.content}")
    return logs

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)