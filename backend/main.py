import os
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 引入内部模块
from simulation_engine.domain_manager import DomainManager
from simulation_engine.graph import app as graph_app 

# 加载环境变量
load_dotenv()

# ==========================================
# 1. 核心对象初始化 (强制启动模式)
# ==========================================
print("-" * 50)
print("🚀 系统正在启动...")

# 尝试初始化大脑
domain_mgr = None
try:
    # 强制在启动时直接加载，不再等待
    domain_mgr = DomainManager("hr")
    
    # 打印一下看看到底加载了啥
    taxonomy_count = len(domain_mgr.domain_db.get("taxonomy", []))
    print(f"✅ 大脑加载成功！")
    print(f"📊 当前包含服务大类: {taxonomy_count} 个")
    
except Exception as e:
    print(f"❌ 大脑加载失败: {e}")
    print("⚠️ 系统将以空脑模式运行，请检查 backend/domain_db/hr.json 是否存在")

print("-" * 50)

app = FastAPI()

# ==========================================
# 2. CORS 安全配置 (确保 3000 和 3001 都能用)
# ==========================================
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 3. 接口定义
# ==========================================

# --- A. 聊天接口 ---
class ChatRequest(BaseModel):
    message: str
    domain: str = "hr"

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not domain_mgr:
        # 如果大脑没加载，尝试临场救急
        return {"response": "系统初始化异常，请检查后端日志。"}
    
    inputs = {
        "messages": [("user", request.message)],
        "domain": request.domain,
        "taxonomy_context": domain_mgr.get_expert_context(),
        "secret_mission": {"category": "unknown", "expert_term": "unknown", "novice_intent": "unknown"},
        "is_concluded": False,
        "turn_count": 0
    }
    config = {"configurable": {"thread_id": "1"}}
    
    result = graph_app.invoke(inputs, config=config)
    last_message = result["messages"][-1]
    return {"response": last_message.content}

# --- B. 知识库日志接口 ---
@app.get("/api/knowledge/logs")
async def get_knowledge_logs():
    # 这是一个独立的接口，读取 JSON 文件
    log_path = Path(__file__).resolve().parent.parent / "etl_factory" / "processing_log.json"
    
    if not log_path.exists():
        return []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data[::-1] 
    except Exception as e:
        return [{"error": str(e)}]

# --- C. 大脑编辑接口 (修复下拉菜单和星图) ---
class TaxonomyUpdate(BaseModel):
    category: str
    service: str

@app.get("/api/taxonomy")
async def get_taxonomy():
    """这是星图和下拉菜单的数据源"""
    if not domain_mgr:
        # 返回空结构防止前端报错
        return {"taxonomy": []}
    return domain_mgr.domain_db

@app.post("/api/taxonomy/add")
async def add_service(update: TaxonomyUpdate):
    """注入新知识"""
    if not domain_mgr:
        raise HTTPException(status_code=500, detail="Domain Manager missing")
    
    try:
        current_db = domain_mgr.domain_db
        
        # 1. 查找大类
        target_category = None
        for cat in current_db["taxonomy"]:
            if cat["name"] == update.category:
                target_category = cat
                break
        
        # 2. 如果是新大类，创建它
        if not target_category:
            target_category = {
                "name": update.category,
                "description": f"关于{update.category}的专业服务",
                "services": []
            }
            current_db["taxonomy"].append(target_category)
        
        # 3. 注入服务
        if update.service not in target_category["services"]:
            target_category["services"].append(update.service)
            
            # 4. 写入文件
            db_path = Path(__file__).parent / "domain_db" / "hr.json"
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(current_db, f, ensure_ascii=False, indent=2)
            
            # 5. 刷新内存
            domain_mgr.load_domain_data()
            return {"status": "success", "message": f"已添加: {update.service}"}
        else:
            return {"status": "skipped", "message": "该服务已存在"}
            
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

    # ... (保留上面的代码)

# ==========================================
# 🆕 新增：大类管理接口 (改名 & 删除)
# ==========================================

class CategoryRename(BaseModel):
    old_name: str
    new_name: str

class CategoryDelete(BaseModel):
    category_name: str

@app.put("/api/taxonomy/category")
async def rename_category(update: CategoryRename):
    """修改大类名称"""
    if not domain_mgr:
        raise HTTPException(status_code=500, detail="Domain Manager missing")
    
    current_db = domain_mgr.domain_db
    target_cat = next((c for c in current_db["taxonomy"] if c["name"] == update.old_name), None)
    
    if target_cat:
        # 检查新名字是否冲突
        if any(c["name"] == update.new_name for c in current_db["taxonomy"]):
            return {"status": "error", "message": "新名称已存在"}
            
        target_cat["name"] = update.new_name
        
        # 保存并刷新
        db_path = Path(__file__).parent / "domain_db" / "hr.json"
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(current_db, f, ensure_ascii=False, indent=2)
        domain_mgr.load_domain_data()
        
        return {"status": "success", "message": f"已重命名为: {update.new_name}"}
    
    return {"status": "error", "message": "未找到该分类"}

@app.delete("/api/taxonomy/category")
async def delete_category(delete_req: CategoryDelete):
    """删除大类 (危险操作：会连带删除下面的服务)"""
    if not domain_mgr:
        raise HTTPException(status_code=500, detail="Domain Manager missing")
        
    current_db = domain_mgr.domain_db
    # 过滤掉要删除的那个
    initial_len = len(current_db["taxonomy"])
    current_db["taxonomy"] = [c for c in current_db["taxonomy"] if c["name"] != delete_req.category_name]
    
    if len(current_db["taxonomy"]) < initial_len:
        # 保存并刷新
        db_path = Path(__file__).parent / "domain_db" / "hr.json"
        with open(db_path, "w", encoding="utf-8") as f:
            json.dump(current_db, f, ensure_ascii=False, indent=2)
        domain_mgr.load_domain_data()
        return {"status": "success", "message": f"已删除: {delete_req.category_name}"}
        
    return {"status": "error", "message": "未找到该分类"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)