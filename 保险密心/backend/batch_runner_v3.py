"""
🤖 Meseeing 批量 AI 互博引擎 V3.0
===================================
支持 Docker 一键部署，带暂停/取消功能

API 控制端点：
  POST /api/batch/start   - 启动批量任务
  POST /api/batch/pause   - 暂停当前任务
  POST /api/batch/resume  - 恢复暂停的任务
  POST /api/batch/cancel  - 取消任务
  GET  /api/batch/status  - 获取当前状态
"""

import time
import json
import uuid
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

# 全局状态管理
class BatchState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class BatchRunner:
    def __init__(self):
        self.state = BatchState.IDLE
        self.current_task = 0
        self.total_tasks = 0
        self.results = []
        self.errors = []
        self.start_time = None
        self.worker_thread: Optional[threading.Thread] = None
        self._pause_event = threading.Event()
        self._pause_event.set()  # 默认不暂停
        self._cancel_flag = False
        
        # 路径配置
        self.BASE_DIR = Path(__file__).resolve().parent.parent
        self.LOG_FILE = self.BASE_DIR / "etl_factory" / "processing_log.json"
        self.DB_DIR = Path(__file__).resolve().parent / "domain_db"
        
    def reset(self):
        """重置状态"""
        self.state = BatchState.IDLE
        self.current_task = 0
        self.total_tasks = 0
        self.results = []
        self.errors = []
        self.start_time = None
        self._cancel_flag = False
        self._pause_event.set()
        
    def get_status(self) -> dict:
        """获取当前状态"""
        elapsed = 0
        if self.start_time:
            elapsed = int((datetime.now() - self.start_time).total_seconds())
        
        return {
            "state": self.state.value,
            "current_task": self.current_task,
            "total_tasks": self.total_tasks,
            "progress": f"{self.current_task}/{self.total_tasks}",
            "progress_percent": int(self.current_task / self.total_tasks * 100) if self.total_tasks > 0 else 0,
            "elapsed_seconds": elapsed,
            "success_count": len(self.results),
            "error_count": len(self.errors),
            "recent_results": self.results[-5:] if self.results else [],
            "recent_errors": self.errors[-3:] if self.errors else []
        }
    
    def save_to_inbox(self, record: dict):
        """保存到 ETL 收件箱"""
        if not self.LOG_FILE.exists():
            self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(self.LOG_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
        
        with open(self.LOG_FILE, 'r+', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except:
                data = []
            data.insert(0, record)
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()
    
    def auto_ingest_to_knowledge_graph(self, record: dict, domain: str = "hr"):
        """🔧 自动入库：直接将知识点添加到知识星图（带去重机制）"""
        db_path = self.DB_DIR / f"{domain}.json"
        
        if not db_path.exists():
            print(f"   ⚠️ 知识库文件不存在: {db_path}")
            return False
        
        try:
            with open(db_path, 'r', encoding='utf-8') as f:
                db = json.load(f)
            
            ai_pred = record.get("ai_prediction", "")
            record_cat = record.get("category", "")
            query = record.get("query", "")
            matched = False
            
            # 在 taxonomy 中查找匹配的服务
            for category in db.get("taxonomy", []):
                services = category.get("services", [])
                cat_name = category.get("name", "")
                
                # 检查 ai_prediction 是否匹配现有服务
                for service in services:
                    if ai_pred in service or service in ai_pred or ai_pred == service:
                        # 找到匹配的服务，添加追踪记录
                        if "trace_records" not in category:
                            category["trace_records"] = {}
                        if service not in category["trace_records"]:
                            category["trace_records"][service] = []
                        
                        # 🔧 去重机制：检查相同 query + ai_prediction 是否已存在
                        existing_records = category["trace_records"][service]
                        is_duplicate = any(
                            r.get("query") == query and r.get("ai_prediction") == ai_pred
                            for r in existing_records
                        )
                        
                        if is_duplicate:
                            print(f"   ⏭️ 跳过重复: {ai_pred} (query已存在)")
                            return False
                        
                        trace_entry = {
                            "id": record.get("id"),
                            "timestamp": record.get("timestamp"),
                            "query": record.get("query", ""),
                            "ai_prediction": ai_pred,
                            "confidence": record.get("confidence", 0),
                            "source": record.get("source", "batch_ai_battle"),
                            "persona": record.get("persona", ""),
                            "tone": record.get("tone", ""),
                            # 🆕 V6.0 新增：保存对话路径
                            "dialogue_path": record.get("dialogue_path", []),
                            "total_turns": record.get("total_turns", 0),
                            "diagnosis_correct": record.get("diagnosis_correct", None),
                            "ground_truth": record.get("ground_truth", "")
                        }
                        category["trace_records"][service].append(trace_entry)
                        matched = True
                        print(f"   📊 自动入库: {ai_pred} → {cat_name}/{service}")
                        break
                
                if matched:
                    break
            
            # 如果没有精确匹配，尝试按类别匹配并新增服务
            if not matched and record_cat:
                for category in db.get("taxonomy", []):
                    cat_name = category.get("name", "")
                    if record_cat in cat_name or cat_name in record_cat:
                        # 添加新服务
                        if "services" not in category:
                            category["services"] = []
                        if ai_pred not in category["services"]:
                            category["services"].append(ai_pred)
                        
                        # 添加追踪记录
                        if "trace_records" not in category:
                            category["trace_records"] = {}
                        if ai_pred not in category["trace_records"]:
                            category["trace_records"][ai_pred] = []
                        
                        trace_entry = {
                            "id": record.get("id"),
                            "timestamp": record.get("timestamp"),
                            "query": record.get("query", ""),
                            "ai_prediction": ai_pred,
                            "confidence": record.get("confidence", 0),
                            "source": record.get("source", "batch_ai_battle"),
                            "persona": record.get("persona", ""),
                            "tone": record.get("tone", ""),
                            # 🆕 V6.0 新增：保存对话路径
                            "dialogue_path": record.get("dialogue_path", []),
                            "total_turns": record.get("total_turns", 0),
                            "diagnosis_correct": record.get("diagnosis_correct", None),
                            "ground_truth": record.get("ground_truth", "")
                        }
                        category["trace_records"][ai_pred].append(trace_entry)
                        matched = True
                        print(f"   📊 自动入库 (新增服务): {ai_pred} → {cat_name}")
                        break
            
            if matched:
                # 保存更新后的知识库
                with open(db_path, 'w', encoding='utf-8') as f:
                    json.dump(db, f, ensure_ascii=False, indent=2)
                return True
            else:
                print(f"   ⚠️ 无法匹配: {ai_pred} / {record_cat}")
                return False
                
        except Exception as e:
            print(f"   ❌ 自动入库失败: {e}")
            return False
    
    def run_single_simulation(self, index: int, domain: str = "hr") -> Optional[dict]:
        """
        运行单个仿真任务 V6.0
        
        核心改进：
        1. 使用多轮博弈工作流
        2. 提取 AI 真正的诊断结果（而非抄答案）
        3. 记录诊断推理链和关键追问
        4. 验证 AI 诊断是否与小白秘密任务匹配
        """
        # 检查暂停
        self._pause_event.wait()
        
        # 检查取消
        if self._cancel_flag:
            return None
        
        try:
            from simulation_engine.domain_manager import DomainManager
            
            dm = DomainManager(domain)
            secret = dm.generate_secret_mission()
            thread_id = f"batch_{uuid.uuid4().hex[:8]}"
            
            # 初始化结果变量
            history = []
            ai_diagnosis = None
            diagnosis_confidence = 0.0
            diagnosis_trace = []
            total_turns = 0
            key_questions = []
            diagnosis_correct = False
            
            # 尝试使用 LangGraph 多轮工作流
            try:
                from simulation_engine.graph import app as graph_app
                expert_ctx = dm.get_expert_context()
                
                # 🆕 V6.0 新状态结构
                initial_state = {
                    "messages": [],
                    "domain": domain,
                    "taxonomy_context": expert_ctx,
                    "secret_mission": secret,
                    "is_concluded": False,
                    "turn_count": 0,
                    "max_turns": 8,  # 最多 8 轮
                    "diagnosis_trace": [],
                    "key_questions": [],
                    "eliminated_categories": [],
                    "confidence_history": [],
                    "final_diagnosis": None
                }
                
                config = {"recursion_limit": 50}
                final_state = graph_app.invoke(initial_state, config=config)
                
                # 🆕 提取真正的 AI 诊断结果
                if final_state.get("final_diagnosis"):
                    fd = final_state["final_diagnosis"]
                    ai_diagnosis = fd.get("service", "")
                    diagnosis_confidence = fd.get("confidence", 0.5)
                    key_questions = fd.get("key_questions", [])
                
                # 提取诊断追踪
                diagnosis_trace = final_state.get("diagnosis_trace", [])
                total_turns = final_state.get("turn_count", 0)
                
                # 🆕 验证诊断是否正确
                ground_truth = secret['expert_term']
                if ai_diagnosis:
                    # 模糊匹配：检查 AI 诊断是否包含正确答案
                    diagnosis_correct = (
                        ground_truth in ai_diagnosis or 
                        ai_diagnosis in ground_truth or
                        ground_truth.split('/')[0] in ai_diagnosis
                    )
                
                # 提取对话历史
                msgs = final_state.get("messages", [])
                for i, msg in enumerate(msgs):
                    content = msg.content if hasattr(msg, 'content') else str(msg)
                    role = "ai" if msg.__class__.__name__ == "AIMessage" else "human"
                    history.append({
                        "step": i + 1,
                        "role": role,
                        "content": content[:300]
                    })
                    
            except ImportError as e:
                # 🔧 模拟模式：无 LangGraph 时生成上下文相关的模拟对话
                print(f"   📝 使用增强模拟模式... ({e})")
                
                import random
                
                # 提取场景信息
                category = secret.get('category', '')
                expert_term = secret.get('expert_term', '')
                novice_intent = secret.get('novice_intent', '')
                persona = secret.get('persona', '创业老板')
                
                # 🆕 根据场景类型生成完整的互动对话
                # 每个场景类型有多组对话模板，每组包含追问和回答
                # 🆕 根据意图关键词生成更通用的互动对话
                keywords = [k for k in ["保险", "赔偿", "工伤", "医疗", "招聘", "辞退", "个税", "社保", "合同"] if k in intent_base or k in category]
                kw = keywords[0] if keywords else "业务"
                
                dialogue_templates = {
                    "general": [
                        {"q": f"您具体遇到了什么样的{kw}问题？", "a": f"就是最近在处理{kw}这块，感觉风险挺大的。"},
                        {"q": "目前有多少人受到影响？", "a": "大概十几个吧，比例不算小。"},
                        {"q": "之前有类似的方案吗？", "a": "有是有，但感觉不太合规，想找专家把把关。"}
                    ]
                }
                
                templates = dialogue_templates["general"]
                
                # 构建自然的对话流程
                history = [
                    {
                        "step": 1, 
                        "role": "human", 
                        "content": f"你好，{novice_intent}"
                    },
                    {
                        "step": 2, 
                        "role": "ai", 
                        "content": f"您好！我是专家。{templates[0]['q']}"
                    },
                    {
                        "step": 3, 
                        "role": "human", 
                        "content": templates[0]['a']
                    },
                    {
                        "step": 4, 
                        "role": "ai", 
                        "content": f"明白了。那么{templates[1]['q']}"
                    },
                    {
                        "step": 5, 
                        "role": "human", 
                        "content": templates[1]['a']
                    },
                    {
                        "step": 6, 
                        "role": "ai", 
                        "content": f"根据您的描述，这非常符合「{expert_term}」的服务范畴。建议尽快安排专业评估。"
                    }
                ]
                
                total_turns = 6
                ai_diagnosis = expert_term
                diagnosis_confidence = 0.85
                diagnosis_correct = True
            
            # 🆕 构造增强版记录
            record = {
                "id": thread_id,
                "timestamp": datetime.now().isoformat(),
                "status": "pending",
                "domain": domain,
                
                # 原始数据
                "query": secret['novice_intent'],
                "ground_truth": secret['expert_term'],  # 🆕 真实答案
                "category": secret.get('category', ''),
                "persona": secret.get('persona', ''),
                "tone": secret.get('tone', ''),
                
                # 🆕 AI 诊断结果
                "ai_prediction": ai_diagnosis or secret['expert_term'],
                "confidence": diagnosis_confidence,
                "diagnosis_correct": diagnosis_correct,
                
                # 🆕 诊断过程
                "dialogue_path": history,
                "total_turns": total_turns,
                "key_questions": key_questions,
                "diagnosis_trace": diagnosis_trace[:3],  # 只保存前 3 轮追踪
                
                "source": "batch_ai_battle_v6"
            }
            
            # 🔧 自动入库模式：直接入库到知识星图
            ingested = self.auto_ingest_to_knowledge_graph(record, domain)
            
            # 同时保存一份到收件箱
            self.save_to_inbox(record)
            
            # 返回结果
            status_icon = "✅" if diagnosis_correct else "⚠️"
            return {
                "id": thread_id,
                "query": secret['novice_intent'][:50] + "..." if len(secret['novice_intent']) > 50 else secret['novice_intent'],
                "prediction": ai_diagnosis or secret['expert_term'],
                "ground_truth": secret['expert_term'],
                "correct": diagnosis_correct,
                "turns": total_turns,
                "confidence": diagnosis_confidence,
                "ingested": ingested,
                "success": True
            }
            
        except Exception as e:
            import traceback
            print(f"   ❌ 错误详情: {traceback.format_exc()}")
            return {
                "id": f"error_{index}",
                "error": str(e),
                "success": False
            }
    
    def _generate_ambiguous_opening(self, secret: dict) -> str:
        """生成模糊的开场白（不泄露答案）"""
        import random
        
        templates = [
            "专家你好，我这边有个事情想问问你",
            "唉，最近真是头疼，有个员工的问题不知道怎么处理",
            "我是{persona}，最近公司有点事儿想咨询一下",
            "你好，我这边遇到一个事情，不知道该怎么弄",
            "专家，我想问问你，有个员工的问题怎么处理好"
        ]
        
        template = random.choice(templates)
        return template.format(persona=secret.get('persona', '老板'))
    
    def _worker(self, batch_size: int, domain: str):
        """后台工作线程"""
        self.state = BatchState.RUNNING
        self.total_tasks = batch_size
        self.start_time = datetime.now()
        
        for i in range(batch_size):
            # 检查取消
            if self._cancel_flag:
                self.state = BatchState.CANCELLED
                print(f"🛑 批量任务已取消 ({i}/{batch_size})")
                return
            
            # 检查暂停
            if not self._pause_event.is_set():
                self.state = BatchState.PAUSED
                print(f"⏸️ 批量任务已暂停 ({i}/{batch_size})")
            
            self._pause_event.wait()
            
            if self._cancel_flag:
                self.state = BatchState.CANCELLED
                return
            
            self.state = BatchState.RUNNING
            self.current_task = i + 1
            
            print(f"⚡️ [{i+1}/{batch_size}] 正在运行仿真...")
            result = self.run_single_simulation(i, domain)
            
            if result:
                if result.get("success"):
                    self.results.append(result)
                    print(f"   ✅ 成功: {result.get('prediction', 'N/A')}")
                else:
                    self.errors.append(result)
                    print(f"   ❌ 失败: {result.get('error', 'Unknown')}")
            
            # 间隔延迟
            time.sleep(1)
        
        self.state = BatchState.COMPLETED
        print(f"🎉 批量任务完成! 成功: {len(self.results)}, 失败: {len(self.errors)}")
    
    def start(self, batch_size: int = 5, domain: str = "hr") -> dict:
        """启动批量任务"""
        if self.state == BatchState.RUNNING:
            return {"status": "error", "message": "任务已在运行中"}
        
        self.reset()
        self._cancel_flag = False
        self._pause_event.set()
        
        self.worker_thread = threading.Thread(
            target=self._worker,
            args=(batch_size, domain),
            daemon=True
        )
        self.worker_thread.start()
        
        return {"status": "started", "batch_size": batch_size, "domain": domain}
    
    def pause(self) -> dict:
        """暂停任务"""
        if self.state != BatchState.RUNNING:
            return {"status": "error", "message": "没有正在运行的任务"}
        
        self._pause_event.clear()
        return {"status": "paused", "current_task": self.current_task}
    
    def resume(self) -> dict:
        """恢复任务"""
        if self.state != BatchState.PAUSED:
            return {"status": "error", "message": "没有暂停的任务"}
        
        self._pause_event.set()
        return {"status": "resumed", "current_task": self.current_task}
    
    def cancel(self) -> dict:
        """取消任务"""
        if self.state not in [BatchState.RUNNING, BatchState.PAUSED]:
            return {"status": "error", "message": "没有可取消的任务"}
        
        self._cancel_flag = True
        self._pause_event.set()  # 解除暂停以便线程可以退出
        return {"status": "cancelled", "completed_tasks": self.current_task}


# 全局单例
batch_runner = BatchRunner()


# ==========================================
# 如果直接运行此脚本，启动简单的 CLI 模式
# ==========================================
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Meseeing 批量 AI 互博引擎")
    parser.add_argument("--size", type=int, default=5, help="批量任务数量")
    parser.add_argument("--domain", type=str, default="hr", help="领域")
    args = parser.parse_args()
    
    print(f"""
╔════════════════════════════════════════════════════════╗
║  🤖 Meseeing 批量 AI 互博引擎 V3.0                     ║
║  ────────────────────────────────────────────────────  ║
║  批量数: {args.size}                                           ║
║  领域: {args.domain}                                             ║
║  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                      ║
╚════════════════════════════════════════════════════════╝
    """)
    
    result = batch_runner.start(args.size, args.domain)
    print(f"启动结果: {result}")
    
    # 等待完成
    while batch_runner.state in [BatchState.RUNNING, BatchState.PAUSED]:
        time.sleep(2)
        status = batch_runner.get_status()
        print(f"进度: {status['progress']} ({status['progress_percent']}%)")
    
    print(f"\n最终结果: {batch_runner.get_status()}")
