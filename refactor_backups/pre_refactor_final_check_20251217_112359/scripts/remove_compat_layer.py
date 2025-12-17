#!/usr/bin/env python3
"""自动移除兼容层脚本"""

import re
import sys

def remove_compatibility_layer(file_path):
    """移除兼容层并替换调用"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. 替换函数调用
    replacements = [
        # 配置管理
        (r'\bload_config\(\)', 'ConfigLoader.load()'),
        (r'\bsave_config\(', 'ConfigLoader.save('),
        (r'\bload_manifest\(', 'ManifestManager.load('),
        (r'\bget_manifest_path\(', 'ManifestManager.get_path('),
        
        # 聊天管理
        (r'\bload_chat_history\(', 'HistoryManager.load('),
        (r'\bsave_chat_history\(', 'HistoryManager.save('),
        (r'\bclear_chat_history\(', 'HistoryManager.clear('),
        
        # 知识库管理 - 需要特殊处理
        (r'\bget_existing_kbs\(([^)]+)\)', r'kb_manager.list_all()  # base_path: \1'),
        (r'\bauto_save_kb_info\(([^,]+),\s*([^)]+)\)', 
         r'kb_manager.save_info(os.path.basename(\1), \2, 0)'),
        (r'\bget_kb_info\(([^)]+)\)', 
         r'kb_manager.get_info(os.path.basename(\1))'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # 2. 移除兼容层函数定义
    # 找到兼容层开始和结束位置
    compat_start = content.find('# 引入配置管理（新接口）')
    if compat_start == -1:
        compat_start = content.find('# 引入配置管理')
    
    rag_engine_import = content.find('# 引入 RAG 引擎')
    
    if compat_start != -1 and rag_engine_import != -1:
        # 保留导入，删除兼容函数
        before = content[:compat_start]
        after = content[rag_engine_import:]
        
        # 重新构建导入部分
        new_imports = """# 引入配置管理
from src.config import ConfigLoader, ManifestManager

# 引入聊天管理
from src.chat import HistoryManager, SuggestionManager

# 引入知识库管理
from src.kb import KBManager
kb_manager = KBManager()

"""
        content = before + new_imports + after
    
    # 3. 处理 get_existing_kbs 的特殊情况
    # 需要在调用前设置 base_path
    content = re.sub(
        r'kb_manager\.list_all\(\)\s*#\s*base_path:\s*([^\n]+)',
        r'kb_manager.base_path = \1\n    existing_kbs = kb_manager.list_all()',
        content
    )
    
    # 4. 处理 rename_kb
    content = re.sub(
        r'rename_kb\(([^,]+),\s*([^,]+),\s*([^)]+)\)',
        r'kb_manager.base_path = \3; success, msg = kb_manager.rename(\1, \2); success',
        content
    )
    
    # 5. 处理 delete_kb
    content = re.sub(
        r'delete_kb\(([^,]+),\s*([^)]+)\)',
        r'kb_manager.base_path = \2; success, msg = kb_manager.delete(\1); success',
        content
    )
    
    if content != original_content:
        # 备份原文件
        with open(file_path + '.v142', 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # 写入新内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新: {file_path}")
        print(f"📦 备份: {file_path}.v142")
        return True
    else:
        print(f"ℹ️  无需更新: {file_path}")
        return False

if __name__ == "__main__":
    file_path = "src/apppro.py"
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    
    try:
        if remove_compatibility_layer(file_path):
            print("\n✅ 兼容层移除完成")
            print("⚠️  请运行测试验证: python3 tests/factory_test.py")
        else:
            print("\n⚠️  未检测到兼容层")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
