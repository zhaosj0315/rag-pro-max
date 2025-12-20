#!/usr/bin/env python3
"""
RAG Pro Max 修复验证脚本
验证最新的4个修复是否正确实现
"""

import re
from pathlib import Path

def verify_fixes():
    """验证修复"""
    apppro_path = Path("src/apppro.py")
    
    if not apppro_path.exists():
        print("❌ src/apppro.py 文件不存在")
        return False
    
    with open(apppro_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fixes_status = {}
    
    # 1. 验证追问建议按钮使用稳定key
    stable_key_pattern = r'sug_btn_stable_\{idx\}'
    if re.search(stable_key_pattern, content):
        fixes_status["追问建议稳定key"] = "✅ 已修复"
    else:
        fixes_status["追问建议稳定key"] = "❌ 未修复"
    
    # 2. 验证侧边栏过滤框已删除
    filter_comment = "知识库搜索/过滤已按用户要求移除"
    if filter_comment in content:
        fixes_status["侧边栏过滤框删除"] = "✅ 已删除"
    else:
        fixes_status["侧边栏过滤框删除"] = "❌ 未删除"
    
    # 3. 验证智能行业搜索关键词功能
    search_keyword_pattern = r'search_keyword = st\.text_input.*关键词'
    if re.search(search_keyword_pattern, content):
        fixes_status["智能行业搜索关键词"] = "✅ 已恢复"
    else:
        fixes_status["智能行业搜索关键词"] = "❌ 未恢复"
    
    # 4. 验证智能行业搜索模式存在
    search_mode_pattern = r'智能行业搜索'
    if re.search(search_mode_pattern, content):
        fixes_status["智能行业搜索模式"] = "✅ 功能完整"
    else:
        fixes_status["智能行业搜索模式"] = "❌ 功能缺失"
    
    return fixes_status

def main():
    print("🔍 RAG Pro Max 修复验证")
    print("=" * 40)
    
    fixes = verify_fixes()
    
    all_good = True
    for fix_name, status in fixes.items():
        print(f"{status} {fix_name}")
        if "❌" in status:
            all_good = False
    
    print("\n" + "=" * 40)
    if all_good:
        print("🎉 所有修复验证通过！可以推送到GitHub")
        return True
    else:
        print("⚠️  发现问题，请检查修复")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
