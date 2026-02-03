"""
🎭 DomainManager - 专家知识领域管理器
=====================================
核心职责：
1. 加载领域知识库（taxonomy）
2. 生成多样化的小白场景（secret mission）
3. 提供结构化的专家上下文

场景多样性保证策略：
- 多维度场景模板库（角色 × 情境 × 情绪 × 紧急程度）
- 动态变量填充（人名、数字、细节）
- 已使用场景追踪（防止重复）
- 分类均衡覆盖
"""

import json
import random
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class DomainManager:
    # 已使用场景的哈希集合（全局去重）
    _used_scenarios: set = set()
    
    def __init__(self, domain: str = "hr"):
        self.domain = domain
        self.db_path = Path(__file__).resolve().parent.parent / "domain_db" / f"{domain}.json"
        self.domain_db = {"taxonomy": []} 
        self.load_domain_data()
        
        # 加载场景模板库
        self._init_scenario_templates()

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

    def _init_scenario_templates(self):
        """初始化多样化场景模板库"""
        
        # ==========================================
        # 🎭 角色设定（WHO）
        # ==========================================
        self.personas = [
            {"role": "创业老板", "tone": "急躁", "prefix": "我是个小老板，"},
            {"role": "HR经理", "tone": "专业", "prefix": "作为公司HR，"},
            {"role": "普通员工", "tone": "迷茫", "prefix": "我是一名普通员工，"},
            {"role": "部门主管", "tone": "焦虑", "prefix": "我是部门主管，"},
            {"role": "应届毕业生", "tone": "紧张", "prefix": "我刚毕业入职，"},
            {"role": "资深员工", "tone": "愤怒", "prefix": "在公司干了十几年，"},
            {"role": "外企高管", "tone": "谨慎", "prefix": "我在外资公司担任高管，"},
            {"role": "初创团队负责人", "tone": "迷茫", "prefix": "我们是个初创团队，"},
        ]
        
        # ==========================================
        # 🎯 HR 领域场景模板库（按服务分类）
        # 每个场景包含：
        # - intent: 小白的模糊表达（不包含专业术语）
        # - term: 对应的专业服务术语（真实答案）
        # - vars: 可变参数
        # - ambiguity: 模糊程度 (1-5)，越高越难诊断
        # - confusion_with: 容易混淆的其他分类
        # ==========================================
        self.hr_scenarios = {
            # 招聘与人才获取
            "招聘与人才获取": [
                {"intent": "最近忙不过来，想找几个人帮忙干活", "term": "灵活用工/兼职招聘", "vars": [], "ambiguity": 3, "confusion_with": ["RPO招聘流程外包"]},
                {"intent": "年底太忙了，能不能临时找点人", "term": "灵活用工/兼职招聘", "vars": [], "ambiguity": 2},
                {"intent": "公司空调坏了{days}天了，员工都要热死了", "term": "设施设备紧急维修", "vars": {"days": [3, 5, 7, 10]}, "ambiguity": 1},
                {"intent": "招人太累了，有没有人能帮我搞定", "term": "RPO招聘流程外包", "vars": [], "ambiguity": 3, "confusion_with": ["灵活用工/兼职招聘"]},
                {"intent": "想找个厉害的人，但怎么都找不到", "term": "高端猎头服务", "vars": [], "ambiguity": 4, "confusion_with": ["RPO招聘流程外包"]},
                {"intent": "有个人想来我们公司，但他的简历看起来太好了", "term": "背景调查", "vars": [], "ambiguity": 2},
                {"intent": "校招季人太多了，我一个人搞不定", "term": "RPO招聘流程外包", "vars": [], "ambiguity": 3},
                {"intent": "竞争对手那边有人想跳过来，不知道靠不靠谱", "term": "背景调查", "vars": [], "ambiguity": 2},
            ],
            
            # 劳动关系与合规 - 这是最容易混淆的大类
            "劳动关系与合规": [
                # 🔴 高模糊场景：需要追问才能区分
                {"intent": "有个员工我不想用了，想让他走", "term": "裁员/辞退合规咨询", "vars": [], "ambiguity": 5, "confusion_with": ["孕期合规", "劳动关系合规"]},
                {"intent": "员工表现不好，我想让他走人", "term": "裁员/辞退合规咨询", "vars": [], "ambiguity": 4, "confusion_with": ["竞业限制管理"]},
                {"intent": "公司要减少一些人，不知道怎么弄", "term": "裁员/辞退合规咨询", "vars": [], "ambiguity": 3},
                
                # 🔴 孕期场景 - 需要追问才能发现
                {"intent": "有个女员工老是请假，干活也不行", "term": "孕期合规", "vars": [], "ambiguity": 5, "confusion_with": ["裁员/辞退合规咨询"], "hidden_signal": "她可能怀孕了"},
                {"intent": "有个员工身体不好，总是请假", "term": "孕期合规", "vars": [], "ambiguity": 5, "confusion_with": ["劳动关系合规"], "hidden_signal": "是个女员工，可能是孕期问题"},
                
                {"intent": "有个员工告我了，我该怎么应对", "term": "劳动仲裁应诉代理", "vars": [], "ambiguity": 2},
                {"intent": "公司的规矩太老了，感觉有问题", "term": "员工手册与规章制度设计", "vars": [], "ambiguity": 3},
                {"intent": "员工出了事之后就不来上班了", "term": "劳动关系合规", "vars": [], "ambiguity": 3, "confusion_with": ["裁员/辞退合规咨询"]},
                {"intent": "刚来的员工不行，我想让他走", "term": "裁员/辞退合规咨询", "vars": [], "ambiguity": 3, "hidden_signal": "试用期员工"},
                {"intent": "核心员工跑了，把东西都带走了", "term": "竞业限制管理", "vars": [], "ambiguity": 2},
                {"intent": "员工离职后把客户都带走了", "term": "竞业限制管理", "vars": [], "ambiguity": 2},
                {"intent": "员工把公司的东西泄露出去了", "term": "保密协议与商业秘密", "vars": [], "ambiguity": 2},
            ],
            
            # 薪酬福利与税务
            "薪酬福利与税务": [
                {"intent": "怎么发工资能少交点税", "term": "个税优化/薪税筹划", "vars": [], "ambiguity": 2},
                {"intent": "年底要发钱，怎么发最划算", "term": "个税优化/薪税筹划", "vars": [], "ambiguity": 3, "confusion_with": ["员工福利方案设计"]},
                {"intent": "公司工资乱七八糟的，想整理一下", "term": "薪酬结构设计", "vars": [], "ambiguity": 3},
                {"intent": "社保那些事太麻烦了，能不能找人帮忙", "term": "社保公积金代缴", "vars": [], "ambiguity": 2},
                {"intent": "外地的员工社保怎么弄", "term": "社保公积金代缴", "vars": [], "ambiguity": 2},
                {"intent": "想给员工发点福利，不知道怎么弄", "term": "员工福利方案设计", "vars": [], "ambiguity": 3, "confusion_with": ["个税优化/薪税筹划"]},
            ],
            
            # 组织发展与培训
            "组织发展与培训": [
                {"intent": "管理层水平太差，想提升一下", "term": "企业内训/领导力培训", "vars": [], "ambiguity": 2},
                {"intent": "核心员工老想跳槽，怎么留住人", "term": "股权激励方案设计", "vars": [], "ambiguity": 4, "confusion_with": ["员工敬业度提升"]},
                {"intent": "团队干活没效率，想找人帮忙看看", "term": "企业内训/领导力培训", "vars": [], "ambiguity": 3, "confusion_with": ["员工敬业度提升"]},
                {"intent": "公司人越来越多，管理跟不上", "term": "组织架构设计", "vars": [], "ambiguity": 3},
                {"intent": "员工没有晋升空间，都不想干了", "term": "职级体系设计", "vars": [], "ambiguity": 3, "confusion_with": ["员工敬业度提升"]},
                {"intent": "最近员工士气很低，离职率也高", "term": "员工敬业度提升", "vars": [], "ambiguity": 2},
            ],
        }
        
        # ==========================================
        # 🔀 混淆场景对 (Confusion Pairs) - 用于训练AI区分能力
        # ==========================================
        self.confusion_pairs = [
            ("裁员/辞退合规咨询", "孕期合规", "关键追问：员工是否在孕期/产期？"),
            ("裁员/辞退合规咨询", "竞业限制管理", "关键追问：员工是否掌握核心技术/客户资源？"),
            ("RPO招聘流程外包", "灵活用工/兼职招聘", "关键追问：需要的是长期还是临时？"),
            ("股权激励方案设计", "员工敬业度提升", "关键追问：是想用物质激励还是文化激励？"),
            ("个税优化/薪税筹划", "员工福利方案设计", "关键追问：是发工资还是发福利？"),
        ]
        
        # ==========================================
        # 😰 情绪修饰语（增加真实感）
        # ==========================================
        self.emotions = [
            "真的很头疼，", "这事儿愁死我了，", "不知道该怎么办，",
            "急死了！", "气死我了！", "这事儿拖不得，",
            "听说会很麻烦，", "害怕出问题，", "完全不懂这个，",
            "之前吃过亏，", "朋友公司被坑过，", "",  # 空字符串表示无情绪修饰
        ]
        
        # ==========================================
        # ⏰ 紧急程度修饰
        # ==========================================
        self.urgency = [
            "这事儿很急，", "下周就要解决，", "越快越好，",
            "已经拖了很久了，", "马上要出问题了，", "",
        ]

    def _fill_variables(self, template: str, vars_config: dict) -> str:
        """填充模板中的变量"""
        result = template
        if isinstance(vars_config, list) and vars_config:
            # 简单变量列表，随机选一个插入
            var = random.choice(vars_config)
            result = template.replace("{var}", str(var))
        elif isinstance(vars_config, dict):
            # 字典形式的变量
            for key, values in vars_config.items():
                if values:
                    result = result.replace(f"{{{key}}}", str(random.choice(values)))
        return result

    def _get_scenario_hash(self, scenario: dict) -> str:
        """生成场景的唯一标识（用于去重）"""
        key = f"{scenario.get('novice_intent', '')}_{scenario.get('expert_term', '')}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def generate_secret_mission(self) -> Dict[str, str]:
        """
        生成一个多样化的秘密任务场景
        优先从加载的 JSON 数据库中获取场景模板
        """
        # 1. 优先尝试从 JSON 数据库加载模板
        json_templates = self.domain_db.get("scenario_templates", {})
        
        # 2. 随机选择角色
        persona = random.choice(self.personas)
        
        if json_templates:
            # 使用 JSON 中的模板
            category = random.choice(list(json_templates.keys()))
            intent_list = json_templates[category]
            intent_base = random.choice(intent_list)
            
            # 从 taxonomy 中找到该分类对应的服务（这部分通常需要 expert_term）
            # 简化逻辑：我们直接随机选一个该分类下的服务，或者如果模板本身是一对一的
            # 这里由于 scenario_templates 格式特殊，我们需要找到正确的 term
            expert_term = "未知服务"
            for cat in self.domain_db.get("taxonomy", []):
                if cat["name"] == category and cat.get("services"):
                    expert_term = random.choice(cat["services"])
                    break
        else:
            # 降级：使用硬编码的 HR 场景
            categories = list(self.hr_scenarios.keys())
            category = random.choice(categories)
            templates = self.hr_scenarios.get(category, [])
            template = random.choice(templates)
            intent_base = self._fill_variables(template["intent"], template.get("vars", {}))
            expert_term = template["term"]

        # 3. 添加角色前缀、情绪和紧急程度
        prefix_parts = [persona["prefix"]]
        if random.random() > 0.5:
            prefix_parts.append(random.choice(self.emotions))
        if random.random() > 0.6:
            prefix_parts.append(random.choice(self.urgency))
        
        full_intent = "".join(prefix_parts) + intent_base
        
        # 4. 构建场景
        scenario = {
            "novice_intent": full_intent,
            "expert_term": expert_term,
            "category": category,
            "persona": persona["role"],
            "tone": persona["tone"]
        }
        
        # 7. 去重检查
        scenario_hash = self._get_scenario_hash(scenario)
        max_retries = 10
        retry_count = 0
        
        while scenario_hash in DomainManager._used_scenarios and retry_count < max_retries:
            # 重新生成
            template = random.choice(templates)
            intent_base = self._fill_variables(template["intent"], template.get("vars", {}))
            full_intent = persona["prefix"] + random.choice(self.emotions) + intent_base
            scenario["novice_intent"] = full_intent
            scenario["expert_term"] = template["term"]
            scenario_hash = self._get_scenario_hash(scenario)
            retry_count += 1
        
        # 记录已使用
        DomainManager._used_scenarios.add(scenario_hash)
        
        # 防止内存泄漏：清理过多的历史
        if len(DomainManager._used_scenarios) > 1000:
            DomainManager._used_scenarios.clear()
        
        return scenario

    def get_expert_context(self) -> str:
        """将 JSON 数据转化为 AI 可读的结构化文本"""
        context_lines = []
        taxonomy = self.domain_db.get("taxonomy", [])
        
        context_lines.append(f"=== {self.domain.upper()} 专业服务体系 ===")
        for category in taxonomy:
            cat_name = category.get("name", "通用服务")
            services = category.get("services", [])
            services_str = " | ".join(services)
            context_lines.append(f"📌 [大类: {cat_name}]")
            context_lines.append(f"   └─ 包含服务: {services_str}")
            
        return "\n".join(context_lines)
    
    def get_scenario_stats(self) -> Dict:
        """获取场景统计信息"""
        total_scenarios = sum(len(s) for s in self.hr_scenarios.values())
        return {
            "domain": self.domain,
            "categories": len(self.hr_scenarios),
            "total_templates": total_scenarios,
            "used_count": len(DomainManager._used_scenarios),
            "personas": len(self.personas),
            "emotions": len(self.emotions),
            "estimated_unique_combinations": total_scenarios * len(self.personas) * len(self.emotions) * len(self.urgency)
        }

    @classmethod
    def reset_used_scenarios(cls):
        """重置已使用场景记录（用于新一轮批量挖掘）"""
        cls._used_scenarios.clear()
        print("🔄 已重置场景使用记录")


# 测试代码
if __name__ == "__main__":
    dm = DomainManager("hr")
    
    print("📊 场景生成统计:")
    print(dm.get_scenario_stats())
    print("\n" + "="*60)
    
    print("\n🎲 生成 10 个多样化场景示例:\n")
    for i in range(10):
        mission = dm.generate_secret_mission()
        print(f"[{i+1}] 角色: {mission.get('persona', 'N/A')}")
        print(f"    意图: {mission['novice_intent']}")
        print(f"    术语: {mission['expert_term']}")
        print(f"    类别: {mission['category']}")
        print()