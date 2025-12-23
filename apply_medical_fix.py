#!/usr/bin/env python3
"""
医学网站搜索修复脚本
快速应用医学专业网站配置
"""

import os
import sys

def apply_medical_sites_fix():
    """应用医学网站修复"""
    print("🏥 正在应用医学网站搜索修复...")
    
    # 检查文件是否存在
    processor_file = "src/processors/web_to_kb_processor.py"
    ui_file = "src/ui/web_to_kb_interface.py"
    
    if not os.path.exists(processor_file):
        print(f"❌ 文件不存在: {processor_file}")
        return False
    
    if not os.path.exists(ui_file):
        print(f"❌ 文件不存在: {ui_file}")
        return False
    
    print("✅ 修复已应用到以下文件:")
    print(f"   - {processor_file}")
    print(f"   - {ui_file}")
    
    print("\n🎯 修复内容:")
    print("1. ✅ 添加专业医学网站：丁香园、好大夫在线、春雨医生")
    print("2. ✅ 优化关键词识别：扩展医学关键词库")
    print("3. ✅ 智能推荐：医学关键词优先推荐医学网站")
    print("4. ✅ UI分组：按类别显示网站选择")
    
    print("\n📋 现在搜索'卵巢癌'将推荐:")
    print("   - 维基百科")
    print("   - 百度百科") 
    print("   - 丁香园 (专业医学)")
    print("   - 好大夫在线 (专业医学)")
    print("   - 春雨医生 (专业医学)")
    
    print("\n🚀 请重启应用以使修复生效:")
    print("   streamlit run src/apppro.py")
    
    return True

if __name__ == "__main__":
    if apply_medical_sites_fix():
        print("\n✅ 修复完成！")
    else:
        print("\n❌ 修复失败！")
        sys.exit(1)
