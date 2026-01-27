import json
import os
from pathlib import Path

class DomainManager:
    def __init__(self, domain: str = "hr"):
        self.domain = domain
        # 1. 自动定位到 backend/domain_db/hr.json
        self.db_path = Path(__file__).resolve().parent.parent / "domain_db" / f"{domain}.json"
        
        # 2. 初始化
        self.domain_db = {"taxonomy": []} 
        
        # 3. 立即加载数据
        self.load_domain_data()

    def load_domain_data(self):
        """从 JSON 文件加载知识库"""
        if not self.db_path.exists():
            print(f"⚠️ 警告: 找不到知识库文件 {self.db_path}")
            self.domain_db = {"taxonomy": []}
            return

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                self.domain_db = json.load(f)
            print(f"📚 DomainManager: 已加载 {self.domain} 知识库")
        except Exception as e:
            print(f"❌ 错误: 知识库文件损坏 - {e}")
            self.domain_db = {"taxonomy": []}

    def get_expert_context(self):
        """将 JSON 数据转化为 AI 可读的结构化文本"""
        context_lines = []
        taxonomy = self.domain_db.get("taxonomy", [])
        
        context_lines.append(f"=== {self.domain.upper()} 专业服务体系 ===")
        for category in taxonomy:
            cat_name = category.get("name", "通用服务")
            services = category.get("services", [])
            # 使用更清晰的列表格式，帮助 AI 理解层级
            services_str = " | ".join(services)
            context_lines.append(f"📌 [大类: {cat_name}]")
            context_lines.append(f"   └─ 包含服务: {services_str}")
            
        return "\n".join(context_lines)

# 测试代码
if __name__ == "__main__":
    dm = DomainManager("hr")
    print(dm.get_expert_context())