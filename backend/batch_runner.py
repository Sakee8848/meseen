import time
import json
import os
import random
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

# 引入核心组件 (确保这些文件都存在)
from simulation_engine.domain_manager import DomainManager
from simulation_engine.graph import app as graph_app

# ==========================================
# ⚙️ 配置区
# ==========================================
BATCH_SIZE = 5            # 也就是一次生成 5 个案例，你可以改大
DOMAIN = "hr"             # 领域
DB_FILE = "knowledge_base.json" # 存到这里，前端就能看到了
# ==========================================

def save_to_db(record):
    """把跑出来的结果存进去"""
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    with open(DB_FILE, 'r+', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except:
            data = []
        
        data.append(record)
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)

def run_simulation(index):
    print(f"\n⚡️ [Case {index+1}/{BATCH_SIZE}] 正在启动仿真...")
    
    # 1. 随机生成秘密任务
    dm = DomainManager(DOMAIN)
    secret = dm.generate_secret_mission()
    expert_ctx = dm.get_expert_context()
    
    print(f"   🎯 目标意图: {secret['novice_intent']}")
    print(f"   💊 真实病症: {secret['expert_term']}")

    # 2. 初始化状态
    state = {
        "messages": [HumanMessage(content="你好，我想咨询一些业务问题。")],
        "domain": DOMAIN,
        "taxonomy_context": expert_ctx,
        "secret_mission": secret,
        "is_concluded": False,
        "turn_count": 0
    }

    # 3. 跑循环 (模拟 main.py 的逻辑)
    max_turns = 15
    while not state["is_concluded"] and state["turn_count"] < max_turns:
        # 调用 LangGraph 引擎
        result = graph_app.invoke(state)
        state = result
        
        # 补丁：防止 secret 丢失
        if "secret_mission" not in state:
             state["secret_mission"] = secret

        # 打印最后一句对话
        last_msg = state["messages"][-1].content
        sender = "🤖 Expert" if isinstance(state["messages"][-1], AIMessage) else "👤 User"
        print(f"   {sender}: {last_msg[:30]}...")

    # 4. 结束与保存
    if state["is_concluded"]:
        print(f"   ✅ 仿真结束，确诊为: {secret['expert_term']}")
        
        # 格式化对话历史
        history_path = []
        msgs = state["messages"][1:] # 去掉第一句
        for i in range(0, len(msgs) - 1, 2):
            if i+1 < len(msgs):
                history_path.append({
                    "step": (i // 2) + 1,
                    "expert_question": msgs[i].content,
                    "novice_response": msgs[i+1].content
                })

        record = {
            "id": f"batch_{int(time.time())}_{index}",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "domain": DOMAIN,
            "secret_intent": secret['novice_intent'],
            "expert_diagnosis": secret['expert_term'],
            "dialogue_path": history_path,
            "final_conclusion": state["messages"][-1].content
        }
        
        save_to_db(record)
        print("   💾 已自动归档到知识库")
    else:
        print("   ❌ 仿真超时或失败")

if __name__ == "__main__":
    print(f"🚀 开始批量运行 {BATCH_SIZE} 个仿真任务...")
    print("----------------------------------------")
    for i in range(BATCH_SIZE):
        try:
            run_simulation(i)
        except Exception as e:
            print(f"   ⚠️ 任务出错: {e}")
        time.sleep(1) # 休息一秒，防止触发 API 速率限制
    
    print("\n🎉 批量任务完成！请去前端刷新页面，查看你的【知识星图】。")