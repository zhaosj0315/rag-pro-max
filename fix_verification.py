#!/usr/bin/env python3
"""
快速修复验证脚本
验证 HistoryManager 导入修复是否成功
"""

import sys
import os
sys.path.append('src')

def verify_imports():
    """验证关键导入"""
    print("🔍 验证关键模块导入...")
    
    imports_to_test = [
        ("src.chat", "HistoryManager"),
        ("src.chat.unified_suggestion_engine", "get_unified_suggestion_engine"),
        ("src.config", "ConfigLoader"),
        ("src.app_logging", "LogManager"),
    ]
    
    all_success = True
    
    for module, item in imports_to_test:
        try:
            exec(f"from {module} import {item}")
            print(f"✅ {module}.{item}")
        except Exception as e:
            print(f"❌ {module}.{item}: {e}")
            all_success = False
    
    return all_success

def verify_syntax():
    """验证语法"""
    print("\n🔍 验证应用语法...")
    
    try:
        import py_compile
        py_compile.compile('src/apppro.py', doraise=True)
        print("✅ src/apppro.py 语法正确")
        return True
    except Exception as e:
        print(f"❌ src/apppro.py 语法错误: {e}")
        return False

def verify_historymanager_usage():
    """验证 HistoryManager 使用"""
    print("\n🔍 验证 HistoryManager 功能...")
    
    try:
        from src.chat import HistoryManager
        
        # 测试基本方法
        methods = ['load', 'save', 'clear', 'exists']
        for method in methods:
            if hasattr(HistoryManager, method):
                print(f"✅ HistoryManager.{method} 存在")
            else:
                print(f"❌ HistoryManager.{method} 不存在")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ HistoryManager 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 RAG Pro Max 导入修复验证")
    print("=" * 50)
    
    # 执行验证
    imports_ok = verify_imports()
    syntax_ok = verify_syntax()
    history_ok = verify_historymanager_usage()
    
    # 总结
    print("\n📊 验证结果:")
    print(f"   导入测试: {'✅ 通过' if imports_ok else '❌ 失败'}")
    print(f"   语法检查: {'✅ 通过' if syntax_ok else '❌ 失败'}")
    print(f"   功能验证: {'✅ 通过' if history_ok else '❌ 失败'}")
    
    all_ok = imports_ok and syntax_ok and history_ok
    
    if all_ok:
        print("\n🎉 修复验证通过！应用可以正常启动")
        print("💡 可以运行: streamlit run src/apppro.py")
    else:
        print("\n⚠️ 发现问题，需要进一步修复")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
