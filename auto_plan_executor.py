#!/usr/bin/env python3
"""
RAG Pro Max 自动化工作计划执行器
根据分析结果自动执行改进任务
"""

import os
import json
from datetime import datetime
from pathlib import Path

class AutoPlanExecutor:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        
    def execute_plan(self, plan_file: str):
        """执行工作计划"""
        with open(plan_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        sprint_plan = data['sprint_plan']
        
        print(f"🚀 开始执行 {sprint_plan['sprint_name']}")
        
        # 执行技术任务
        for task in sprint_plan['technical_tasks']:
            if task['type'] == 'enhancement':
                self._execute_enhancement(task)
            elif task['type'] == 'bugfix':
                self._execute_bugfix(task)
    
    def _execute_enhancement(self, task: dict):
        """执行功能增强任务"""
        print(f"🔧 执行增强任务: {task['title']}")
        
        if "提示词模板" in task['title']:
            self._create_prompt_templates()
        elif "动态配置" in task['title']:
            self._implement_hot_config()
        elif "问题推荐" in task['title']:
            self._implement_question_recommendation()
    
    def _create_prompt_templates(self):
        """创建提示词模板功能"""
        templates_dir = self.project_root / "prompt_templates"
        templates_dir.mkdir(exist_ok=True)
        
        # 创建模板文件
        templates = {
            "文档总结": "请帮我总结这个文档的主要内容，包括关键点和结论。",
            "问题解答": "基于提供的文档内容，请详细回答以下问题：",
            "代码分析": "请分析这段代码的功能、逻辑和可能的改进点。",
            "学习指导": "请为我制定一个关于这个主题的学习计划和要点。"
        }
        
        template_file = templates_dir / "default_templates.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 提示词模板已创建: {template_file}")
    
    def _implement_hot_config(self):
        """实现热配置更新"""
        config_watcher = self.project_root / "config_watcher.py"
        
        code = '''#!/usr/bin/env python3
"""
配置文件监控器 - 支持热更新
"""
import json
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigHandler(FileSystemEventHandler):
    def __init__(self, config_file):
        self.config_file = config_file
        
    def on_modified(self, event):
        if event.src_path == str(self.config_file):
            print(f"🔄 配置文件已更新: {self.config_file}")
            # 这里可以添加重新加载配置的逻辑

def watch_config(config_file):
    """监控配置文件变化"""
    event_handler = ConfigHandler(config_file)
    observer = Observer()
    observer.schedule(event_handler, str(config_file.parent), recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    config_file = Path("config/app_config.json")
    watch_config(config_file)
'''
        
        config_watcher.write_text(code, encoding='utf-8')
        print(f"✅ 配置监控器已创建: {config_watcher}")
    
    def _execute_bugfix(self, task: dict):
        """执行错误修复任务"""
        print(f"🐛 执行修复任务: {task['title']}")
        
        if "错误提示" in task['title']:
            self._improve_error_messages()
    
    def _improve_error_messages(self):
        """改进错误提示"""
        error_handler = self.project_root / "error_handler.py"
        
        code = '''#!/usr/bin/env python3
"""
改进的错误处理器
"""
import streamlit as st
from typing import Optional

class UserFriendlyErrorHandler:
    @staticmethod
    def show_error(error_type: str, message: str, suggestion: Optional[str] = None):
        """显示用户友好的错误信息"""
        error_messages = {
            "file_upload": "文件上传失败",
            "processing": "文档处理出错", 
            "query": "查询执行失败",
            "config": "配置加载错误"
        }
        
        title = error_messages.get(error_type, "系统错误")
        
        with st.error(title):
            st.write(f"错误详情: {message}")
            if suggestion:
                st.write(f"建议: {suggestion}")
            st.write("如果问题持续存在，请联系技术支持。")
    
    @staticmethod
    def show_success(message: str):
        """显示成功信息"""
        st.success(f"✅ {message}")
    
    @staticmethod
    def show_warning(message: str):
        """显示警告信息"""
        st.warning(f"⚠️ {message}")
'''
        
        error_handler.write_text(code, encoding='utf-8')
        print(f"✅ 错误处理器已创建: {error_handler}")
    
    def _implement_question_recommendation(self):
        """实现问题推荐功能"""
        recommender_file = self.project_root / "question_recommender.py"
        
        code = '''#!/usr/bin/env python3
"""
智能问题推荐器
"""
import re
from typing import List

class QuestionRecommender:
    def __init__(self):
        self.question_templates = [
            "这个文档的主要观点是什么？",
            "能否详细解释一下{}？",
            "{}的优缺点有哪些？",
            "如何实际应用{}？",
            "{}与其他方案相比有什么特点？"
        ]
    
    def recommend_questions(self, document_content: str) -> List[str]:
        """基于文档内容推荐问题"""
        # 提取关键词
        keywords = self._extract_keywords(document_content)
        
        # 生成推荐问题
        questions = []
        for keyword in keywords[:3]:  # 取前3个关键词
            for template in self.question_templates[:2]:  # 取前2个模板
                if "{}" in template:
                    questions.append(template.format(keyword))
                else:
                    questions.append(template)
        
        return questions[:5]  # 返回前5个问题
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词（简化版）"""
        # 简单的关键词提取
        words = re.findall(r'\\b[\\w]{3,}\\b', content)
        # 过滤常见词汇
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而'}
        keywords = [w for w in words if w not in stop_words]
        
        # 返回出现频率最高的词
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(10)]
'''
        
        recommender_file.write_text(code, encoding='utf-8')
        print(f"✅ 问题推荐器已创建: {recommender_file}")
        """实现问题推荐功能"""
        recommender_file = self.project_root / "question_recommender.py"
        
        code = '''#!/usr/bin/env python3
"""
智能问题推荐器
"""
import re
from typing import List

class QuestionRecommender:
    def __init__(self):
        self.question_templates = [
            "这个文档的主要观点是什么？",
            "能否详细解释一下{}？",
            "{}的优缺点有哪些？",
            "如何实际应用{}？",
            "{}与其他方案相比有什么特点？"
        ]
    
    def recommend_questions(self, document_content: str) -> List[str]:
        """基于文档内容推荐问题"""
        # 提取关键词
        keywords = self._extract_keywords(document_content)
        
        # 生成推荐问题
        questions = []
        for keyword in keywords[:3]:  # 取前3个关键词
            for template in self.question_templates[:2]:  # 取前2个模板
                if "{}" in template:
                    questions.append(template.format(keyword))
                else:
                    questions.append(template)
        
        return questions[:5]  # 返回前5个问题
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词（简化版）"""
        # 简单的关键词提取
        words = re.findall(r'\\b[\\w]{3,}\\b', content)
        # 过滤常见词汇
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '而'}
        keywords = [w for w in words if w not in stop_words]
        
        # 返回出现频率最高的词
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(10)]
'''
        
        recommender_file.write_text(code, encoding='utf-8')
        print(f"✅ 问题推荐器已创建: {recommender_file}")

def main():
    """主函数"""
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    plan_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not plan_file:
        # 查找最新的计划文件
        plans_dir = Path(project_root) / "work_plans"
        if plans_dir.exists():
            plan_files = list(plans_dir.glob("project_analysis_*.json"))
            if plan_files:
                plan_file = max(plan_files, key=lambda x: x.stat().st_mtime)
    
    if not plan_file or not Path(plan_file).exists():
        print("❌ 未找到工作计划文件")
        return
    
    executor = AutoPlanExecutor(project_root)
    executor.execute_plan(plan_file)
    
    print("🎉 工作计划执行完成！")

if __name__ == "__main__":
    main()
