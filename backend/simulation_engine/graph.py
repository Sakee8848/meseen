"""
🔄 Meseeing 密心 - LangGraph 多轮博弈工作流 V6.0
=================================================
核心改变：
1. 实现真正的多轮循环（最多 10 轮）
2. 专家必须追问至少 2-3 次才能得出结论
3. 记录完整的诊断推理链
4. 计算每轮的信息增益
"""

import json
import re
import operator
import os
from typing import TypedDict, Annotated, List, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from .prompts import expert_prompt, novice_prompt, opening_prompt
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# =======================================================
# 🛡️ 配置 LLM
# =======================================================
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4/")

if not api_key:
    raise ValueError("❌ 错误：未找到 OPENAI_API_KEY！请检查 .env 文件。")

llm = ChatOpenAI(
    model="glm-4",
    temperature=0.3,  # 稍微提高，让对话更自然
    openai_api_key=api_key,
    openai_api_base=api_base
)

# =======================================================
# 🔧 工具函数
# =======================================================
def parse_json_robust(text: str) -> Optional[dict]:
    """健壮的 JSON 解析器"""
    text = text.strip()
    
    # 尝试直接解析
    try:
        return json.loads(text)
    except:
        pass
    
    # 尝试从 markdown 代码块提取
    if "```" in text:
        pattern = r"```(?:json)?\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
    
    # 尝试提取 JSON 对象
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            json_str = match.group(0).replace('\n', ' ')
            return json.loads(json_str)
        except:
            pass
    
    return None


# =======================================================
# 📊 状态定义 (增强版)
# =======================================================
class SimulationState(TypedDict):
    """仿真状态 - 包含完整的诊断追踪"""
    messages: Annotated[List[BaseMessage], operator.add]
    domain: str
    taxonomy_context: str
    secret_mission: dict  # 小白的秘密任务
    is_concluded: bool
    turn_count: int
    max_turns: int  # 最大轮次限制
    
    # 🆕 诊断追踪数据
    diagnosis_trace: List[dict]  # 每轮的诊断推理记录
    key_questions: List[dict]  # 关键追问列表
    eliminated_categories: List[str]  # 已排除的分类
    confidence_history: List[float]  # 置信度变化曲线
    final_diagnosis: Optional[dict]  # 最终诊断结果


# =======================================================
# 🎭 生成开场白节点
# =======================================================
def generate_opening_node(state: SimulationState) -> dict:
    """生成小白的开场白（确保不泄露答案）"""
    mission = state["secret_mission"]
    
    chain = opening_prompt | llm
    response = chain.invoke({
        "secret_user_intent": mission.get("novice_intent", ""),
        "secret_category": mission.get("category", ""),
        "persona_role": mission.get("persona", "普通人"),
        "persona_tone": mission.get("tone", "焦虑")
    })
    
    opening = response.content.strip()
    # 去掉可能的引号
    opening = opening.strip('"\'')
    
    print(f"   💬 小白开场: {opening[:50]}...")
    
    return {
        "messages": [HumanMessage(content=opening)],
        "turn_count": 1
    }


# =======================================================
# 🤖 专家诊断节点
# =======================================================
def expert_node(state: SimulationState) -> dict:
    """专家进行诊断追问"""
    chain = expert_prompt | llm
    
    response = chain.invoke({
        "domain": state["domain"],
        "taxonomy_context": state["taxonomy_context"],
        "messages": state["messages"]
    })
    
    data = parse_json_robust(response.content)
    
    # 提取诊断数据
    diagnosis_trace_entry = {}
    reply = ""
    is_done = False
    confidence = 0.0
    
    if data:
        # 提取诊断推理
        reasoning = data.get("diagnosis_reasoning", {})
        analysis = data.get("analysis_data", {})
        reply = data.get("reply_to_user", str(data))
        
        diagnosis_trace_entry = {
            "turn": state["turn_count"],
            "hypotheses": reasoning.get("current_hypotheses", []),
            "key_signals": reasoning.get("key_signals", []),
            "question_purpose": reasoning.get("next_question_purpose", ""),
            "eliminated": reasoning.get("eliminated_categories", []),
            "confidence": reasoning.get("confidence", 0.5),
            "diagnosis": analysis.get("diagnosis", ""),
            "matched_service": analysis.get("matched_service", "")
        }
        
        confidence = reasoning.get("confidence", 0.5)
        
        # 判断是否结束
        status = analysis.get("status", "active")
        is_done = (status == "concluded" and state["turn_count"] >= 3)  # 至少 3 轮
        
    else:
        reply = response.content
        diagnosis_trace_entry = {
            "turn": state["turn_count"],
            "raw_response": reply[:200]
        }
    
    print(f"   🤖 专家追问 (T{state['turn_count']}): {reply[:50]}...")
    
    # 更新追踪数据
    new_trace = state.get("diagnosis_trace", []) + [diagnosis_trace_entry]
    new_confidence = state.get("confidence_history", []) + [confidence]
    new_eliminated = state.get("eliminated_categories", []) + diagnosis_trace_entry.get("eliminated", [])
    
    # 如果结束，记录最终诊断
    final_diagnosis = None
    if is_done and data:
        final_diagnosis = {
            "service": data.get("analysis_data", {}).get("matched_service", ""),
            "diagnosis": data.get("analysis_data", {}).get("diagnosis", ""),
            "confidence": confidence,
            "total_turns": state["turn_count"],
            "key_questions": [t.get("question_purpose", "") for t in new_trace if t.get("question_purpose")]
        }
    
    return {
        "messages": [AIMessage(content=reply)],
        "is_concluded": is_done,
        "diagnosis_trace": new_trace,
        "confidence_history": new_confidence,
        "eliminated_categories": list(set(new_eliminated)),
        "final_diagnosis": final_diagnosis
    }


# =======================================================
# 👤 小白回复节点
# =======================================================
def novice_node(state: SimulationState) -> dict:
    """小白根据专家追问进行回复"""
    if state["is_concluded"]:
        return {"messages": []}
    
    mission = state["secret_mission"]
    chain = novice_prompt | llm
    
    response = chain.invoke({
        "secret_user_intent": mission.get("novice_intent", ""),
        "secret_category": mission.get("category", ""),
        "persona_role": mission.get("persona", "普通人"),
        "persona_tone": mission.get("tone", "焦虑"),
        "messages": state["messages"]
    })
    
    data = parse_json_robust(response.content)
    
    if data:
        reply = data.get("response", str(data))
        # 记录透露和隐藏的信息
        revealed = data.get("revealed_info", [])
        hidden = data.get("hidden_info", [])
        print(f"   👤 小白回复: {reply[:50]}... (透露: {len(revealed)}, 隐藏: {len(hidden)})")
    else:
        reply = response.content
        print(f"   👤 小白回复: {reply[:50]}...")
    
    return {
        "messages": [HumanMessage(content=reply)],
        "turn_count": state["turn_count"] + 1
    }


# =======================================================
# 🔀 条件判断函数
# =======================================================
def should_continue(state: SimulationState) -> str:
    """判断是否继续对话"""
    # 如果已经结束
    if state.get("is_concluded", False):
        print(f"   ✅ 诊断完成! 总轮次: {state['turn_count']}")
        return "end"
    
    # 如果超过最大轮次
    max_turns = state.get("max_turns", 10)
    if state["turn_count"] >= max_turns:
        print(f"   ⚠️ 达到最大轮次 ({max_turns})，强制结束")
        return "end"
    
    # 继续对话
    return "continue"


# =======================================================
# 🔄 组装工作流 (多轮循环版)
# =======================================================
workflow = StateGraph(SimulationState)

# 添加节点
workflow.add_node("opening", generate_opening_node)
workflow.add_node("expert", expert_node)
workflow.add_node("novice", novice_node)

# 设置入口：先生成开场白
workflow.set_entry_point("opening")

# 开场白后进入专家诊断
workflow.add_edge("opening", "expert")

# 专家诊断后进入小白回复
workflow.add_edge("expert", "novice")

# 小白回复后，条件判断是否继续
workflow.add_conditional_edges(
    "novice",
    should_continue,
    {
        "continue": "expert",  # 继续下一轮追问
        "end": END            # 结束对话
    }
)

# 编译工作流
app = workflow.compile()


# =======================================================
# 🧪 测试函数
# =======================================================
def run_simulation_test():
    """运行一次完整的仿真测试"""
    from .domain_manager import DomainManager
    
    dm = DomainManager("hr")
    mission = dm.generate_secret_mission()
    
    print("=" * 60)
    print("🎭 开始 AI 互博仿真")
    print("=" * 60)
    print(f"📋 秘密任务: {mission['novice_intent'][:50]}...")
    print(f"🎯 目标分类: {mission['expert_term']}")
    print(f"👤 角色: {mission.get('persona', 'N/A')} ({mission.get('tone', 'N/A')})")
    print("-" * 60)
    
    initial_state = {
        "messages": [],
        "domain": "hr",
        "taxonomy_context": dm.get_expert_context(),
        "secret_mission": mission,
        "is_concluded": False,
        "turn_count": 0,
        "max_turns": 8,
        "diagnosis_trace": [],
        "key_questions": [],
        "eliminated_categories": [],
        "confidence_history": [],
        "final_diagnosis": None
    }
    
    config = {"recursion_limit": 50}
    final_state = app.invoke(initial_state, config=config)
    
    print("-" * 60)
    print("📊 仿真结果")
    print(f"   总轮次: {final_state['turn_count']}")
    print(f"   置信度曲线: {final_state.get('confidence_history', [])}")
    print(f"   排除分类: {final_state.get('eliminated_categories', [])}")
    
    if final_state.get("final_diagnosis"):
        fd = final_state["final_diagnosis"]
        print(f"   最终诊断: {fd.get('service', 'N/A')}")
        print(f"   诊断置信度: {fd.get('confidence', 0):.2%}")
    
    return final_state


if __name__ == "__main__":
    run_simulation_test()