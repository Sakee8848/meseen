"""
🏦 保险密心 (Insurance Meseeing) - FastAPI 后端主入口
=====================================================
专为人力资源行业保险服务供应商设计的专家知识库提取工具

版本：1.0.0
领域：企业保险服务（团体险、雇主责任、弹性福利等）
"""

import json
import os
import uuid
import random
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量（智谱 API 配置）
load_dotenv()

# 路径锚定
ROOT_DIR = Path(__file__).resolve().parent
ETL_DIR = ROOT_DIR.parent / "etl_factory"
INBOX_PATH = ETL_DIR / "processing_log.json"

app = FastAPI(
    title="保险密心 API",
    description="人力资源行业保险服务供应商的专家知识库提取工具",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
simulation_state = {
    "state": None,
    "step_count": 0,
    "mission": None,
    "domain": "insurance"
}


# ==========================================
# 📊 数据模型
# ==========================================

class SimulationStartRequest(BaseModel):
    domain: str = "insurance"
    config: Optional[dict] = None


class BatchIngestRequest(BaseModel):
    items: List[dict]


# ==========================================
# 🎮 仿真控制接口
# ==========================================

@app.post("/api/start")
@app.post("/api/simulation/start")
async def start_simulation(data: Dict[str, Any] = None):
    """启动一次新的保险需求诊断仿真"""
    global simulation_state
    
    try:
        from simulation_engine.domain_manager import DomainManager
        from simulation_engine.graph import create_insurance_simulation_graph
        
        domain = "insurance"
        if data:
            domain = data.get("domain", "insurance")
        
        dm = DomainManager(domain)
        mission = dm.generate_secret_mission()
        
        simulation_state = {
            "state": {
                "messages": [],
                "mission": mission,
                "turn_count": 0,
                "diagnosis_history": [],
                "final_result": None,
                "domain": domain,
                "status": "initialized"
            },
            "step_count": 0,
            "mission": mission,
            "domain": domain
        }
        
        return {
            "status": "initialized",
            "message": "保险诊断仿真已初始化",
            "mission_preview": {
                "category": mission.get("category_short", mission["category"]),
                "persona": mission.get("persona", "企业管理者"),
                "industry": mission.get("industry", "未知"),
                "company_size": mission.get("company_size", "未知")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/next")
@app.post("/api/simulation/next")
async def next_step():
    """执行仿真的下一步"""
    global simulation_state
    
    if not simulation_state["state"]:
        raise HTTPException(status_code=400, detail="请先调用 /api/start 初始化仿真")
    
    try:
        from simulation_engine.graph import create_insurance_simulation_graph
        from simulation_engine.prompts import expert_prompt, novice_prompt, opening_prompt
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        
        state = simulation_state["state"]
        mission = state["mission"]
        step = simulation_state["step_count"]
        
        # 初始化 LLM (智谱 glm-4)
        api_key = os.getenv("OPENAI_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4/")
        llm = ChatOpenAI(
            model="glm-4",
            temperature=0.7,
            max_tokens=2000,
            openai_api_key=api_key,
            openai_api_base=api_base
        )
        
        # 步骤: 开场白 → 顾问1 → 客户1 → 顾问2 → ...
        if step == 0:
            # 生成开场白
            from simulation_engine.domain_manager import DomainManager
            dm = DomainManager(state["domain"])
            
            prompt = opening_prompt.format(
                secret_user_intent=mission["novice_intent"],
                secret_category=mission["category"],
                persona_role=mission.get("persona", "企业管理者"),
                persona_tone=mission.get("tone", "迷茫")
            )
            
            response = llm.invoke([HumanMessage(content=prompt)])
            opening = response.content.strip()
            
            state["messages"].append({
                "step": 1,
                "role": "human",
                "content": f"我是{mission.get('persona', '企业管理者')}，{opening}"
            })
            state["turn_count"] = 1
            state["status"] = "active"
            
        elif step % 2 == 1:
            # 保险顾问响应
            from simulation_engine.domain_manager import DomainManager
            dm = DomainManager(state["domain"])
            taxonomy_context = dm.get_expert_context()
            
            messages_text = "\n".join([
                f"{'客户' if m['role'] == 'human' else '顾问'}: {m['content']}"
                for m in state["messages"]
            ])
            
            prompt = expert_prompt.format(
                taxonomy_context=taxonomy_context,
                messages=messages_text
            )
            
            response = llm.invoke([HumanMessage(content=prompt)])
            
            try:
                content = response.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                expert_data = json.loads(content)
            except:
                expert_data = {
                    "diagnosis_reasoning": {"confidence": 0.5},
                    "analysis_data": {"status": "active", "matched_service": "待诊断"},
                    "reply_to_user": "请您详细说说企业的情况"
                }
            
            state["messages"].append({
                "step": state["turn_count"] + 1,
                "role": "ai",
                "content": expert_data.get("reply_to_user", "请详细说说"),
                "diagnosis": expert_data.get("diagnosis_reasoning", {})
            })
            
            state["diagnosis_history"].append({
                "turn": state["turn_count"] + 1,
                "data": expert_data.get("analysis_data", {})
            })
            
            status = expert_data.get("analysis_data", {}).get("status", "active")
            confidence = expert_data.get("diagnosis_reasoning", {}).get("confidence", 0)
            
            if status == "concluded" or state["turn_count"] >= 6:
                state["status"] = "concluded"
                state["final_result"] = {
                    "ai_prediction": expert_data.get("analysis_data", {}).get("matched_service", "未诊断"),
                    "confidence": confidence,
                    "ground_truth": mission["expert_term"],
                    "category": mission["category"],
                    "total_turns": state["turn_count"] + 1,
                    "diagnosis_correct": (str(expert_data.get("analysis_data", {}).get("matched_service", "")) in str(mission["expert_term"])) or (str(mission["expert_term"]) in str(expert_data.get("analysis_data", {}).get("matched_service", "")))
                }
                # 自动保存到 ETL
                _save_to_etl(state)
            
            state["turn_count"] += 1
            
        else:
            # 企业客户响应
            messages_text = "\n".join([
                f"{'客户' if m['role'] == 'human' else '顾问'}: {m['content']}"
                for m in state["messages"]
            ])
            
            prompt = novice_prompt.format(
                secret_user_intent=mission["novice_intent"],
                secret_category=mission["category"],
                persona_role=mission.get("persona", "企业管理者"),
                persona_tone=mission.get("tone", "迷茫"),
                messages=messages_text
            )
            
            response = llm.invoke([HumanMessage(content=prompt)])
            
            try:
                content = response.content.strip()
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                novice_data = json.loads(content)
            except:
                novice_data = {"response": "是的，情况就是这样"}
            
            state["messages"].append({
                "step": state["turn_count"] + 1,
                "role": "human",
                "content": novice_data.get("response", "是的")
            })
            state["turn_count"] += 1
        
        simulation_state["step_count"] += 1
        simulation_state["state"] = state
        
        return {
            "status": state["status"],
            "step": simulation_state["step_count"],
            "current_turn": state["turn_count"],
            "last_message": state["messages"][-1] if state["messages"] else None,
            "final_result": state.get("final_result")
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def _save_to_etl(state: dict):
    """将完成的仿真保存到 ETL 收件箱"""
    try:
        ETL_DIR.mkdir(parents=True, exist_ok=True)
        
        inbox = []
        if INBOX_PATH.exists():
            with open(INBOX_PATH, "r", encoding="utf-8") as f:
                inbox = json.load(f)
        
        mission = state["mission"]
        final = state.get("final_result", {})
        
        record = {
            "id": f"ins_{uuid.uuid4().hex[:8]}",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "domain": "insurance",
            "query": state["messages"][0]["content"] if state["messages"] else "",
            "ai_prediction": final.get("ai_prediction", "未诊断"),
            "ground_truth": mission["expert_term"],
            "category": mission["category"],
            "confidence": final.get("confidence", 0),
            "persona": mission.get("persona", "企业管理者"),
            "industry": mission.get("industry", "未知"),
            "company_size": mission.get("company_size", "未知"),
            "tone": mission.get("tone", "迷茫"),
            "dialogue_path": state["messages"],
            "total_turns": state["turn_count"],
            "diagnosis_correct": final.get("diagnosis_correct", False),
            "source": "insurance_meseeing_v1",
            "status": "pending"
        }
        
        inbox.append(record)
        
        with open(INBOX_PATH, "w", encoding="utf-8") as f:
            json.dump(inbox, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 保险诊断记录已保存: {record['id']}")
        
    except Exception as e:
        print(f"❌ 保存到 ETL 失败: {e}")


# ==========================================
# 📥 ETL 收件箱接口
# ==========================================

@app.get("/api/etl/inbox")
async def get_etl_inbox():
    """获取 ETL 收件箱内容"""
    try:
        if INBOX_PATH.exists():
            with open(INBOX_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ingest")
@app.post("/api/batch_ingest")
async def universal_ingest(request: Request):
    """万能入库接口 - 将审核通过的记录入库到知识库"""
    try:
        body = await request.json()
        items = body.get("items", [body])  # 支持单条和批量
        
        db_path = ROOT_DIR / "domain_db" / "insurance.json"
        
        with open(db_path, "r", encoding="utf-8") as f:
            db = json.load(f)
        
        ingested = []
        for item in items:
            item_id = item.get("id")
            domain = item.get("domain", "insurance")
            
            # 从收件箱获取完整记录
            inbox_record = None
            if INBOX_PATH.exists():
                with open(INBOX_PATH, "r", encoding="utf-8") as f:
                    inbox = json.load(f)
                    for rec in inbox:
                        if rec.get("id") == item_id:
                            inbox_record = rec
                            break
            
            if not inbox_record:
                continue
            
            # 找到对应类别并添加 trace_record
            category_name = inbox_record.get("category", "")
            service_name = inbox_record.get("ground_truth", "")
            
            for cat in db.get("taxonomy", []):
                # 兼容性匹配：类别名称
                if category_name in cat["name"] or cat["name"] in category_name:
                    if "trace_records" not in cat:
                        cat["trace_records"] = {}
                    
                    # 🔧 修正：使用完整的 service_name 作为 key，与 HR 领域保持一致
                    service_key = service_name
                    
                    if service_key not in cat["trace_records"]:
                        cat["trace_records"][service_key] = []
                    
                    # 添加追踪记录
                    trace = {
                        "id": inbox_record["id"],
                        "timestamp": inbox_record["timestamp"],
                        "query": inbox_record["query"],
                        "ai_prediction": inbox_record["ai_prediction"],
                        "confidence": inbox_record["confidence"],
                        "source": inbox_record.get("source", "insurance_meseeing"),
                        "persona": inbox_record.get("persona", ""),
                        "industry": inbox_record.get("industry", ""),
                        "tone": inbox_record.get("tone", ""),
                        "dialogue_path": inbox_record.get("dialogue_path", []),
                        "total_turns": inbox_record.get("total_turns", 0),
                        "diagnosis_correct": inbox_record.get("diagnosis_correct", False),
                        "ground_truth": service_name
                    }
                    
                    cat["trace_records"][service_key].append(trace)
                    ingested.append(item_id)
                    print(f"✅ 入库成功: {service_key} -> {cat['name']}")
                    break
        
        # 保存更新后的知识库
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        
        # 从收件箱移除已入库的记录
        if INBOX_PATH.exists():
            with open(INBOX_PATH, "r", encoding="utf-8") as f:
                inbox = json.load(f)
            inbox = [rec for rec in inbox if rec.get("id") not in ingested]
            with open(INBOX_PATH, "w", encoding="utf-8") as f:
                json.dump(inbox, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "ingested_count": len(ingested),
            "ingested_ids": ingested
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 📊 知识库统计接口
# ==========================================

@app.get("/api/taxonomy")
async def get_taxonomy(domain: str = "insurance"):
    """获取保险服务分类体系"""
    db_path = ROOT_DIR / "domain_db" / f"{domain}.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 返回完整对象格式，前端期望 {taxonomy: [...]}
    return {"taxonomy": data.get("taxonomy", [])}


@app.get("/api/coverage")
async def get_coverage(domain: str = "insurance"):
    """获取知识库覆盖率统计"""
    db_path = ROOT_DIR / "domain_db" / f"{domain}.json"
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    stats = {"categories": [], "total_services": 0, "covered_services": 0}
    total_trace_count = 0
    
    for cat in data.get("taxonomy", []):
        cat_stats = {
            "name": cat["name"],
            "services": []
        }
        for svc in cat.get("services", []):
            stats["total_services"] += 1
            # 🔧 增强：兼容完整名和简短名作为 key
            traces = cat.get("trace_records", {}).get(svc, [])
            if not traces:
                svc_short = svc.split(" ")[0] if " " in svc else svc
                traces = cat.get("trace_records", {}).get(svc_short, [])
                
            trace_count = len(traces)
            total_trace_count += trace_count
            if traces:
                stats["covered_services"] += 1
            cat_stats["services"].append({
                "name": svc,
                "trace_count": trace_count
            })
        stats["categories"].append(cat_stats)
    
    # 计算覆盖率 - 使用与前端期望一致的字段名
    service_coverage = stats["covered_services"] / stats["total_services"] if stats["total_services"] > 0 else 0
    
    # 预估总知识点 (基于领域维度: 行业×公司规模×角色×紧急度)
    dimensions = {
        "industries": {"name": "行业", "count": 10, "description": "制造/科技/金融等"},
        "company_sizes": {"name": "公司规模", "count": 5, "description": "10人/50人/100人等"},
        "personas": {"name": "角色", "count": 8, "description": "HR/财务/老板等"},
        "urgency": {"name": "紧急度", "count": 3, "description": "低/中/高"}
    }
    
    estimated_total = stats["total_services"] * 10 * 5 * 8 * 3  # 服务数 × 各维度
    coverage_rate = (total_trace_count / estimated_total * 100) if estimated_total > 0 else 0
    
    return {
        # 前端期望的核心字段
        "coverage_rate": coverage_rate,
        "covered_count": total_trace_count,
        "estimated_total": estimated_total,
        "service_node_count": stats["total_services"],
        "covered_service_count": stats["covered_services"],
        "service_coverage_rate": service_coverage * 100,
        
        # 公式说明
        "formula": {
            "expression": f"覆盖率 = 已生成对话数 / 预估总知识点 = {total_trace_count} / {estimated_total}",
            "estimated_total_formula": f"服务数({stats['total_services']}) × 行业(10) × 规模(5) × 角色(8) × 紧急度(3)",
            "note": "覆盖率基于真实业务场景多维度预估"
        },
        "dimensions": dimensions,
        
        # 原始数据
        "categories": stats["categories"]
    }


# ==========================================
# 🤖 批量 AI 互博控制接口
# ==========================================

try:
    from batch_runner import InsuranceBatchRunner
    BATCH_AVAILABLE = True
except ImportError:
    BATCH_AVAILABLE = False


@app.post("/api/batch/start")
async def batch_start(request: Request):
    """启动批量保险诊断任务"""
    if not BATCH_AVAILABLE:
        raise HTTPException(status_code=501, detail="批量模块未加载")
    
    body = await request.json()
    count = body.get("count", 10)
    
    runner = InsuranceBatchRunner()
    runner.start(count)
    
    return {"status": "started", "target_count": count}


@app.get("/api/batch/status")
async def batch_status():
    """获取批量任务状态"""
    if not BATCH_AVAILABLE:
        return {"available": False}
    
    runner = InsuranceBatchRunner()
    return runner.get_status()


# ==========================================
# 🏥 健康检查
# ==========================================

@app.get("/")
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "保险密心 API",
        "version": "1.0.0",
        "domain": "insurance"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
