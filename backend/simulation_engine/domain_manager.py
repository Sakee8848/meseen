import json
import os
from pathlib import Path

class DomainManager:
    def __init__(self, domain: str = "hr"):
        self.domain = domain
        # 1. 自动定位到 backend/domain_db/hr.json
        # 这里的路径是相对于当前文件的：父级(simulation_engine) -> 父级(backend) -> domain_db
        self.db_path = Path(__file__).resolve().parent.parent / "domain_db" / f"{domain}.json"
        
        # 2. 关键修复：初始化 self.domain_db 属性
        self.domain_db = {"taxonomy": []} 
        
        # 3. 立即加载数据
        self.load_domain_data()

    def load_domain_data(self):
        """从 JSON 文件加载知识库"""
        if not self.db_path.exists():
            print(f"⚠️ 警告: 找不到知识库文件 {self.db_path}")
            # 如果文件不存在，初始化一个空的结构，防止报错
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
        """将 JSON 数据转化为 AI 可读的 Prompt 文本"""
        context_lines = []
        taxonomy = self.domain_db.get("taxonomy", [])
        
        for category in taxonomy:
            cat_name = category.get("name", "未命名大类")
            services = category.get("services", [])
            services_str = ", ".join(services)
            context_lines.append(f"【{cat_name}】: {services_str}")
            
        return "\n".join(context_lines)

# 测试代码
if __name__ == "__main__":
    dm = DomainManager("hr")
    print(dm.get_expert_context())