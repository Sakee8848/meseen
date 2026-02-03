"""
📊 保险密心 - 知识库覆盖率计算器
=================================
计算各保险服务类别的知识库覆盖情况
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


class InsuranceCoverageCalculator:
    """保险知识库覆盖率计算器"""
    
    def __init__(self, domain: str = "insurance"):
        self.domain = domain
        self.db_path = Path(__file__).resolve().parent.parent / "domain_db" / f"{domain}.json"
        self.data = self._load_data()
    
    def _load_data(self) -> dict:
        """加载知识库数据"""
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {"taxonomy": []}
    
    def calculate_coverage(self) -> Dict:
        """计算整体覆盖率"""
        taxonomy = self.data.get("taxonomy", [])
        
        total_services = 0
        covered_services = 0
        total_traces = 0
        
        category_stats = []
        
        for cat in taxonomy:
            cat_name = cat["name"]
            services = cat.get("services", [])
            trace_records = cat.get("trace_records", {})
            
            cat_total = len(services)
            cat_covered = 0
            cat_traces = 0
            
            service_details = []
            
            for svc in services:
                svc_key = svc.split(" ")[0] if " " in svc else svc
                traces = trace_records.get(svc_key, [])
                trace_count = len(traces)
                
                if trace_count > 0:
                    cat_covered += 1
                    covered_services += 1
                
                cat_traces += trace_count
                total_traces += trace_count
                total_services += 1
                
                service_details.append({
                    "name": svc,
                    "trace_count": trace_count,
                    "is_covered": trace_count > 0
                })
            
            category_stats.append({
                "name": cat_name,
                "total_services": cat_total,
                "covered_services": cat_covered,
                "coverage_rate": cat_covered / cat_total if cat_total > 0 else 0,
                "total_traces": cat_traces,
                "services": service_details
            })
        
        return {
            "summary": {
                "total_categories": len(taxonomy),
                "total_services": total_services,
                "covered_services": covered_services,
                "coverage_rate": covered_services / total_services if total_services > 0 else 0,
                "total_traces": total_traces
            },
            "categories": category_stats
        }
    
    def get_uncovered_services(self) -> List[Tuple[str, str]]:
        """获取未覆盖的服务列表"""
        coverage = self.calculate_coverage()
        uncovered = []
        
        for cat in coverage["categories"]:
            for svc in cat["services"]:
                if not svc["is_covered"]:
                    uncovered.append((cat["name"], svc["name"]))
        
        return uncovered
    
    def get_priority_queue(self) -> List[dict]:
        """获取优先挖掘队列（按覆盖率从低到高排序）"""
        coverage = self.calculate_coverage()
        
        priority = []
        for cat in coverage["categories"]:
            for svc in cat["services"]:
                priority.append({
                    "category": cat["name"],
                    "service": svc["name"],
                    "trace_count": svc["trace_count"],
                    "priority_score": 1 / (svc["trace_count"] + 1)  # 越少越优先
                })
        
        priority.sort(key=lambda x: x["priority_score"], reverse=True)
        return priority
    
    def print_report(self):
        """打印覆盖率报告"""
        coverage = self.calculate_coverage()
        summary = coverage["summary"]
        
        print("\n" + "="*60)
        print("📊 保险密心知识库覆盖率报告")
        print("="*60)
        
        print(f"\n📈 总体统计:")
        print(f"   服务类别: {summary['total_categories']} 个")
        print(f"   服务总数: {summary['total_services']} 项")
        print(f"   已覆盖数: {summary['covered_services']} 项")
        print(f"   覆盖率: {summary['coverage_rate']*100:.1f}%")
        print(f"   追踪记录总数: {summary['total_traces']} 条")
        
        print(f"\n📋 分类明细:")
        for cat in coverage["categories"]:
            rate = cat["coverage_rate"] * 100
            bar = "█" * int(rate / 5) + "░" * (20 - int(rate / 5))
            print(f"\n   【{cat['name']}】")
            print(f"   [{bar}] {rate:.0f}% ({cat['covered_services']}/{cat['total_services']})")
            print(f"   追踪记录: {cat['total_traces']} 条")
        
        # 显示未覆盖服务
        uncovered = self.get_uncovered_services()
        if uncovered:
            print(f"\n⚠️  未覆盖服务 ({len(uncovered)} 项):")
            for cat, svc in uncovered[:10]:  # 只显示前10个
                print(f"   - {svc}")
            if len(uncovered) > 10:
                print(f"   ... 还有 {len(uncovered) - 10} 项")
        
        print("\n" + "="*60)


# 命令行入口
if __name__ == "__main__":
    calc = InsuranceCoverageCalculator("insurance")
    calc.print_report()
