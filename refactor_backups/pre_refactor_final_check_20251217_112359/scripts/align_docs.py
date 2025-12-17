#!/usr/bin/env python3
"""
文档对齐脚本 - 按照代码结构整理所有文档材料
"""

import os
import shutil
from pathlib import Path

def align_documentation():
    """按照代码结构对齐所有文档"""
    
    base_dir = Path("/Users/zhaosj/Documents/rag-pro-max")
    docs_dir = base_dir / "docs"
    
    # 创建新的文档结构
    new_structure = {
        "core": ["STAGE14_REFACTOR_SUMMARY.md", "STAGE15_REFACTOR_SUMMARY.md", 
                "STAGE16_REFACTOR_SUMMARY.md", "STAGE17_FINAL_OPTIMIZATION.md",
                "MAIN_FILE_SIMPLIFICATION.md"],
        
        "features": ["V2.0_FEATURES.md", "V2.1_FEATURES.md", "V1.6_FEATURES.md", 
                    "V1.7_FEATURES.md"],
        
        "installation": ["INSTALLATION_V2.1.md", "INSTALLATION.md"],
        
        "performance": ["PERFORMANCE_GUIDE.md", "CPU_PROTECTION.md", 
                       "RESOURCE_OPTIMIZATION_GUIDE.md", "OCR_OPTIMIZATION.md"],
        
        "migration": ["MIGRATION_GUIDE_V2.2.md", "V1.7_MIGRATION_GUIDE.md", 
                     "MIGRATION_COMPLETE.md"],
        
        "troubleshooting": ["TROUBLESHOOTING.md", "HOTFIX_MAC_FREEZE.md", 
                           "CPU_PROTECTION_V2.md"],
        
        "testing": ["V2.2.1_FEASIBILITY_TEST.md", "V1.7_FEASIBILITY.md", 
                   "V1.6_FEASIBILITY.md"],
        
        "ui": ["UI_OPTIMIZATION_V2.2.1.md", "TABBED_SIDEBAR_DESIGN.md", 
               "TAB_MIGRATION_COMPLETE.md"],
        
        "releases": ["V2.1_CHANGELOG.md", "VERSION_COMPARISON.md", 
                    "FEATURE_COMPARISON_V2.2.md"]
    }
    
    print("🔄 开始对齐文档结构...")
    
    # 创建新的目录结构
    for category in new_structure.keys():
        category_dir = docs_dir / category
        category_dir.mkdir(exist_ok=True)
        print(f"📁 创建目录: {category}")
    
    # 移动文件到对应目录
    moved_count = 0
    for category, files in new_structure.items():
        for filename in files:
            src_file = docs_dir / filename
            dst_file = docs_dir / category / filename
            
            if src_file.exists():
                shutil.move(str(src_file), str(dst_file))
                print(f"📄 移动: {filename} -> {category}/")
                moved_count += 1
    
    # 更新文档索引
    create_docs_index(docs_dir, new_structure)
    
    print(f"✅ 完成！共移动 {moved_count} 个文档文件")
    print("📚 文档结构已按代码架构对齐")

def create_docs_index(docs_dir, structure):
    """创建文档索引"""
    
    index_content = """# 📚 文档索引 - 按代码结构对齐

## 🏗️ 核心架构文档
"""
    
    for category, files in structure.items():
        index_content += f"\n### 📁 {category.title()}\n"
        for filename in files:
            file_path = docs_dir / category / filename
            if file_path.exists():
                title = filename.replace('.md', '').replace('_', ' ')
                index_content += f"- [{title}]({category}/{filename})\n"
    
    # 写入索引文件
    index_file = docs_dir / "README.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print("📋 已创建文档索引: docs/README.md")

if __name__ == "__main__":
    align_documentation()
