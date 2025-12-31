#!/usr/bin/env python3
"""
RAG Pro Max 智能规划系统
基于代码和文档分析，自动制定下一步优化计划
"""

import os
import ast
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class OptimizationPlan:
    category: str  # functionality, usability, performance, architecture
    priority: int  # 1-5
    title: str
    description: str
    reasoning: str
    estimated_effort: str  # small, medium, large
    dependencies: List[str]
    files_to_modify: List[str]

class IntelligentPlanner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.src_dir = self.project_root / "src"
        
    def analyze_project(self) -> Dict[str, Any]:
        """分析项目现状"""
        analysis = {
            "code_analysis": self._analyze_code_structure(),
            "feature_gaps": self._identify_feature_gaps(),
            "usability_issues": self._analyze_usability(),
            "architecture_debt": self._analyze_architecture(),
            "user_feedback": self._analyze_user_feedback()
        }
        return analysis
    
    def _analyze_code_structure(self) -> Dict[str, Any]:
        """分析代码结构"""
        py_files = list(self.src_dir.rglob("*.py"))
        
        # 统计各模块复杂度
        modules = {}
        for file_path in py_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    
                    # 统计函数和类
                    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                    
                    modules[str(file_path.relative_to(self.project_root))] = {
                        "lines": len(content.splitlines()),
                        "functions": len(functions),
                        "classes": len(classes),
                        "complexity": self._calculate_complexity(tree)
                    }
            except:
                continue
                
        return modules
    
    def _calculate_complexity(self, tree) -> int:
        """计算代码复杂度"""
        complexity = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try)):
                complexity += 1
        return complexity
    
    def _identify_feature_gaps(self) -> List[Dict[str, Any]]:
        """识别功能缺口"""
        gaps = []
        
        # 检查主应用文件
        main_app = self.src_dir / "apppro.py"
        if main_app.exists():
            content = main_app.read_text(encoding='utf-8')
            
            # 分析现有功能
            if "def " in content:
                # 检查是否缺少常见功能
                missing_features = []
                
                if "export" not in content.lower():
                    missing_features.append("数据导出功能")
                if "batch" not in content.lower():
                    missing_features.append("批量处理功能")
                if "template" not in content.lower():
                    missing_features.append("模板管理功能")
                if "history" not in content.lower():
                    missing_features.append("历史记录管理")
                
                for feature in missing_features:
                    gaps.append({
                        "feature": feature,
                        "impact": "medium",
                        "user_value": "提升工作效率"
                    })
        
        return gaps
    
    def _analyze_usability(self) -> List[Dict[str, Any]]:
        """分析易用性问题"""
        issues = []
        
        # 检查UI组件
        ui_dir = self.src_dir / "ui"
        if ui_dir.exists():
            ui_files = list(ui_dir.rglob("*.py"))
            
            for ui_file in ui_files:
                content = ui_file.read_text(encoding='utf-8')
                
                # 检查常见易用性问题
                if "st.error" in content and "st.success" not in content:
                    issues.append({
                        "file": str(ui_file.relative_to(self.project_root)),
                        "issue": "缺少成功提示",
                        "suggestion": "添加操作成功的用户反馈"
                    })
                
                if "st.button" in content and "help=" not in content:
                    issues.append({
                        "file": str(ui_file.relative_to(self.project_root)),
                        "issue": "按钮缺少帮助文本",
                        "suggestion": "为按钮添加help参数说明功能"
                    })
        
        return issues
    
    def _analyze_architecture(self) -> List[Dict[str, Any]]:
        """分析架构技术债务"""
        debt = []
        
        # 检查大文件
        py_files = list(self.src_dir.rglob("*.py"))
        for file_path in py_files:
            lines = len(file_path.read_text(encoding='utf-8').splitlines())
            if lines > 500:
                debt.append({
                    "file": str(file_path.relative_to(self.project_root)),
                    "issue": f"文件过大 ({lines}行)",
                    "suggestion": "考虑拆分为多个模块"
                })
        
        # 检查重复代码
        # 简化版：检查相似的函数名
        all_functions = []
        for file_path in py_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            all_functions.append(node.name)
            except:
                continue
        
        # 检查重复函数名（可能的重复逻辑）
        from collections import Counter
        func_counts = Counter(all_functions)
        for func_name, count in func_counts.items():
            if count > 2 and not func_name.startswith('_'):
                debt.append({
                    "issue": f"可能的重复逻辑: {func_name} 出现{count}次",
                    "suggestion": "考虑提取公共函数"
                })
        
        return debt
    
    def _analyze_user_feedback(self) -> List[Dict[str, Any]]:
        """分析用户反馈（从README、Issues等）"""
        feedback = []
        
        # 分析README中的TODO
        readme_file = self.project_root / "README.md"
        if readme_file.exists():
            content = readme_file.read_text(encoding='utf-8')
            
            # 查找TODO、FIXME等标记
            todo_patterns = [r'TODO:?\s*(.+)', r'FIXME:?\s*(.+)', r'待实现:?\s*(.+)']
            for pattern in todo_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    feedback.append({
                        "source": "README",
                        "type": "todo",
                        "content": match.strip()
                    })
        
        return feedback
    
    def generate_optimization_plans(self, analysis: Dict[str, Any]) -> List[OptimizationPlan]:
        """基于分析结果生成优化计划"""
        plans = []
        
        # 功能增强计划
        for gap in analysis["feature_gaps"]:
            plans.append(OptimizationPlan(
                category="functionality",
                priority=2,
                title=f"添加{gap['feature']}",
                description=f"实现{gap['feature']}以{gap['user_value']}",
                reasoning=f"当前系统缺少{gap['feature']}，影响用户体验",
                estimated_effort="medium",
                dependencies=[],
                files_to_modify=["src/apppro.py", "src/ui/"]
            ))
        
        # 易用性改进计划
        for issue in analysis["usability_issues"]:
            plans.append(OptimizationPlan(
                category="usability",
                priority=3,
                title=issue["issue"],
                description=issue["suggestion"],
                reasoning="提升用户界面友好性",
                estimated_effort="small",
                dependencies=[],
                files_to_modify=[issue["file"]]
            ))
        
        # 架构优化计划
        for debt in analysis["architecture_debt"]:
            plans.append(OptimizationPlan(
                category="architecture",
                priority=4,
                title=debt["issue"],
                description=debt["suggestion"],
                reasoning="减少技术债务，提升代码质量",
                estimated_effort="large",
                dependencies=[],
                files_to_modify=[debt.get("file", "multiple")]
            ))
        
        # 基于代码分析的性能优化
        large_modules = [f for f, info in analysis["code_analysis"].items() 
                        if info["lines"] > 300 or info["complexity"] > 20]
        
        for module in large_modules:
            plans.append(OptimizationPlan(
                category="performance",
                priority=3,
                title=f"优化{module}模块",
                description="重构复杂模块，提升性能和可维护性",
                reasoning=f"模块{module}复杂度过高，需要重构",
                estimated_effort="large",
                dependencies=[],
                files_to_modify=[module]
            ))
        
        return sorted(plans, key=lambda x: x.priority)
    
    def create_work_plan(self) -> Dict[str, Any]:
        """创建工作计划"""
        print("🔍 分析项目现状...")
        analysis = self.analyze_project()
        
        print("📋 生成优化计划...")
        plans = self.generate_optimization_plans(analysis)
        
        # 按优先级和工作量组织计划
        work_plan = {
            "generated_at": datetime.now().isoformat(),
            "analysis_summary": {
                "total_files": len(analysis["code_analysis"]),
                "feature_gaps": len(analysis["feature_gaps"]),
                "usability_issues": len(analysis["usability_issues"]),
                "architecture_debt": len(analysis["architecture_debt"])
            },
            "immediate_actions": [p for p in plans if p.priority <= 2],
            "short_term_goals": [p for p in plans if p.priority == 3],
            "long_term_improvements": [p for p in plans if p.priority >= 4],
            "detailed_analysis": analysis
        }
        
        return work_plan
    
    def save_work_plan(self, work_plan: Dict[str, Any]):
        """保存工作计划"""
        plans_dir = self.project_root / "work_plans"
        plans_dir.mkdir(exist_ok=True)
        
        plan_file = plans_dir / f"work_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 转换dataclass为dict
        serializable_plan = work_plan.copy()
        for key in ["immediate_actions", "short_term_goals", "long_term_improvements"]:
            serializable_plan[key] = [
                {
                    "category": p.category,
                    "priority": p.priority,
                    "title": p.title,
                    "description": p.description,
                    "reasoning": p.reasoning,
                    "estimated_effort": p.estimated_effort,
                    "dependencies": p.dependencies,
                    "files_to_modify": p.files_to_modify
                }
                for p in serializable_plan[key]
            ]
        
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_plan, f, indent=2, ensure_ascii=False)
        
        print(f"📄 工作计划已保存: {plan_file}")
        return plan_file
    
    def generate_markdown_report(self, work_plan: Dict[str, Any]) -> str:
        """生成Markdown格式的工作计划报告"""
        report = f"""# RAG Pro Max 智能工作计划

**生成时间**: {work_plan['generated_at'][:19]}

## 📊 项目分析摘要

- **代码文件数**: {work_plan['analysis_summary']['total_files']}
- **功能缺口**: {work_plan['analysis_summary']['feature_gaps']} 个
- **易用性问题**: {work_plan['analysis_summary']['usability_issues']} 个  
- **架构债务**: {work_plan['analysis_summary']['architecture_debt']} 个

---

## 🚨 立即行动项 (优先级 1-2)

"""
        for plan in work_plan['immediate_actions']:
            report += f"""### {plan.title}
- **类别**: {plan.category}
- **工作量**: {plan.estimated_effort}
- **描述**: {plan.description}
- **原因**: {plan.reasoning}
- **涉及文件**: {', '.join(plan.files_to_modify)}

"""

        report += """---

## 📅 短期目标 (1-2周内)

"""
        for plan in work_plan['short_term_goals']:
            report += f"""### {plan.title}
- **类别**: {plan.category}
- **工作量**: {plan.estimated_effort}
- **描述**: {plan.description}

"""

        report += """---

## 🎯 长期改进 (1个月内)

"""
        for plan in work_plan['long_term_improvements']:
            report += f"""### {plan.title}
- **类别**: {plan.category}
- **工作量**: {plan.estimated_effort}
- **描述**: {plan.description}

"""

        return report

def main():
    """主函数"""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    planner = IntelligentPlanner(project_root)
    work_plan = planner.create_work_plan()
    
    # 保存JSON格式
    plan_file = planner.save_work_plan(work_plan)
    
    # 生成Markdown报告
    report = planner.generate_markdown_report(work_plan)
    report_file = plan_file.with_suffix('.md')
    report_file.write_text(report, encoding='utf-8')
    
    print(f"📋 Markdown报告已生成: {report_file}")
    
    # 输出摘要
    print(f"\n🎯 下一步工作计划摘要:")
    print(f"立即行动: {len(work_plan['immediate_actions'])} 项")
    print(f"短期目标: {len(work_plan['short_term_goals'])} 项") 
    print(f"长期改进: {len(work_plan['long_term_improvements'])} 项")

if __name__ == "__main__":
    main()
