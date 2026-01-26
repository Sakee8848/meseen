import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# ==========================================
# 1. 环境准备
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
sys.path.append(str(BASE_DIR))

# 引入专家提示词
from backend.simulation_engine.prompts import expert_prompt
from backend.simulation_engine.domain_manager import DomainManager

api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4/")

if not api_key:
    raise ValueError("❌ 未找到 API Key")

print("✅ ETL 智能质检引擎启动...")

# ==========================================
# 2. 定义 AI 角色
# ==========================================
llm = ChatOpenAI(
    model="glm-4",
    temperature=0.01,
    openai_api_key=api_key,
    openai_api_base=api_base
)

extract_prompt = ChatPromptTemplate.from_template("""
你是一个专业的数据挖掘专家。你的任务是从非结构化的“原始对话记录”中，提取出用户意图和专家服务分类。
【原始数据】
{raw_text}
【提取要求】
1. 分析用户的核心痛点，总结为 "novice_intent"。
2. 根据痛点，匹配最专业的 HR 服务术语，定义为 "expert_term"。
3. 必须输出纯净 JSON。
""")

# ==========================================
# 3. 辅助功能：存档日志 (New!)
# ==========================================
LOG_FILE = Path(__file__).parent / "processing_log.json"

def save_report(record):
    """把质检结果存入 JSON 文件，供前端读取"""
    if not LOG_FILE.exists():
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    with open(LOG_FILE, 'r+', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except:
            data = []
        
        # 加上时间戳和唯一ID
        record["id"] = f"etl_{int(time.time())}"
        record["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        data.append(record)
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 报告已存档至: {LOG_FILE.name}")

# ==========================================
# 4. 核心功能：模拟考
# ==========================================
def run_mock_exam(novice_intent, ground_truth_term):
    print(f"\n📝 [模拟考] 正在测试当前 Expert Agent 的能力...")
    
    dm = DomainManager("hr")
    taxonomy_context = dm.get_expert_context()
    
    chain = expert_prompt | llm
    response = chain.invoke({
        "domain": "hr",
        "taxonomy_context": taxonomy_context,
        "messages": [{"role": "user", "content": novice_intent}]
    })
    
    ai_answer_raw = response.content
    print(f"   🤖 Expert Agent 回答: {ai_answer_raw[:40]}...")
    
    judge_prompt = ChatPromptTemplate.from_template("""
    我是系统判卷员。请判断以下两个服务名称是否属于同一个服务范畴？
    标准答案: {ground_truth}
    AI回答: {ai_answer}
    
    如果意思相近且属于同一领域，输出 TRUE。如果不相关或 AI 明确拒绝，输出 FALSE。只输出单词。
    """)
    judge_chain = judge_prompt | llm
    verdict = judge_chain.invoke({
        "ground_truth": ground_truth_term,
        "ai_answer": ai_answer_raw
    }).content.strip()

    return verdict == "TRUE", ai_answer_raw

# ==========================================
# 5. 主流水线
# ==========================================
def process_file(file_path):
    print(f"\n📂 读取: {file_path.name}")
    with open(file_path, "r", encoding="utf-8") as f:
        raw_content = f.read()

    # Step 1: 提取
    print("⛏️  正在提取 Ground Truth...")
    chain = extract_prompt | llm
    try:
        data_str = chain.invoke({"raw_text": raw_content}).content.strip()
        if "```" in data_str:
            import re
            match = re.search(r"\{.*\}", data_str, re.DOTALL)
            if match: data_str = match.group(0)
            
        data = json.loads(data_str)
        novice_intent = data['novice_intent']
        expert_term = data['expert_term']
        print(f"   🎯 提取结果: {expert_term}")
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        return

    # Step 2: 质检
    is_pass, ai_answer = run_mock_exam(novice_intent, expert_term)

    status = "PASS" if is_pass else "REJECT"
    print("-" * 40)
    print(f"🏁 最终判定: {status}")
    print("-" * 40)

    # Step 3: 存档 (New!)
    report = {
        "file_source": file_path.name,
        "novice_intent": novice_intent,
        "ground_truth_term": expert_term,
        "current_ai_response": ai_answer,
        "status": status, # PASS 或 REJECT
        "action_required": not is_pass # 如果是 Reject，则需要人工处理
    }
    save_report(report)

if __name__ == "__main__":
    target_file = Path(__file__).parent / "raw_materials" / "demo_chat.txt"
    if target_file.exists():
        process_file(target_file)
    else:
        print(f"❌ 找不到文件: {target_file}")