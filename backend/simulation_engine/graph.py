import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from .prompts import EXPERT_PROMPT, NOVICE_PROMPT

load_dotenv()

# --- 1. 初始化模型 ---
llm = ChatOpenAI(
    model="glm-4",
    temperature=0.5, # 稍微降低温度，让 JSON 格式更稳定
    openai_api_base=os.environ.get("OPENAI_API_BASE"),
    openai_api_key=os.environ.get("OPENAI_API_KEY")
)

# --- 2. 定义状态 ---
class SimState(TypedDict):
    context: str
    hidden_fact: str
    messages: List[str]
    round_count: int
    result_node: dict

# --- 3. 定义节点 ---
def expert_node(state: SimState):
    history_str = "\n".join(state["messages"])
    prompt = EXPERT_PROMPT.format(context=state["context"], history=history_str)
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.replace("```json", "").replace("```", "").strip()
    
    # 尝试解析 JSON，如果失败则回退到普通文本
    try:
        data = json.loads(content)
        question = data.get("question", "AI 解析失败")
        rationale = data.get("rationale", "无逻辑解释")
        confidence = data.get("confidence", 0.8)
        # 格式化分支显示
        next_nodes = [f"{b['option']} -> {b['prediction']}" for b in data.get("next_branches", [])]
        
    except json.JSONDecodeError:
        print("JSON 解析失败，原始返回:", content)
        question = content
        rationale = "AI 返回了非标准格式，需人工清洗"
        confidence = 0.5
        next_nodes = ["解析错误 -> 请重试"]

    return {
        "messages": [f"专家: {question}"], 
        "round_count": state["round_count"] + 1,
        "result_node": {
            "question": question,
            "ai_rationale": rationale,
            "confidence": confidence,
            "next_nodes": next_nodes # 现在这里是真实的预测了！
        }
    }

def novice_node(state: SimState):
    last_question = state["messages"][-1]
    prompt = NOVICE_PROMPT.format(context=state["context"], hidden_fact=state["hidden_fact"])
    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=last_question)
    ])
    return {"messages": [f"客户: {response.content}"]}

def should_continue(state: SimState):
    if state["round_count"] >= 1: return END
    return "novice"

# --- 4. 构建图 ---
workflow = StateGraph(SimState)
workflow.add_node("expert", expert_node)
workflow.add_node("novice", novice_node)
workflow.set_entry_point("expert")
workflow.add_edge("novice", "expert")
workflow.add_conditional_edges("expert", should_continue, {"novice": "novice", END: END})
app_graph = workflow.compile()

def generate_one_node(context: str):
    import random
    facts = ["情况A", "情况B", "情况C"] # 简化，实际可扩展
    inputs = {
        "context": context,
        "hidden_fact": random.choice(facts),
        "messages": [],
        "round_count": 0,
        "result_node": {}
    }
    final_state = app_graph.invoke(inputs)
    
    # 再次确保返回的数据结构完整
    node_data = final_state["result_node"]
    if "next_nodes" not in node_data:
        node_data["next_nodes"] = ["是 -> (未预测)", "否 -> (未预测)"]
        
    return node_data