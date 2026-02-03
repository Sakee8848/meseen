import json
import os
from pathlib import Path

# 路径锚定
ROOT_DIR = Path("/Users/tonyyu/Documents/密心/保险密心/backend")
ETL_DIR = ROOT_DIR.parent / "etl_factory"
INBOX_PATH = ETL_DIR / "processing_log.json"
DB_PATH = ROOT_DIR / "domain_db" / "insurance.json"

# 分类映射表 (将旧标签映射到新标签)
CATEGORY_MAP = {
    "【个险/寿险】家庭保障体系": "【财险/意外】风险规避", # 暂时映射到风险规避，或根据需要调整
    "【团险/福利】企业员工保障": "团体员工保险 (Group Employee Insurance)"
}

def batch_ingest():
    if not INBOX_PATH.exists():
        print("❌ Inbox file not found.")
        return

    with open(INBOX_PATH, "r", encoding="utf-8") as f:
        inbox = json.load(f)

    if not DB_PATH.exists():
        print("❌ Database file not found.")
        return

    with open(DB_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    ingested_count = 0
    remaining_inbox = []

    for record in inbox:
        if record.get("domain") != "insurance":
            remaining_inbox.append(record)
            continue

        category_name = record.get("category", "")
        # 如果在映射表中，则转换
        if category_name in CATEGORY_MAP:
            category_name = CATEGORY_MAP[category_name]
            
        service_name = record.get("ground_truth", "")
        
        # 提取核心名称进行匹配 (去掉括号后的内容)
        core_cat = category_name.split(" (")[0].replace("【", "").replace("】", "").strip()
        core_svc = service_name.split(" (")[0].strip()

        matched = False
        for cat in db.get("taxonomy", []):
            db_cat_core = cat["name"].split(" (")[0].replace("【", "").replace("】", "").strip()
            
            # 使用更宽松的包含关系匹配
            if core_cat in db_cat_core or db_cat_core in core_cat:
                if "trace_records" not in cat:
                    cat["trace_records"] = {}
                
                # 寻找服务节点
                service_key = None
                for svc in cat["services"]:
                    svc_core = svc.split(" (")[0].strip()
                    if core_svc == svc_core or core_svc in svc or svc in core_svc:
                        service_key = svc
                        break
                
                if not service_key:
                    # 如果分类匹配但服务不匹配，动态添加服务节点
                    cat["services"].append(service_name)
                    service_key = service_name
                
                # 提取服务的简短键名用于 trace_records
                trace_key = service_key.split(" (")[0]
                if trace_key not in cat["trace_records"]:
                    cat["trace_records"][trace_key] = []
                
                trace = {
                    "id": record["id"],
                    "timestamp": record["timestamp"],
                    "query": record["query"],
                    "ai_prediction": record["ai_prediction"],
                    "confidence": record.get("confidence", 0.5),
                    "source": record.get("source", "batch_fix"),
                    "persona": record.get("persona", ""),
                    "industry": record.get("industry", ""),
                    "tone": record.get("tone", ""),
                    "dialogue_path": record.get("dialogue_path", []),
                    "total_turns": record.get("total_turns", 0),
                    "diagnosis_correct": record.get("diagnosis_correct", False),
                    "ground_truth": service_name
                }
                
                cat["trace_records"][trace_key].append(trace)
                ingested_count += 1
                matched = True
                break
        
        if not matched:
            # 如果依然没匹配到，保留并打印
            print(f"⚠️ No match for: Category='{category_name}', Service='{service_name}'")
            remaining_inbox.append(record)

    # 保存更新后的知识库
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

    # 更新收件箱
    with open(INBOX_PATH, "w", encoding="utf-8") as f:
        json.dump(remaining_inbox, f, ensure_ascii=False, indent=4)

    print(f"✅ Successfully ingested {ingested_count} records into the Insurance Knowledge Galaxy.")
    print(f"📦 {len(remaining_inbox)} records remaining in inbox.")

if __name__ == "__main__":
    batch_ingest()
