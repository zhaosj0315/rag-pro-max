#!/usr/bin/env python3
"""
RAG Pro Max 智能项目分析器
深度分析项目特点，制定精准的下一步计划
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class SmartProjectAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def analyze_project_context(self) -> Dict[str, Any]:
        """深度分析项目上下文"""
        context = {
            "project_type": self._identify_project_type(),
            "current_features": self._extract_current_features(),
            "user_pain_points": self._identify_pain_points(),
            "missing_capabilities": self._find_missing_capabilities(),
            "improvement_opportunities": self._find_improvement_opportunities()
        }
        return context
    
    def _identify_project_type(self) -> str:
        """识别项目类型"""
        readme = self.project_root / "README.md"
        if readme.exists():
            content = readme.read_text(encoding='utf-8').lower()
            if "rag" in content and "知识库" in content:
                return "RAG知识库系统"
        return "未知项目类型"
    
    def _extract_current_features(self) -> List[str]:
        """提取当前功能特性"""
        features = []
        
        # 从README提取功能
        readme = self.project_root / "README.md"
        if readme.exists():
            content = readme.read_text(encoding='utf-8')
            
            # 查找功能列表
            feature_patterns = [
                r'[✓✅]\s*(.+)',
                r'[-*]\s*\*\*(.+?)\*\*',
                r'###\s*(.+功能)',
                r'##\s*(.+功能)'
            ]
            
            for pattern in feature_patterns:
                matches = re.findall(pattern, content)
                features.extend([m.strip() for m in matches])
        
        # 从代码分析功能
        main_app = self.project_root / "src" / "apppro.py"
        if main_app.exists():
            content = main_app.read_text(encoding='utf-8')
            
            # 查找Streamlit页面和功能
            if "st.sidebar" in content:
                features.append("侧边栏导航")
            if "st.file_uploader" in content:
                features.append("文件上传")
            if "st.chat_input" in content:
                features.append("聊天对话")
            if "vector" in content.lower():
                features.append("向量检索")
        
        return list(set(features))
    
    def _identify_pain_points(self) -> List[Dict[str, Any]]:
        """识别用户痛点"""
        pain_points = []
        
        # 从代码注释中找TODO和FIXME
        py_files = list(self.project_root.rglob("*.py"))
        for file_path in py_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # 查找TODO注释
                todo_matches = re.findall(r'#\s*TODO:?\s*(.+)', content, re.IGNORECASE)
                for todo in todo_matches:
                    pain_points.append({
                        "type": "技术债务",
                        "description": todo.strip(),
                        "file": str(file_path.relative_to(self.project_root)),
                        "priority": "medium"
                    })
                
                # 查找异常处理
                if "except:" in content or "except Exception:" in content:
                    pain_points.append({
                        "type": "错误处理",
                        "description": "存在过于宽泛的异常捕获",
                        "file": str(file_path.relative_to(self.project_root)),
                        "priority": "low"
                    })
            except:
                continue
        
        # 从日志目录分析常见错误
        log_dir = self.project_root / "app_logs"
        if log_dir.exists():
            pain_points.append({
                "type": "用户体验",
                "description": "需要更好的错误提示和用户引导",
                "priority": "high"
            })
        
        return pain_points
    
    def _find_missing_capabilities(self) -> List[Dict[str, Any]]:
        """发现缺失的能力"""
        missing = []
        
        # 检查是否有API接口
        api_files = list(self.project_root.rglob("*api*.py"))
        if not api_files:
            missing.append({
                "capability": "REST API接口",
                "description": "提供程序化访问能力",
                "business_value": "支持第三方集成和自动化",
                "effort": "medium"
            })
        
        # 检查是否有批量处理
        main_app = self.project_root / "src" / "apppro.py"
        if main_app.exists():
            content = main_app.read_text(encoding='utf-8')
            
            if "batch" not in content.lower():
                missing.append({
                    "capability": "批量文档处理",
                    "description": "支持一次性处理多个文档",
                    "business_value": "提升大量文档处理效率",
                    "effort": "medium"
                })
            
            if "export" not in content.lower():
                missing.append({
                    "capability": "数据导出功能",
                    "description": "支持对话记录和知识库导出",
                    "business_value": "数据备份和迁移",
                    "effort": "small"
                })
            
            if "template" not in content.lower():
                missing.append({
                    "capability": "提示词模板",
                    "description": "预设常用提示词模板",
                    "business_value": "提升查询效率和质量",
                    "effort": "small"
                })
        
        return missing
    
    def _find_improvement_opportunities(self) -> List[Dict[str, Any]]:
        """发现改进机会"""
        opportunities = []
        
        # 性能优化机会
        config_dir = self.project_root / "config"
        if config_dir.exists():
            opportunities.append({
                "area": "配置管理",
                "opportunity": "动态配置热更新",
                "description": "支持不重启应用更新配置",
                "impact": "提升运维效率"
            })
        
        # 用户体验优化
        ui_dir = self.project_root / "src" / "ui"
        if ui_dir.exists():
            opportunities.append({
                "area": "用户界面",
                "opportunity": "响应式设计优化",
                "description": "优化移动端和小屏幕显示",
                "impact": "扩大用户群体"
            })
        
        # 智能化提升
        opportunities.append({
            "area": "智能化",
            "opportunity": "自动问题推荐",
            "description": "基于文档内容智能推荐相关问题",
            "impact": "提升用户探索体验"
        })
        
        opportunities.append({
            "area": "智能化", 
            "opportunity": "文档质量评估",
            "description": "自动评估上传文档的质量和完整性",
            "impact": "提升知识库质量"
        })
        
        return opportunities
    
    def generate_next_sprint_plan(self) -> Dict[str, Any]:
        """生成下一个冲刺计划"""
        context = self.analyze_project_context()
        
        # 基于分析结果制定计划
        sprint_plan = {
            "sprint_name": f"Sprint {datetime.now().strftime('%Y%m%d')}",
            "duration": "2周",
            "focus_areas": self._determine_focus_areas(context),
            "user_stories": self._generate_user_stories(context),
            "technical_tasks": self._generate_technical_tasks(context),
            "success_metrics": self._define_success_metrics(context)
        }
        
        return sprint_plan
    
    def _determine_focus_areas(self, context: Dict[str, Any]) -> List[str]:
        """确定重点关注领域"""
        focus_areas = []
        
        # 基于痛点确定重点
        pain_types = [p["type"] for p in context["user_pain_points"]]
        if "用户体验" in pain_types:
            focus_areas.append("用户体验优化")
        if "技术债务" in pain_types:
            focus_areas.append("代码质量提升")
        
        # 基于缺失能力确定重点
        if context["missing_capabilities"]:
            focus_areas.append("功能完善")
        
        return focus_areas or ["稳定性提升"]
    
    def _generate_user_stories(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成用户故事"""
        stories = []
        
        for capability in context["missing_capabilities"]:
            stories.append({
                "title": f"作为用户，我希望有{capability['capability']}",
                "description": capability["description"],
                "acceptance_criteria": [
                    f"功能可以正常使用",
                    f"界面友好易用",
                    f"性能满足要求"
                ],
                "priority": "high" if capability["effort"] == "small" else "medium",
                "effort": capability["effort"]
            })
        
        return stories
    
    def _generate_technical_tasks(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成技术任务"""
        tasks = []
        
        # 基于痛点生成任务
        for pain_point in context["user_pain_points"]:
            if pain_point["priority"] == "high":
                tasks.append({
                    "title": f"修复: {pain_point['description']}",
                    "type": "bugfix",
                    "priority": "high",
                    "estimated_hours": 4
                })
        
        # 基于改进机会生成任务
        for opportunity in context["improvement_opportunities"]:
            tasks.append({
                "title": f"实现: {opportunity['opportunity']}",
                "type": "enhancement",
                "priority": "medium",
                "estimated_hours": 8
            })
        
        return tasks
    
    def _define_success_metrics(self, context: Dict[str, Any]) -> List[str]:
        """定义成功指标"""
        metrics = [
            "用户满意度 > 4.0/5",
            "系统响应时间 < 2秒",
            "错误率 < 1%",
            "功能使用率提升 > 20%"
        ]
        
        # 基于项目特点添加特定指标
        if "RAG" in context["project_type"]:
            metrics.extend([
                "检索准确率 > 85%",
                "文档处理成功率 > 95%"
            ])
        
        return metrics

def main():
    """主函数"""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    analyzer = SmartProjectAnalyzer(project_root)
    
    print("🧠 智能项目分析中...")
    context = analyzer.analyze_project_context()
    
    print("📋 生成下一冲刺计划...")
    sprint_plan = analyzer.generate_next_sprint_plan()
    
    # 保存分析结果
    plans_dir = Path(project_root) / "work_plans"
    plans_dir.mkdir(exist_ok=True)
    
    # 保存详细分析
    analysis_file = plans_dir / f"project_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump({
            "context": context,
            "sprint_plan": sprint_plan
        }, f, indent=2, ensure_ascii=False)
    
    # 生成可读报告
    report = f"""# RAG Pro Max 下一步工作计划

## 📊 项目现状分析

**项目类型**: {context['project_type']}
**当前功能**: {len(context['current_features'])} 个
**发现痛点**: {len(context['user_pain_points'])} 个
**缺失能力**: {len(context['missing_capabilities'])} 个
**改进机会**: {len(context['improvement_opportunities'])} 个

## 🎯 {sprint_plan['sprint_name']} 计划

**持续时间**: {sprint_plan['duration']}
**重点领域**: {', '.join(sprint_plan['focus_areas'])}

### 📝 用户故事

"""
    
    for story in sprint_plan['user_stories']:
        report += f"""#### {story['title']}
- **描述**: {story['description']}
- **优先级**: {story['priority']}
- **工作量**: {story['effort']}

"""
    
    report += """### 🔧 技术任务

"""
    
    for task in sprint_plan['technical_tasks']:
        report += f"""#### {task['title']}
- **类型**: {task['type']}
- **优先级**: {task['priority']}
- **预估时间**: {task['estimated_hours']} 小时

"""
    
    report += f"""### 📈 成功指标

"""
    for metric in sprint_plan['success_metrics']:
        report += f"- {metric}\n"
    
    # 保存报告
    report_file = plans_dir / f"next_sprint_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_file.write_text(report, encoding='utf-8')
    
    print(f"📄 分析报告已保存: {analysis_file}")
    print(f"📋 工作计划已保存: {report_file}")
    
    # 输出摘要
    print(f"\n🎯 下一冲刺计划摘要:")
    print(f"用户故事: {len(sprint_plan['user_stories'])} 个")
    print(f"技术任务: {len(sprint_plan['technical_tasks'])} 个")
    print(f"重点领域: {', '.join(sprint_plan['focus_areas'])}")

if __name__ == "__main__":
    main()
