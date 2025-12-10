#!/usr/bin/env python3
"""
智能命名功能演示脚本
展示优化后的知识库命名算法效果
"""

import os
import tempfile
import shutil
from datetime import datetime
import re
from collections import Counter

def generate_smart_kb_name(target_path, cnt, file_types, folder_name):
    """智能生成知识库名称 - 优化版"""
    # 分析文件类型
    main_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
    if not main_types:
        return f"{folder_name}_{datetime.now().strftime('%m%d')}"
    
    main_ext = main_types[0][0].replace('.', '').upper()
    
    # 获取所有文件名（不含扩展名）
    all_files = []
    try:
        for f in os.listdir(target_path):
            if not f.startswith('.'):
                all_files.append(os.path.splitext(f)[0])
    except:
        pass
    
    # 策略1: 单文件 - 清理文件名
    if cnt == 1 and all_files:
        filename = all_files[0]
        clean_name = re.sub(r'[_\-\s]*(?:v?\d+[\.\d]*|20\d{2}[\-\d]*|final|draft|copy|backup|new|old|temp).*$', '', filename, flags=re.IGNORECASE)
        clean_name = re.sub(r'^[_\-\s]+|[_\-\s]+$', '', clean_name)
        if clean_name and len(clean_name) > 2:
            return clean_name[:20]
    
    # 策略2: 多文件 - 寻找共同前缀
    if len(all_files) > 1:
        common_prefix = os.path.commonprefix(all_files)
        clean_prefix = re.sub(r'[_\-\s\d]*$', '', common_prefix)
        if len(clean_prefix) >= 3:
            return clean_prefix[:15]
    
    # 策略3: 基于文件夹名
    if folder_name and folder_name not in ['temp_uploads', 'uploads', 'documents', 'files']:
        clean_folder = re.sub(r'[_\-\s]*(?:20\d{2}[\-\d]*|backup|copy|new|old|temp|v\d+).*$', '', folder_name, flags=re.IGNORECASE)
        clean_folder = re.sub(r'^[_\-\s]+|[_\-\s]+$', '', clean_folder)
        if clean_folder and len(clean_folder) >= 2:
            return clean_folder[:15]
    
    # 策略4: 分析高频词汇
    if all_files:
        words = []
        for filename in all_files:
            parts = re.split(r'[_\-\s\.\d]+', filename.lower())
            words.extend([w for w in parts if len(w) >= 3])
        
        if words:
            word_freq = Counter(words)
            stop_words = {
                'the', 'and', 'for', 'with', 'doc', 'file', 'new', 'old', 'temp', 'test', 'demo',
                'pdf', 'docx', 'txt', 'xlsx', 'ppt', 'html', 'json', 'csv', 'data', 'info'
            }
            meaningful_words = [
                (w, c) for w, c in word_freq.most_common(5) 
                if w not in stop_words and len(w) >= 3 and c >= 2
            ]
            if meaningful_words:
                return meaningful_words[0][0].capitalize()[:12]
    
    # 策略5: 基于文件类型
    type_names = {
        'PDF': '文档库', 'DOCX': '文档库', 'DOC': '文档库',
        'MD': '笔记本', 'TXT': '文本集',
        'PY': 'Python项目', 'JS': 'JS项目', 'JAVA': 'Java项目',
        'XLSX': '数据表', 'CSV': '数据集',
        'PPT': '演示文稿', 'PPTX': '演示文稿',
        'HTML': '网页集', 'JSON': '配置集'
    }
    
    base_name = type_names.get(main_ext, f"{main_ext}文件")
    date_suffix = datetime.now().strftime("%m%d")
    return f"{base_name}_{date_suffix}"

def demo_smart_naming():
    """演示智能命名功能"""
    print("🎯 RAG Pro Max - 智能命名功能演示")
    print("=" * 50)
    
    # 真实场景测试用例
    scenarios = [
        {
            'name': '📚 技术文档',
            'files': ['Python编程指南_v2.1_final.pdf', 'Django开发手册_2024.pdf'],
            'folder': 'tech_docs',
            'description': '技术文档集合'
        },
        {
            'name': '📊 项目报告',
            'files': ['项目报告_第一章.docx', '项目报告_第二章.docx', '项目报告_附录.docx'],
            'folder': 'project_reports',
            'description': '项目相关报告'
        },
        {
            'name': '💻 代码库',
            'files': ['main.py', 'utils.py', 'config.py', 'tests.py'],
            'folder': 'my_python_project',
            'description': 'Python项目代码'
        },
        {
            'name': '📈 数据分析',
            'files': ['sales_data_2024.xlsx', 'customer_analysis.csv'],
            'folder': 'analytics',
            'description': '业务数据文件'
        },
        {
            'name': '📝 会议记录',
            'files': ['会议记录_20241201.md', '会议记录_20241208.md'],
            'folder': 'meeting_notes',
            'description': '会议笔记'
        },
        {
            'name': '🎨 设计文档',
            'files': ['UI设计规范.pdf'],
            'folder': 'design_docs',
            'description': '单个设计文档'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['name']}")
        print(f"   描述: {scenario['description']}")
        print(f"   文件: {', '.join(scenario['files'][:2])}{'...' if len(scenario['files']) > 2 else ''}")
        print(f"   文件夹: {scenario['folder']}")
        
        # 创建临时测试环境
        temp_dir = tempfile.mkdtemp()
        try:
            # 创建测试文件
            for filename in scenario['files']:
                with open(os.path.join(temp_dir, filename), 'w', encoding='utf-8') as f:
                    f.write(f"这是 {filename} 的内容")
            
            # 计算文件类型分布
            file_types = {}
            for filename in scenario['files']:
                ext = os.path.splitext(filename)[1].lower()
                file_types[ext] = file_types.get(ext, 0) + 1
            
            # 生成智能名称
            smart_name = generate_smart_kb_name(
                temp_dir, 
                len(scenario['files']), 
                file_types, 
                scenario['folder']
            )
            
            print(f"   💡 智能命名: {smart_name}")
            
        finally:
            # 清理临时文件
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    print("\n" + "=" * 50)
    print("✨ 智能命名特性:")
    print("  • 单文件: 自动清理版本号、日期后缀")
    print("  • 多文件: 提取共同前缀作为主题")
    print("  • 文件夹: 使用有意义的文件夹名")
    print("  • 高频词: 分析文件名中的关键词")
    print("  • 类型名: 基于文件类型的默认命名")
    print("  • 防重名: 自动添加日期后缀")
    
    print("\n🎉 智能命名让知识库管理更轻松！")

if __name__ == "__main__":
    demo_smart_naming()
