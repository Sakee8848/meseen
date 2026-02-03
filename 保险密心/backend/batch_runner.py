"""
🤖 保险密心 - 批量 AI 互博运行器
=================================
自动化批量生成保险诊断对话样本
"""

import json
import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

# 路径锚定
ROOT_DIR = Path(__file__).resolve().parent
ETL_DIR = ROOT_DIR.parent / "etl_factory"
INBOX_PATH = ETL_DIR / "processing_log.json"


class InsuranceBatchRunner:
    """保险领域批量仿真运行器"""
    
    _instance = None
    _running = False
    _paused = False
    _cancelled = False
    _progress = {"completed": 0, "total": 0, "current": None}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def start(self, count: int = 10):
        """启动批量任务"""
        if self._running:
            return {"status": "already_running"}
        
        self._running = True
        self._cancelled = False
        self._paused = False
        self._progress = {"completed": 0, "total": count, "current": None}
        
        # 在后台线程运行
        executor = ThreadPoolExecutor(max_workers=1)
        executor.submit(self._run_batch, count)
        
        return {"status": "started", "total": count}
    
    def _run_batch(self, count: int):
        """执行批量仿真"""
        try:
            import os
            from dotenv import load_dotenv
            from simulation_engine.domain_manager import DomainManager
            from simulation_engine.prompts import expert_prompt, novice_prompt, opening_prompt
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import HumanMessage
            
            load_dotenv()
            
            dm = DomainManager("insurance")
            dm.reset_used_scenarios()
            
            # 智谱 API 配置
            api_key = os.getenv("OPENAI_API_KEY")
            api_base = os.getenv("OPENAI_API_BASE", "https://open.bigmodel.cn/api/paas/v4/")
            llm = ChatOpenAI(
                model="glm-4",
                temperature=0.7,
                max_tokens=2000,
                openai_api_key=api_key,
                openai_api_base=api_base
            )
            
            for i in range(count):
                if self._cancelled:
                    break
                
                while self._paused:
                    import time
                    time.sleep(0.5)
                
                # 生成任务
                mission = dm.generate_secret_mission()
                self._progress["current"] = {
                    "index": i + 1,
                    "category": mission.get("category_short", mission["category"]),
                    "persona": mission.get("persona", "企业管理者")
                }
                
                # 执行仿真
                result = self._run_single_simulation(llm, dm, mission)
                
                if result:
                    self._save_result(result, mission)
                
                self._progress["completed"] = i + 1
                
        except Exception as e:
            print(f"❌ 批量运行错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self._running = False
            self._progress["current"] = None
    
    def _run_single_simulation(self, llm, dm, mission) -> Optional[dict]:
        """运行单次仿真"""
        try:
            from simulation_engine.prompts import expert_prompt, novice_prompt, opening_prompt
            from langchain_core.messages import HumanMessage
            
            messages = []
            taxonomy_context = dm.get_expert_context()
            
            # 生成开场白
            prompt = opening_prompt.format(
                secret_user_intent=mission["novice_intent"],
                secret_category=mission["category"],
                persona_role=mission.get("persona", "企业管理者"),
                persona_tone=mission.get("tone", "迷茫")
            )
            
            response = llm.invoke([HumanMessage(content=prompt)])
            opening = response.content.strip()
            
            messages.append({
                "step": 1,
                "role": "human",
                "content": f"我是{mission.get('persona', '企业管理者')}，{opening}"
            })
            
            # 多轮对话 (最多6轮)
            final_result = None
            for turn in range(6):
                # 顾问响应
                messages_text = "\n".join([
                    f"{'客户' if m['role'] == 'human' else '顾问'}: {m['content']}"
                    for m in messages
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
                        "reply_to_user": "请详细说说企业情况"
                    }
                
                messages.append({
                    "step": len(messages) + 1,
                    "role": "ai",
                    "content": expert_data.get("reply_to_user", "请详细说说")
                })
                
                status = expert_data.get("analysis_data", {}).get("status", "active")
                confidence = expert_data.get("diagnosis_reasoning", {}).get("confidence", 0)
                
                if status == "concluded" or turn >= 5:
                    final_result = {
                        "ai_prediction": expert_data.get("analysis_data", {}).get("matched_service", "未诊断"),
                        "confidence": confidence,
                        "total_turns": len(messages)
                    }
                    break
                
                # 客户响应
                messages_text = "\n".join([
                    f"{'客户' if m['role'] == 'human' else '顾问'}: {m['content']}"
                    for m in messages
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
                
                messages.append({
                    "step": len(messages) + 1,
                    "role": "human",
                    "content": novice_data.get("response", "是的")
                })
            
            return {
                "messages": messages,
                "final_result": final_result or {"ai_prediction": "未完成", "confidence": 0, "total_turns": len(messages)}
            }
            
        except Exception as e:
            print(f"❌ 单次仿真失败: {e}")
            return None
    
    def _save_result(self, result: dict, mission: dict):
        """保存结果到 ETL 收件箱"""
        try:
            ETL_DIR.mkdir(parents=True, exist_ok=True)
            
            inbox = []
            if INBOX_PATH.exists():
                with open(INBOX_PATH, "r", encoding="utf-8") as f:
                    inbox = json.load(f)
            
            final = result.get("final_result", {})
            prediction = final.get("ai_prediction", "未诊断")
            ground_truth = mission["expert_term"]
            
            # 增强健壮性：确保是字符串进行比较
            pred_val = str(prediction) if not isinstance(prediction, list) else ", ".join([str(x) for x in prediction])
            gt_val = str(ground_truth)
            
            record = {
                "id": f"batch_ins_{uuid.uuid4().hex[:8]}",
                "timestamp": datetime.now().isoformat(),
                "domain": "insurance",
                "query": result["messages"][0]["content"] if result["messages"] else "",
                "ai_prediction": prediction,
                "ground_truth": ground_truth,
                "category": mission["category"],
                "confidence": final.get("confidence", 0),
                "persona": mission.get("persona", "企业管理者"),
                "industry": mission.get("industry", "未知"),
                "company_size": mission.get("company_size", "未知"),
                "tone": mission.get("tone", "迷茫"),
                "dialogue_path": result["messages"],
                "total_turns": final.get("total_turns", len(result["messages"])),
                "diagnosis_correct": pred_val in gt_val or gt_val in pred_val,
                "source": "batch_insurance_v1",
                "status": "pending"
            }
            
            inbox.append(record)
            
            with open(INBOX_PATH, "w", encoding="utf-8") as f:
                json.dump(inbox, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 批量记录保存: {record['id']} | {mission.get('category_short', '')}")
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
    
    def pause(self):
        """暂停批量任务"""
        self._paused = True
        return {"status": "paused"}
    
    def resume(self):
        """恢复批量任务"""
        self._paused = False
        return {"status": "resumed"}
    
    def cancel(self):
        """取消批量任务"""
        self._cancelled = True
        return {"status": "cancelled"}
    
    def get_status(self) -> dict:
        """获取当前状态 - 返回前端期望的格式"""
        # 确定状态字符串
        if self._cancelled:
            state = "cancelled"
        elif self._paused:
            state = "paused"
        elif self._running:
            state = "running"
        else:
            state = "idle"
        
        completed = self._progress.get("completed", 0)
        total = self._progress.get("total", 0)
        
        return {
            "state": state,
            "current_task": completed,
            "total_tasks": total,
            "progress": f"{completed}/{total}",
            "progress_percent": int((completed / total * 100)) if total > 0 else 0,
            "elapsed_seconds": 0,
            "success_count": completed,
            "error_count": 0,
            "recent_results": [],
            "recent_errors": [],
            # 保留旧字段兼容
            "running": self._running,
            "paused": self._paused,
            "cancelled": self._cancelled
        }


# 命令行入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="保险密心批量挖掘")
    parser.add_argument("--count", type=int, default=10, help="生成数量")
    args = parser.parse_args()
    
    runner = InsuranceBatchRunner()
    print(f"🚀 启动批量保险诊断挖掘，目标: {args.count} 条")
    runner._run_batch(args.count)
    print("✅ 批量任务完成")
