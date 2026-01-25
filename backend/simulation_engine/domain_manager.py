import json
import random
import os

class DomainManager:
    def __init__(self, domain_name="hr"):
        # 自动定位到 backend/domain_db 目录
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(base_dir, "domain_db", f"{domain_name}.json")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Domain file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            
        self.domain_name = self.data['domain']
        self.categories = self.data['categories']

    def get_expert_context(self):
        """生成给专家看的'地图'（只有大类和名词，没有具体症状）"""
        context = []
        for cat in self.categories:
            services = [svc['expert_term'] for svc in cat['services']]
            context.append(f"- 【{cat['name']}】: {', '.join(services)}")
        return "\n".join(context)

    def generate_secret_mission(self):
        """随机抽取一个小白的秘密任务"""
        all_services = []
        for cat in self.categories:
            for svc in cat['services']:
                svc['category_name'] = cat['name']
                all_services.append(svc)
        
        if not all_services:
            raise ValueError("没有找到任何服务项，请检查 json 文件内容")
            
        return random.choice(all_services)