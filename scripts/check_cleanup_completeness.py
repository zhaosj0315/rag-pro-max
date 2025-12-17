#!/usr/bin/env python3
"""
RAG Pro Max - 开发材料清理完整性检查
检查是否还有未清理的开发过程材料
"""

import os
import glob
from pathlib import Path

def check_cleanup():
    """检查开发材料清理完整性"""
    print("🔍 RAG Pro Max 清理完整性检查")
    print("=" * 35)
    
    # 应该被删除的文件/目录模式
    cleanup_patterns = [
        # 内部开发文档
        "PRODUCTION_RELEASE_STANDARD.md",
        "RELEASE_CHECKLIST.md", 
        "PROJECT_STRUCTURE_V*.md",
        "DOCUMENTATION_STRATEGY.md",
        "REFACTOR_PROGRESS_RECORD.md",
        "PHASE_*.md",
        
        # 开发工具
        "tools/",
        "rag",
        "kbllama", 
        "view_crawl_logs.py",
        
        # 版本历史文档
        "docs/",
        
        # 测试数据
        "exports/",
        "test_*_output/",
        "refactor_backups/",
        "PRODUCTION_RELEASE_REPORT_*.md",
        "*_test_*.txt",
        "*_test_*.json",
        
        # 技术细节文档
        "UX_IMPROVEMENTS.md",
        "BM25.md", 
        "RERANK.md",
        "OCR_LOGGING_SYSTEM.md",
        "RESOURCE_PROTECTION_V2.md",
        
        # 备份和临时文件
        "*_backup.py",
        "*_old.py",
        "*.pre-migration",
        "crawler_state*.json",
        "*.tmp",
        "*.temp",
        ".DS_Store"
    ]
    
    found_items = []
    
    # 检查每个模式
    for pattern in cleanup_patterns:
        matches = glob.glob(pattern)
        if matches:
            found_items.extend(matches)
    
    # 报告结果
    if found_items:
        print("❌ 发现未清理的开发材料:")
        for item in sorted(found_items):
            item_type = "目录" if os.path.isdir(item) else "文件"
            print(f"   - {item} ({item_type})")
        
        print(f"\n📊 统计: 发现 {len(found_items)} 个未清理项目")
        print("\n🔧 建议:")
        print("   1. 运行清理脚本: ./scripts/cleanup_development_materials.sh")
        print("   2. 手动删除剩余项目")
        print("   3. 重新运行此检查")
        
        return False
    else:
        print("✅ 开发材料清理完整")
        
        # 统计保留的核心文件
        core_files = {
            "Python文件": len(glob.glob("**/*.py", recursive=True)),
            "配置文件": len(glob.glob("**/*.json", recursive=True)),
            "文档文件": len(glob.glob("*.md")),
            "脚本文件": len(glob.glob("scripts/*.sh")) + len(glob.glob("scripts/*.py"))
        }
        
        print("\n📊 保留的核心文件:")
        for file_type, count in core_files.items():
            print(f"   - {file_type}: {count}个")
        
        print("\n🎯 项目状态: 精简专业，专注核心功能！")
        return True

def check_essential_files():
    """检查必需文件是否完整"""
    print("\n🔍 检查必需文件完整性...")
    
    essential_files = [
        "README.md",
        "CHANGELOG.md", 
        "requirements.txt",
        "version.json",
        "src/apppro.py"
    ]
    
    missing_files = []
    for file_path in essential_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少必需文件:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    else:
        print("✅ 必需文件完整")
        return True

def main():
    """主检查函数"""
    os.chdir(Path(__file__).parent.parent)
    
    cleanup_ok = check_cleanup()
    essential_ok = check_essential_files()
    
    print("\n" + "=" * 35)
    if cleanup_ok and essential_ok:
        print("🎉 清理检查全部通过！")
        print("📦 项目已准备好发布")
        return 0
    else:
        print("⚠️  清理检查未通过")
        print("🔧 请按建议修复后重试")
        return 1

if __name__ == "__main__":
    exit(main())
