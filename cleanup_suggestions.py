#!/usr/bin/env python3
"""
清理重复的推荐问题系统
统一使用 UnifiedSuggestionEngine
"""

import os
import shutil

def cleanup_old_suggestion_systems():
    """清理旧的推荐系统"""
    print("🧹 清理重复的推荐问题系统...")
    
    # 要移除的文件列表
    files_to_remove = [
        "src/chat/web_suggestion_engine.py",
        "src/chat/suggestion_engine.py", 
        "src/ui/suggestion_panel.py",
        "src/chat/suggestion_manager_old.py"
    ]
    
    # 移除文件
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ 已删除: {file_path}")
            except Exception as e:
                print(f"❌ 删除失败 {file_path}: {e}")
        else:
            print(f"⚠️ 文件不存在: {file_path}")
    
    # 移除备份目录中的重复文件
    backup_dirs = [
        "backups/backup_20251220_075210/src/chat/",
        "backups/backup_20251220_074956/src/chat/"
    ]
    
    for backup_dir in backup_dirs:
        web_engine_file = os.path.join(backup_dir, "web_suggestion_engine.py")
        if os.path.exists(web_engine_file):
            try:
                os.remove(web_engine_file)
                print(f"✅ 已删除备份: {web_engine_file}")
            except Exception as e:
                print(f"❌ 删除备份失败 {web_engine_file}: {e}")
    
    print("\n📊 统一后的推荐系统架构:")
    print("├── src/chat/unified_suggestion_engine.py  # 🎯 统一推荐引擎")
    print("├── src/chat/suggestion_manager.py         # 🔄 适配器 (兼容旧接口)")
    print("└── src/processors/web_to_kb_processor.py  # 🌐 网页处理器 (使用统一引擎)")
    
    print("\n✅ 清理完成！现在所有推荐问题都使用统一的 UnifiedSuggestionEngine")

def verify_unified_system():
    """验证统一系统"""
    print("\n🔍 验证统一推荐系统...")
    
    try:
        from src.chat.unified_suggestion_engine import get_unified_suggestion_engine
        
        # 测试统一引擎
        engine = get_unified_suggestion_engine("test_cleanup")
        
        # 测试不同场景
        scenarios = [
            ("chat", "这是一个测试方案"),
            ("web_crawl", "Python编程教程"),
            ("file_upload", "研究报告分析")
        ]
        
        for source_type, context in scenarios:
            suggestions = engine.generate_suggestions(
                context=context,
                source_type=source_type,
                num_questions=2
            )
            print(f"✅ {source_type:12} 场景: 生成 {len(suggestions)} 个问题")
        
        print("✅ 统一推荐系统验证通过！")
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    cleanup_old_suggestion_systems()
    verify_unified_system()
