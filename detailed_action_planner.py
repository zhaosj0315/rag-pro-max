#!/usr/bin/env python3
"""
RAG Pro Max 单功能迭代规划系统 V2.0
基于项目当前状态，制定下一步功能优化计划并实施
核心原则：一次一个功能，零污染原则，分支开发，完成->测试->验证->文档->确认->下一个
"""

import os
import json
from datetime import datetime
from pathlib import Path

class SingleFeatureIterationPlanner:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.iteration_log = self.project_root / "iteration_log.json"
        
    def analyze_and_plan_next_feature(self):
        """分析项目状态，制定下一个功能的具体计划"""
        
        # 检查当前迭代状态
        current_iteration = self._get_current_iteration_status()
        
        if current_iteration["status"] == "pending_user_approval":
            return self._generate_approval_request(current_iteration)
        
        # 分析项目现状
        project_analysis = self._analyze_project_state()
        
        # 选择下一个最重要的功能
        next_feature = self._select_next_feature(project_analysis)
        
        # 生成详细实施计划
        implementation_plan = self._create_implementation_plan(next_feature)
        
        # 记录新的迭代
        self._start_new_iteration(next_feature, implementation_plan)
        
        return {
            "analysis": project_analysis,
            "selected_feature": next_feature,
            "implementation_plan": implementation_plan,
            "iteration_workflow": self._get_iteration_workflow()
        }
    
    def _get_current_iteration_status(self):
        """获取当前迭代状态"""
        if not self.iteration_log.exists():
            return {"status": "none"}
        
        with open(self.iteration_log, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        current = data.get("current_iteration", {})
        return current
    
    def _analyze_project_state(self):
        """分析项目当前状态"""
        main_app = self.project_root / "src" / "apppro.py"
        
        if not main_app.exists():
            return {"error": "主应用文件不存在"}
        
        content = main_app.read_text(encoding='utf-8')
        
        # 分析具体问题
        issues = []
        
        # 用户体验问题
        if "st.text_input" in content and content.count("placeholder=") < content.count("st.text_input"):
            issues.append({
                "category": "用户体验",
                "problem": "输入框缺少提示文本",
                "impact": "用户不知道该输入什么",
                "priority": "high",
                "effort": "small"
            })
        
        if "st.error" in content and content.count("st.success") < content.count("st.error") * 0.5:
            issues.append({
                "category": "用户体验", 
                "problem": "负面反馈过多，缺少成功提示",
                "impact": "用户体验偏负面",
                "priority": "medium",
                "effort": "small"
            })
        
        # 功能完整性问题
        if "progress" not in content.lower():
            issues.append({
                "category": "功能完整性",
                "problem": "缺少处理进度显示",
                "impact": "用户不知道处理状态",
                "priority": "high", 
                "effort": "medium"
            })
        
        if "template" not in content.lower() and "模板" not in content:
            issues.append({
                "category": "功能完整性",
                "problem": "缺少问题模板功能",
                "impact": "新用户不知道如何提问",
                "priority": "high",
                "effort": "small"
            })
        
        return {
            "total_issues": len(issues),
            "high_priority": [i for i in issues if i["priority"] == "high"],
            "medium_priority": [i for i in issues if i["priority"] == "medium"],
            "all_issues": issues
        }
    
    def _select_next_feature(self, analysis):
        """选择下一个要实现的功能（优先级：high + small effort）"""
        high_priority = analysis["high_priority"]
        
        # 优先选择高优先级且工作量小的
        for issue in high_priority:
            if issue["effort"] == "small":
                return {
                    "title": self._generate_feature_title(issue),
                    "problem": issue["problem"],
                    "solution": self._generate_solution(issue),
                    "priority": issue["priority"],
                    "effort": issue["effort"],
                    "category": issue["category"]
                }
        
        # 如果没有小工作量的，选择第一个高优先级
        if high_priority:
            issue = high_priority[0]
            return {
                "title": self._generate_feature_title(issue),
                "problem": issue["problem"], 
                "solution": self._generate_solution(issue),
                "priority": issue["priority"],
                "effort": issue["effort"],
                "category": issue["category"]
            }
        
        # 兜底：选择中优先级
        medium_priority = analysis["medium_priority"]
        if medium_priority:
            issue = medium_priority[0]
            return {
                "title": self._generate_feature_title(issue),
                "problem": issue["problem"],
                "solution": self._generate_solution(issue), 
                "priority": issue["priority"],
                "effort": issue["effort"],
                "category": issue["category"]
            }
        
        return {"title": "项目优化完成", "problem": "未发现需要改进的问题"}
    
    def _generate_feature_title(self, issue):
        """生成功能标题"""
        titles = {
            "输入框缺少提示文本": "改进输入框用户引导",
            "负面反馈过多，缺少成功提示": "增加操作成功反馈",
            "缺少处理进度显示": "添加文档处理进度条",
            "缺少问题模板功能": "添加常用问题模板"
        }
        return titles.get(issue["problem"], f"解决：{issue['problem']}")
    
    def _generate_solution(self, issue):
        """生成解决方案"""
        solutions = {
            "输入框缺少提示文本": {
                "what": "为所有输入框添加placeholder和help参数（仅新增，不修改现有功能）",
                "why": "让用户明确知道该输入什么内容",
                "how": [
                    "1. 找到src/apppro.py中的st.text_input调用",
                    "2. 仅为缺少placeholder的输入框添加参数",
                    "3. 添加help='详细说明'参数",
                    "4. 测试所有输入框的显示效果",
                    "⚠️ 注意：不修改现有功能，只添加缺失的提示"
                ],
                "files": ["src/apppro.py"],
                "time": "30分钟"
            },
            "负面反馈过多，缺少成功提示": {
                "what": "在关键操作成功后添加st.success提示（纯新增功能）",
                "why": "让用户感受到操作成功，提升使用信心",
                "how": [
                    "1. 在文件上传成功后添加成功提示",
                    "2. 在知识库创建后添加成功提示", 
                    "3. 在查询完成后添加成功提示",
                    "4. 测试所有成功提示的显示",
                    "⚠️ 注意：只添加新的提示，不修改现有错误处理逻辑"
                ],
                "files": ["src/apppro.py"],
                "time": "45分钟"
            },
            "缺少处理进度显示": {
                "what": "添加文档处理进度条和状态显示",
                "why": "用户上传大文件时需要知道处理进度",
                "how": [
                    "1. 创建进度显示组件",
                    "2. 在文件处理时显示进度条",
                    "3. 显示处理状态文本",
                    "4. 完成后显示统计信息"
                ],
                "files": ["src/ui/progress_display.py", "src/apppro.py"],
                "time": "1.5小时"
            },
            "缺少问题模板功能": {
                "what": "在侧边栏添加常用问题模板选择器",
                "why": "帮助新用户快速开始使用系统",
                "how": [
                    "1. 在侧边栏添加模板选择框",
                    "2. 预设常用问题模板",
                    "3. 选择后自动填入输入框",
                    "4. 测试模板选择和应用功能"
                ],
                "files": ["src/apppro.py"],
                "time": "1小时"
            }
        }
        return solutions.get(issue["problem"], {
            "what": f"解决{issue['problem']}",
            "why": "改善用户体验",
            "how": ["待详细分析"],
            "files": ["src/apppro.py"],
            "time": "待评估"
        })
    
    def _create_implementation_plan(self, feature):
        """创建详细实施计划"""
        return {
            "phase_1_implement": {
                "description": "实现功能代码",
                "tasks": feature["solution"]["how"],
                "files": feature["solution"]["files"],
                "estimated_time": feature["solution"]["time"]
            },
            "phase_2_test": {
                "description": "自动测试验证",
                "tasks": [
                    "运行功能测试脚本",
                    "检查代码语法错误",
                    "验证功能正常工作",
                    "测试边界情况"
                ]
            },
            "phase_3_document": {
                "description": "更新相关文档",
                "tasks": [
                    "更新README.md功能说明",
                    "更新CHANGELOG.md版本记录",
                    "添加功能使用说明",
                    "更新API文档（如需要）"
                ]
            },
            "phase_4_approval": {
                "description": "等待用户验证确认",
                "tasks": [
                    "提交功能演示",
                    "说明改进效果",
                    "等待用户确认",
                    "收集反馈意见"
                ]
            }
        }
    
    def _get_iteration_workflow(self):
        """获取迭代工作流程"""
        return {
            "workflow": "单功能迭代流程",
            "steps": [
                "1️⃣ 分析项目状态，选择下一个功能",
                "2️⃣ 实现功能代码",
                "3️⃣ 自动测试验证",
                "4️⃣ 更新相关文档",
                "5️⃣ 提交用户验证",
                "6️⃣ 用户确认后进入下一个功能"
            ],
            "principles": [
                "🎯 一次只做一个功能",
                "🧪 每个功能都要测试",
                "📝 及时更新文档",
                "✅ 用户确认才继续"
            ]
        }
    
    def _start_new_iteration(self, feature, plan):
        """开始新的迭代"""
        iteration_data = {
            "current_iteration": {
                "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "feature": feature,
                "plan": plan,
                "status": "planning",
                "started_at": datetime.now().isoformat(),
                "phase": "phase_1_implement"
            },
            "history": []
        }
        
        # 如果已有历史记录，保留
        if self.iteration_log.exists():
            with open(self.iteration_log, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                iteration_data["history"] = existing_data.get("history", [])
        
        with open(self.iteration_log, 'w', encoding='utf-8') as f:
            json.dump(iteration_data, f, indent=2, ensure_ascii=False)
    
    def _generate_approval_request(self, current_iteration):
        """生成用户确认请求"""
        return {
            "status": "waiting_for_approval",
            "message": "当前功能已完成实现和测试，等待您的验证确认",
            "feature": current_iteration["feature"],
            "completed_phases": ["实现", "测试", "文档更新"],
            "next_action": "请验证功能效果，确认后可进入下一个功能开发"
        }

def main():
    """主函数"""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    planner = SingleFeatureIterationPlanner(project_root)
    result = planner.analyze_and_plan_next_feature()
    
    print("🎯 RAG Pro Max 单功能迭代规划")
    print("=" * 50)
    
    if result.get("status") == "waiting_for_approval":
        print("⏳ 等待用户验证确认")
        print(f"功能: {result['feature']['title']}")
        print("请验证功能效果后确认是否继续下一个功能")
        return
    
    feature = result["selected_feature"]
    print(f"📋 下一个功能: {feature['title']}")
    print(f"🎯 解决问题: {feature['problem']}")
    print(f"⚡ 优先级: {feature['priority']}")
    print(f"⏱️ 工作量: {feature['effort']}")
    
    solution = feature["solution"]
    print(f"\n💡 解决方案:")
    print(f"做什么: {solution['what']}")
    print(f"为什么: {solution['why']}")
    print(f"预估时间: {solution['time']}")
    
    print(f"\n🔧 具体步骤:")
    for step in solution["how"]:
        print(f"  {step}")
    
    print(f"\n📁 涉及文件: {', '.join(solution['files'])}")
    
    workflow = result["iteration_workflow"]
    print(f"\n🔄 迭代流程:")
    for step in workflow["steps"]:
        print(f"  {step}")

if __name__ == "__main__":
    main()
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def analyze_and_plan(self):
        """分析项目并生成具体行动计划"""
        
        # 分析当前项目状态
        current_state = self._analyze_current_state()
        
        # 生成具体改进计划
        action_plans = self._generate_specific_plans(current_state)
        
        return {
            "analysis_time": datetime.now().isoformat(),
            "current_state": current_state,
            "action_plans": action_plans
        }
    
    def _analyze_current_state(self):
        """分析当前项目状态"""
        main_app = self.project_root / "src" / "apppro.py"
        
        issues = []
        
        if main_app.exists():
            content = main_app.read_text(encoding='utf-8')
            
            # 具体问题分析
            if "st.text_input" in content and "placeholder=" not in content:
                issues.append({
                    "problem": "输入框缺少提示文本",
                    "impact": "用户不知道该输入什么",
                    "location": "主界面输入框"
                })
            
            if "st.error" in content and content.count("st.success") < content.count("st.error"):
                issues.append({
                    "problem": "错误提示多于成功提示",
                    "impact": "用户体验偏负面",
                    "location": "错误处理逻辑"
                })
            
            if "TODO" in content or "FIXME" in content:
                issues.append({
                    "problem": "代码中有未完成的TODO项",
                    "impact": "功能不完整",
                    "location": "源代码注释"
                })
        
        # 检查配置文件
        config_dir = self.project_root / "config"
        if config_dir.exists():
            config_files = list(config_dir.glob("*.json"))
            if len(config_files) > 3:
                issues.append({
                    "problem": "配置文件过多且分散",
                    "impact": "配置管理复杂",
                    "location": "config目录"
                })
        
        return {
            "total_issues": len(issues),
            "issues": issues,
            "project_size": len(list(self.project_root.rglob("*.py")))
        }
    
    def _generate_specific_plans(self, current_state):
        """生成具体的行动计划"""
        plans = []
        
        for issue in current_state["issues"]:
            if "输入框缺少提示文本" in issue["problem"]:
                plans.append({
                    "title": "改进用户输入体验",
                    "what_to_do": "为所有输入框添加清晰的提示文本",
                    "why_important": "让用户明确知道该输入什么内容，减少困惑",
                    "how_to_implement": [
                        "1. 找到src/apppro.py中的所有st.text_input调用",
                        "2. 为每个输入框添加placeholder参数",
                        "3. 添加help参数提供详细说明",
                        "4. 示例：st.text_input('问题', placeholder='请输入您的问题...', help='支持中英文问题')"
                    ],
                    "expected_result": "用户输入更顺畅，减少50%的输入错误",
                    "files_to_change": ["src/apppro.py"],
                    "estimated_time": "30分钟",
                    "priority": "high"
                })
            
            elif "错误提示多于成功提示" in issue["problem"]:
                plans.append({
                    "title": "平衡用户反馈体验",
                    "what_to_do": "增加成功操作的正面反馈提示",
                    "why_important": "让用户感受到操作成功，提升使用信心",
                    "how_to_implement": [
                        "1. 在文件上传成功后添加st.success('文件上传成功！')",
                        "2. 在知识库创建后添加st.success('知识库创建完成！')",
                        "3. 在查询完成后添加st.success('查询结果已生成')",
                        "4. 为每个主要操作添加进度提示"
                    ],
                    "expected_result": "用户满意度提升，操作更有成就感",
                    "files_to_change": ["src/apppro.py", "src/ui/*.py"],
                    "estimated_time": "1小时",
                    "priority": "medium"
                })
            
            elif "配置文件过多" in issue["problem"]:
                plans.append({
                    "title": "统一配置管理",
                    "what_to_do": "将分散的配置文件合并为一个主配置文件",
                    "why_important": "简化配置管理，减少维护成本",
                    "how_to_implement": [
                        "1. 创建config/main_config.json作为主配置",
                        "2. 将app_config.json和rag_config.json内容合并",
                        "3. 修改代码中的配置读取逻辑",
                        "4. 保留原文件作为备份"
                    ],
                    "expected_result": "配置管理更简单，减少配置错误",
                    "files_to_change": ["config/*.json", "src/services/config_service.py"],
                    "estimated_time": "2小时",
                    "priority": "low"
                })
        
        # 基于项目特点添加功能改进计划
        plans.extend(self._generate_feature_plans())
        
        return plans
    
    def _generate_feature_plans(self):
        """生成功能改进计划"""
        return [
            {
                "title": "添加常用问题模板",
                "what_to_do": "创建一个问题模板选择器，让用户快速选择常见问题类型",
                "why_important": "新用户不知道该问什么，模板可以引导用户更好地使用系统",
                "how_to_implement": [
                    "1. 在侧边栏添加'常用问题'选择框",
                    "2. 预设5-10个常见问题模板，如：",
                    "   - '请总结这个文档的主要内容'",
                    "   - '这个文档中有哪些重要的数据或结论？'",
                    "   - '基于文档内容，给我一些实用建议'",
                    "3. 用户选择模板后自动填入输入框",
                    "4. 允许用户修改模板内容"
                ],
                "expected_result": "新用户上手更快，提问质量提升30%",
                "files_to_change": ["src/apppro.py"],
                "estimated_time": "1.5小时",
                "priority": "high"
            },
            {
                "title": "添加文档处理进度显示",
                "what_to_do": "在文档上传和处理时显示详细的进度条和状态信息",
                "why_important": "用户上传大文件时不知道处理进度，容易以为系统卡死",
                "how_to_implement": [
                    "1. 使用st.progress()显示处理进度",
                    "2. 添加状态文本：'正在读取文件...'、'正在分析内容...'、'正在构建索引...'",
                    "3. 显示处理时间估计",
                    "4. 处理完成后显示文档统计信息（页数、字数等）"
                ],
                "expected_result": "用户等待体验更好，减少90%的中途放弃",
                "files_to_change": ["src/file_processor.py", "src/apppro.py"],
                "estimated_time": "2小时",
                "priority": "high"
            },
            {
                "title": "添加对话历史快速访问",
                "what_to_do": "在侧边栏显示最近的对话记录，支持快速切换",
                "why_important": "用户想回看之前的对话内容，现在只能重新提问",
                "how_to_implement": [
                    "1. 在侧边栏添加'历史对话'折叠面板",
                    "2. 显示最近10次对话的标题（取问题前20字）",
                    "3. 点击历史记录可以查看完整对话",
                    "4. 支持删除和收藏功能"
                ],
                "expected_result": "用户可以轻松回顾历史对话，提升使用效率",
                "files_to_change": ["src/apppro.py", "src/chat_history.py"],
                "estimated_time": "3小时",
                "priority": "medium"
            }
        ]
    
    def generate_detailed_report(self, analysis_result):
        """生成详细的行动报告"""
        report = f"""# RAG Pro Max 具体行动计划

**生成时间**: {analysis_result['analysis_time'][:19]}

## 🔍 当前问题分析

发现 **{analysis_result['current_state']['total_issues']}** 个具体问题需要解决：

"""
        
        for i, issue in enumerate(analysis_result['current_state']['issues'], 1):
            report += f"""### 问题 {i}: {issue['problem']}
- **影响**: {issue['impact']}
- **位置**: {issue['location']}

"""
        
        report += """---

## 🎯 具体行动计划

"""
        
        # 按优先级排序
        high_priority = [p for p in analysis_result['action_plans'] if p['priority'] == 'high']
        medium_priority = [p for p in analysis_result['action_plans'] if p['priority'] == 'medium']
        low_priority = [p for p in analysis_result['action_plans'] if p['priority'] == 'low']
        
        for priority_name, plans in [("🔥 高优先级（立即执行）", high_priority), 
                                   ("⚡ 中优先级（本周完成）", medium_priority),
                                   ("📋 低优先级（有时间再做）", low_priority)]:
            if plans:
                report += f"""### {priority_name}

"""
                for plan in plans:
                    report += f"""#### {plan['title']}

**要做什么**: {plan['what_to_do']}

**为什么重要**: {plan['why_important']}

**具体怎么做**:
"""
                    for step in plan['how_to_implement']:
                        report += f"{step}\n"
                    
                    report += f"""
**预期效果**: {plan['expected_result']}
**需要修改的文件**: {', '.join(plan['files_to_change'])}
**预估时间**: {plan['estimated_time']}

---

"""
        
        # 添加总结
        total_time = sum([
            float(p['estimated_time'].split('小时')[0]) if '小时' in p['estimated_time'] 
            else float(p['estimated_time'].split('分钟')[0])/60 if '分钟' in p['estimated_time']
            else 0.5
            for p in analysis_result['action_plans']
        ])
        
        report += f"""## 📊 执行总结

- **总计划数**: {len(analysis_result['action_plans'])} 个
- **高优先级**: {len(high_priority)} 个
- **预估总时间**: {total_time:.1f} 小时
- **建议执行顺序**: 先做高优先级，再做中优先级

## 🎯 下一步行动

1. **今天就做**: {high_priority[0]['title'] if high_priority else '无'}
2. **本周完成**: 所有高优先级计划
3. **下周开始**: 中优先级计划

---

*这个计划基于当前代码分析生成，具体实施时可根据实际情况调整*
"""
        
        return report

def main():
    """主函数"""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    
    planner = SingleFeatureIterationPlanner(project_root)
    result = planner.analyze_and_plan_next_feature()
    
    print("🎯 RAG Pro Max 单功能迭代规划")
    print("=" * 50)
    
    if result.get("status") == "waiting_for_approval":
        print("⏳ 等待用户验证确认")
        print(f"功能: {result['feature']['title']}")
        print("请验证功能效果后确认是否继续下一个功能")
        return
    
    feature = result["selected_feature"]
    print(f"📋 下一个功能: {feature['title']}")
    print(f"🎯 解决问题: {feature['problem']}")
    print(f"⚡ 优先级: {feature['priority']}")
    print(f"⏱️ 工作量: {feature['effort']}")
    
    solution = feature["solution"]
    print(f"\n💡 解决方案:")
    print(f"做什么: {solution['what']}")
    print(f"为什么: {solution['why']}")
    print(f"预估时间: {solution['time']}")
    
    print(f"\n🔧 具体步骤:")
    for step in solution["how"]:
        print(f"  {step}")
    
    print(f"\n📁 涉及文件: {', '.join(solution['files'])}")
    
    workflow = result["iteration_workflow"]
    print(f"\n🔄 迭代流程:")
    for step in workflow["steps"]:
        print(f"  {step}")
    
    # 保存计划到文件
    plans_dir = Path(project_root) / "work_plans"
    plans_dir.mkdir(exist_ok=True)
    
    plan_file = plans_dir / f"single_feature_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(plan_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 计划已保存: {plan_file}")

if __name__ == "__main__":
    main()
