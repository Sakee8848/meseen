import json
from pathlib import Path

# 1. 定位文件 (自动寻找 backend/domain_db/hr.json)
# 这里的路径假设脚本在根目录运行
db_path = Path("backend/domain_db/hr.json")

if not db_path.exists():
    print(f"❌ 找不到文件: {db_path.absolute()}")
else:
    print(f"🧹 正在清洗: {db_path} ...")
    with open(db_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. 去重逻辑
    cleaned_taxonomy = []
    seen = set()
    
    for cat in data.get("taxonomy", []):
        if cat["name"] not in seen:
            # 服务内部也去重
            cat["services"] = list(set(cat["services"])) 
            cleaned_taxonomy.append(cat)
            seen.add(cat["name"])
    
    data["taxonomy"] = cleaned_taxonomy

    # 3. 写回
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 清洗完成！剩余 {len(cleaned_taxonomy)} 个大类。")