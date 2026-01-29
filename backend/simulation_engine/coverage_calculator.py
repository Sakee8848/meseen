"""
📊 知识库覆盖率计算器
=====================
核心公式: 覆盖率 = 已覆盖知识节点数 / 预估真实世界知识节点总数 × 100%

预估总数计算方式:
- 角色设定 × 场景类别 × 场景模板 × 情绪修饰 × 紧急程度
- 各维度数量可动态配置和更新

维度说明:
1. 角色设定 (Personas): 创业老板、HR经理、普通员工、部门主管、应届毕业生等
2. 场景类别 (Categories): 招聘、劳动关系、薪酬福利、组织发展
3. 场景模板 (Templates): 每个类别下的具体场景描述
4. 情绪修饰 (Emotions): 头疼、愁死了、急死了、气死了等
5. 紧急程度 (Urgency): 很急、下周解决、越快越好等
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class CoverageCalculator:
    """知识库覆盖率计算器"""
    
    def __init__(self, domain: str = "hr"):
        self.domain = domain
        self.db_path = Path(__file__).resolve().parent.parent / "domain_db" / f"{domain}.json"
        
        # ===========================================
        # 📊 维度配置（可根据业务需求动态更新）
        # ===========================================
        self.dimension_config = {
            "personas": {
                "name": "角色设定",
                "count": 8,
                "items": ["创业老板", "HR经理", "普通员工", "部门主管", "应届毕业生", "资深员工", "外企高管", "初创团队负责人"],
                "description": "不同身份背景的用户"
            },
            "categories": {
                "name": "场景类别",
                "count": 4,
                "items": ["招聘与人才获取", "劳动关系与合规", "薪酬福利与税务", "组织发展与培训"],
                "description": "HR服务的四大核心领域"
            },
            "templates": {
                "name": "场景模板",
                "count_per_category": 8,  # 平均每类 8 个模板
                "total": 30,  # 总计 30+ 个模板
                "description": "每类 6-10 个真实场景"
            },
            "emotions": {
                "name": "情绪修饰",
                "count": 12,
                "items": ["头疼", "愁死了", "不知道怎么办", "急死了", "气死我了", "拖不得", 
                        "听说会很麻烦", "害怕出问题", "完全不懂", "之前吃过亏", "朋友被坑过", "无情绪"],
                "description": "用户的情绪状态"
            },
            "urgency": {
                "name": "紧急程度",
                "count": 6,
                "items": ["很急", "下周要解决", "越快越好", "已经拖了很久", "马上要出问题", "不紧急"],
                "description": "问题的紧迫性"
            }
        }
    
    def get_estimated_total(self) -> int:
        """
        计算预估的真实世界知识节点总数
        
        公式: 角色 × 类别 × 模板 × 情绪 × 紧急程度
        
        注意: 这个数字代表理论上可能存在的所有场景组合
        """
        personas = self.dimension_config["personas"]["count"]
        categories = self.dimension_config["categories"]["count"]
        templates = self.dimension_config["templates"]["total"]
        emotions = self.dimension_config["emotions"]["count"]
        urgency = self.dimension_config["urgency"]["count"]
        
        # 计算总组合数
        total = personas * templates * emotions * urgency
        
        return total
    
    def get_covered_count(self) -> int:
        """
        计算已覆盖的知识节点数
        
        统计方式: 遍历知识库中所有 trace_records，计算去重后的记录数
        """
        if not self.db_path.exists():
            return 0
        
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                db = json.load(f)
            
            # 使用集合去重（基于 query + ai_prediction）
            unique_records = set()
            
            for category in db.get("taxonomy", []):
                trace_records = category.get("trace_records", {})
                for service, records in trace_records.items():
                    for record in records:
                        # 生成去重键
                        key = f"{record.get('query', '')}|{record.get('ai_prediction', '')}"
                        unique_records.add(key)
            
            return len(unique_records)
            
        except Exception as e:
            print(f"❌ 读取知识库失败: {e}")
            return 0
    
    def get_coverage_rate(self) -> float:
        """
        计算覆盖率
        
        返回值: 0.0 ~ 100.0 的浮点数
        """
        covered = self.get_covered_count()
        total = self.get_estimated_total()
        
        if total == 0:
            return 0.0
        
        rate = (covered / total) * 100
        return round(rate, 2)
    
    def get_full_stats(self) -> Dict:
        """
        获取完整的覆盖率统计信息
        
        返回格式:
        {
            "coverage_rate": 2.35,
            "covered_count": 64,
            "estimated_total": 17280,
            "dimensions": {...},
            "formula_explanation": "...",
            "last_updated": "..."
        }
        """
        covered = self.get_covered_count()
        total = self.get_estimated_total()
        rate = (covered / total * 100) if total > 0 else 0
        
        # 获取各维度详细信息
        dimensions = {}
        for key, config in self.dimension_config.items():
            dimensions[key] = {
                "name": config["name"],
                "count": config.get("count", config.get("total", 0)),
                "description": config["description"]
            }
            if "items" in config:
                dimensions[key]["items"] = config["items"]
        
        # 服务节点统计
        service_stats = self._get_service_stats()
        
        return {
            # 核心指标
            "coverage_rate": round(rate, 4),
            "covered_count": covered,
            "estimated_total": total,
            
            # 服务节点
            "service_node_count": service_stats["total_services"],
            "covered_service_count": service_stats["covered_services"],
            "service_coverage_rate": service_stats["service_coverage_rate"],
            
            # 维度详情
            "dimensions": dimensions,
            
            # 计算公式说明
            "formula": {
                "expression": "覆盖率 = 已覆盖知识节点数 ÷ 预估真实世界知识节点总数 × 100%",
                "estimated_total_formula": f"{self.dimension_config['personas']['count']} (角色) × {self.dimension_config['templates']['total']} (模板) × {self.dimension_config['emotions']['count']} (情绪) × {self.dimension_config['urgency']['count']} (紧急程度) = {total}",
                "note": "预估总数代表理论上可能存在的所有场景组合"
            },
            
            # 元信息
            "domain": self.domain,
            "last_updated": datetime.now().isoformat()
        }
    
    def _get_service_stats(self) -> Dict:
        """获取服务节点统计"""
        if not self.db_path.exists():
            return {"total_services": 0, "covered_services": 0, "service_coverage_rate": 0}
        
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                db = json.load(f)
            
            total_services = 0
            covered_services = 0
            
            for category in db.get("taxonomy", []):
                services = category.get("services", [])
                trace_records = category.get("trace_records", {})
                
                total_services += len(services)
                
                # 统计有记录的服务
                for service in services:
                    if service in trace_records and trace_records[service]:
                        covered_services += 1
            
            rate = (covered_services / total_services * 100) if total_services > 0 else 0
            
            return {
                "total_services": total_services,
                "covered_services": covered_services,
                "service_coverage_rate": round(rate, 2)
            }
            
        except Exception as e:
            return {"total_services": 0, "covered_services": 0, "service_coverage_rate": 0}
    
    def update_dimension(self, dimension: str, count: int = None, items: List[str] = None):
        """
        更新维度配置（用于业务调整）
        
        示例:
            calculator.update_dimension("personas", count=10, items=["新角色1", "新角色2", ...])
        """
        if dimension not in self.dimension_config:
            raise ValueError(f"未知维度: {dimension}")
        
        if count is not None:
            self.dimension_config[dimension]["count"] = count
        if items is not None:
            self.dimension_config[dimension]["items"] = items
            self.dimension_config[dimension]["count"] = len(items)


# API 接口函数
def get_coverage_stats(domain: str = "hr") -> Dict:
    """获取覆盖率统计（供 API 调用）"""
    calculator = CoverageCalculator(domain)
    return calculator.get_full_stats()


# 测试代码
if __name__ == "__main__":
    calculator = CoverageCalculator("hr")
    stats = calculator.get_full_stats()
    
    print("=" * 60)
    print("📊 Meseeing 知识库覆盖率报告")
    print("=" * 60)
    print(f"\n🎯 核心指标:")
    print(f"   覆盖率: {stats['coverage_rate']:.4f}%")
    print(f"   已覆盖: {stats['covered_count']} 条")
    print(f"   预估总数: {stats['estimated_total']:,} 条")
    
    print(f"\n📌 服务节点:")
    print(f"   服务总数: {stats['service_node_count']}")
    print(f"   已覆盖服务: {stats['covered_service_count']}")
    print(f"   服务覆盖率: {stats['service_coverage_rate']}%")
    
    print(f"\n📐 计算公式:")
    print(f"   {stats['formula']['estimated_total_formula']}")
    
    print(f"\n📋 维度配置:")
    for key, dim in stats['dimensions'].items():
        print(f"   {dim['name']}: {dim['count']} 种 ({dim['description']})")
    print()
