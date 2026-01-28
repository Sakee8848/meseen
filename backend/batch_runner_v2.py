import time
import json
import os
import uuid
import ast
from datetime import datetime
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage
from simulation_engine.domain_manager import DomainManager
from simulation_engine.graph import app as graph_app

# ==========================================
# ⚙️ 配置区 (已对齐 V5.1 架构)
# ==========================================
BATCH_SIZE = 5            
DOMAIN = "hr"             
# 指向收件箱路径
BASE_DIR = Path(__file__).resolve().parent.parent
LOG_FILE = BASE_DIR / "etl_factory" / "processing_log.json"

def clean_content(content):
    """复刻 main.py 的美颜滤镜，确保 JSON 纯净"""
    str_content = str(content)
    if "{" in str_content and "}" in str_content:
        try:
            # 处理 Python 风格的 Dict 字符串
            fixed = str_content.replace("'", '"').replace("None", "null").replace("False", "false").replace("True", "true")
            return json.loads(fixed)
        except:
            try:
                return ast.literal_eval(str_content)
            except:
                return str_content
    return str_content

def save_to_inbox(record):
    """存入待处理池 (Processing Log)"""
    if not LOG_FILE.exists():
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    with open(LOG_FILE, 'r+', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except:
            data = []
        data.insert(0, record) # 新挖掘的放在最前面
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.truncate()

def run_simulation(index):
    print(f"\n⚡️ [Task {index+1}/{BATCH_SIZE}] 启动挖掘任务...")
    
    dm = DomainManager(DOMAIN)
    # 这里建议在 DomainManager 里增加一个随机生成不同意图的方法
    # 目前先沿用你的逻辑，或手动指定不同的测试用例
    secret = {
        "novice_intent": "我想把不听话的员工开除，但怕赔钱",
        "expert_term": "裁员/辞退合规咨询",
        "category": "劳动关系与合规"
    }
    
    thread_id = f"batch_sim_{uuid.uuid4().hex[:8]}"
    
    state = {
        "messages": [("user", "你好，专家。我这边团队管理上遇到个棘手的事...")],
        "domain": DOMAIN,
        "taxonomy_context": dm.get_expert_context(),
        "secret_mission": secret,
        "is_concluded": False,
        "turn_count": 0
    }

    # 运行流式或同步 invoke
    # 关键：设置 recursion_limit 防止中断
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 100}
    
    try:
        # 使用 invoke 获取最终状态
        final_state = graph_app.invoke(state, config=config)
        
        # 提取对话路径
        history = []
        msgs = final_state["messages"]
        for i in range(1, len(msgs)-1, 2): # 跳过第一句，成对提取
            history.append({
                "step": (i // 2) + 1,
                "expert_question": msgs[i].content if hasattr(msgs[i], 'content') else str(msgs[i]),
                "novice_response": msgs[i+1].content if hasattr(msgs[i+1], 'content') else str(msgs[i+1])
            })

        # 构造符合 V5.1 前端要求的记录
        record = {
            "id": thread_id,
            "timestamp": datetime.now().isoformat(),
            "query": secret['novice_intent'],
            "ai_prediction": secret['expert_term'],
            "category": secret['category'],
            "confidence": 0.85, # 批量生成的初始置信度
            "dialogue_path": history,
            "status": "pending" # 标记为待审核
        }
        
        save_to_inbox(record)
        print(f"   ✅ 挖掘成功: {secret['expert_term']} (ID: {thread_id})")
        
    except Exception as e:
        print(f"   ❌ 运行出错: {e}")

if __name__ == "__main__":
    print(f"🚀 Meseeing 批量挖矿引擎 V2.0 启动...")
    print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📦 目标池: {LOG_FILE}")
    print("-" * 50)
    
    for i in range(BATCH_SIZE):
        run_simulation(i)
        time.sleep(2) # 适当延迟
    
    print("\n🎉 挖掘任务完成！请前往前端【收件箱】进行审核入库。")