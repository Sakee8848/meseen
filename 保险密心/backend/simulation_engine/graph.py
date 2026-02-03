"""
🎭 保险密心 - AI 互博仿真图 (Insurance Graph Engine)
=====================================================
核心职能：编排保险顾问与企业客户的多轮对话仿真
"""

import json
import os
from typing import TypedDict, List, Optional, Annotated
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from .prompts import expert_prompt, novice_prompt, opening_prompt
from .domain_manager import DomainManager

# 加载环境变量
load_dotenv()


class SimulationState(TypedDict):
    """仿真状态定义"""
    messages: List[dict]
    mission: dict
    turn_count: int
    diagnosis_history: List[dict]
    final_result: Optional[dict]
    domain: str
    status: str


def create_insurance_simulation_graph(model_name: str = "glm-4"):
    """创建保险领域仿真图"""
    
    # 初始化 LLM (智谱 API)
    api_key = os.getenv("OPENAI_API_KEY")
    api_base = os.getenv("OPENAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4/")
    
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.7,
        max_tokens=2000,
        openai_api_key=api_key,
        openai_api_base=api_base
    )
    
    def initialize_simulation(state: SimulationState) -> SimulationState:
        """初始化仿真 - 生成企业客户的秘密任务"""
        domain = state.get("domain", "insurance")
        dm = DomainManager(domain)
        mission = dm.generate_secret_mission()
        
        state["mission"] = mission
        state["messages"] = []
        state["turn_count"] = 0
        state["diagnosis_history"] = []
        state["status"] = "initialized"
        
        return state
    
    def generate_opening(state: SimulationState) -> SimulationState:
        """生成企业客户的开场白"""
        mission = state["mission"]
        
        prompt = opening_prompt.format(
            secret_user_intent=mission["novice_intent"],
            secret_category=mission["category"],
            persona_role=mission.get("persona", "企业管理者"),
            persona_tone=mission.get("tone", "迷茫")
        )
        
        response = llm.invoke([HumanMessage(content=prompt)])
        opening = response.content.strip()
        
        # 记录开场白
        state["messages"].append({
            "role": "human",
            "content": f"我是{mission.get('persona', '企业管理者')}，{opening}",
            "step": 1
        })
        state["turn_count"] = 1
        state["status"] = "active"
        
        return state
    
    def expert_response(state: SimulationState) -> SimulationState:
        """保险顾问响应 - 诊断并追问"""
        domain = state.get("domain", "insurance")
        dm = DomainManager(domain)
        taxonomy_context = dm.get_expert_context()
        
        # 格式化对话历史
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
            # 解析 JSON 响应
            content = response.content.strip()
            # 尝试提取 JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            expert_data = json.loads(content)
        except json.JSONDecodeError:
            # 解析失败时的备用处理
            expert_data = {
                "diagnosis_reasoning": {"confidence": 0.5},
                "analysis_data": {"status": "active", "matched_service": "未知"},
                "reply_to_user": response.content[:200]
            }
        
        # 记录顾问响应
        state["messages"].append({
            "role": "ai",
            "content": expert_data.get("reply_to_user", "请您详细说说情况"),
            "step": state["turn_count"] + 1,
            "diagnosis": expert_data.get("diagnosis_reasoning", {})
        })
        
        # 更新诊断历史
        state["diagnosis_history"].append({
            "turn": state["turn_count"] + 1,
            "data": expert_data.get("analysis_data", {})
        })
        
        # 检查是否结束
        status = expert_data.get("analysis_data", {}).get("status", "active")
        if status == "concluded" or state["turn_count"] >= 6:
            state["status"] = "concluded"
            state["final_result"] = {
                "predicted_service": expert_data.get("analysis_data", {}).get("matched_service", "未诊断"),
                "confidence": expert_data.get("diagnosis_reasoning", {}).get("confidence", 0),
                "ground_truth": state["mission"]["expert_term"],
                "total_turns": state["turn_count"] + 1
            }
        
        state["turn_count"] += 1
        return state
    
    def novice_response(state: SimulationState) -> SimulationState:
        """企业客户响应 - 回答追问"""
        if state["status"] == "concluded":
            return state
        
        mission = state["mission"]
        
        # 格式化对话历史
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
        except json.JSONDecodeError:
            novice_data = {
                "response": "是的，就是这样的情况",
                "revealed_info": [],
                "hidden_info": []
            }
        
        # 记录客户响应
        state["messages"].append({
            "role": "human",
            "content": novice_data.get("response", "是的"),
            "step": state["turn_count"] + 1
        })
        
        state["turn_count"] += 1
        return state
    
    def should_continue(state: SimulationState) -> str:
        """判断是否继续仿真"""
        if state["status"] == "concluded":
            return "end"
        if state["turn_count"] >= 8:
            return "end"
        return "continue"
    
    # 构建状态图
    workflow = StateGraph(SimulationState)
    
    # 添加节点
    workflow.add_node("initialize", initialize_simulation)
    workflow.add_node("opening", generate_opening)
    workflow.add_node("expert", expert_response)
    workflow.add_node("novice", novice_response)
    
    # 设置边
    workflow.set_entry_point("initialize")
    workflow.add_edge("initialize", "opening")
    workflow.add_edge("opening", "expert")
    workflow.add_conditional_edges(
        "expert",
        should_continue,
        {
            "continue": "novice",
            "end": END
        }
    )
    workflow.add_edge("novice", "expert")
    
    return workflow.compile()


# 测试入口
if __name__ == "__main__":
    graph = create_insurance_simulation_graph()
    
    initial_state = {
        "messages": [],
        "mission": {},
        "turn_count": 0,
        "diagnosis_history": [],
        "final_result": None,
        "domain": "insurance",
        "status": "pending"
    }
    
    result = graph.invoke(initial_state)
    print("\n📊 仿真结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
