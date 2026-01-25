import json
import re
import operator
import os
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from .prompts import expert_prompt, novice_prompt

# 👇 1. 引入 dotenv 库
from dotenv import load_dotenv

# 👇 2. 加载 .env 文件 (它会自动找 OPENAI_API_KEY 和 OPENAI_API_BASE)
load_dotenv()

# =======================================================
# 🛡️ 配置 LLM (智谱 OpenAI 兼容模式)
# =======================================================

# 从环境变量读取 (对应你 .env 里的名字)
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4/") # 默认值防呆

if not api_key:
    raise ValueError("❌ 错误：未找到 OPENAI_API_KEY！请检查 .env 文件。")

# 初始化 LangChain 的 OpenAI 客户端
# 虽然名字叫 ChatOpenAI，但指向了智谱的服务器
llm = ChatOpenAI(
    model="glm-4",           # 智谱的模型名称 (也可以改 glm-4-flash, glm-4-plus)
    temperature=0.1,         # 温度低一点，让专家更严谨
    openai_api_key=api_key,  # 传入智谱 Key
    openai_api_base=api_base # 传入智谱 URL
)

# =======================================================
# 🧠 下面是核心逻辑 (不需要改动)
# =======================================================

def parse_json_robust(text: str):
    text = text.strip()
    try:
        return json.loads(text)
    except:
        pass
    if "```" in text:
        pattern = r"```(?:json)?\s*(.*?)\s*```"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            text = match.group(1)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        json_str = match.group(0)
        try:
            json_str = json_str.replace('\n', ' ')
            return json.loads(json_str)
        except:
            pass
    return None

class SimulationState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    domain: str
    taxonomy_context: str
    secret_mission: dict
    is_concluded: bool
    turn_count: int

def expert_node(state: SimulationState):
    chain = expert_prompt | llm
    response = chain.invoke({
        "domain": state["domain"],
        "taxonomy_context": state["taxonomy_context"],
        "messages": state["messages"]
    })
    
    data = parse_json_robust(response.content)
    
    if data:
        question = data.get("question", str(data))
        is_done = data.get("is_conclusion", False)
        # 容错处理：有时 LLM 会返回字符串 "true"
        if isinstance(is_done, str) and is_done.lower() == 'true':
            is_done = True
    else:
        question = response.content
        is_done = False
        
    return {
        "messages": [AIMessage(content=question)],
        "is_concluded": is_done,
        "turn_count": state["turn_count"] + 1
    }

def novice_node(state: SimulationState):
    if state["is_concluded"]:
        return {"messages": []}

    chain = novice_prompt | llm
    mission = state["secret_mission"]
    category = mission.get("category_name", mission.get("category", "通用咨询"))

    response = chain.invoke({
        "secret_expert_term": mission["expert_term"],
        "secret_user_intent": mission["novice_intent"],
        "secret_category": category,
        "messages": state["messages"]
    })
    
    data = parse_json_robust(response.content)
    if data:
        reply = data.get("response", str(data))
    else:
        reply = response.content
        
    return {"messages": [HumanMessage(content=reply)]}

# --- 组装工作流 ---
workflow = StateGraph(SimulationState)
workflow.add_node("expert", expert_node)
workflow.add_node("novice", novice_node)

workflow.set_entry_point("expert")
workflow.add_edge("expert", "novice")
workflow.add_edge("novice", END)

app = workflow.compile()