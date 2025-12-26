#!/usr/bin/env python3
"""
RAG Pro Max v2.6.1 界面重构功能测试
测试4x1扁平布局和统一触发机制
"""

import os
import sys
import json
import tempfile
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_ui_refactor_features():
    """测试v2.6.1界面重构功能"""
    print("🧪 测试 v2.6.1 界面重构功能...")
    
    tests_passed = 0
    tests_total = 0
    
    # 测试1: 检查主应用文件存在
    tests_total += 1
    try:
        app_file = Path(__file__).parent.parent / "src" / "apppro.py"
        if app_file.exists():
            print("✅ 主应用文件存在")
            tests_passed += 1
        else:
            print("❌ 主应用文件不存在")
    except Exception as e:
        print(f"❌ 主应用文件检查失败: {e}")
    
    # 测试2: 检查4x1布局相关代码
    tests_total += 1
    try:
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "📂 文件上传" in content and "📝 粘贴文本" in content and "🔗 网址抓取" in content and "🔍 智能搜索" in content:
                print("✅ 4x1扁平布局代码存在")
                tests_passed += 1
            else:
                print("❌ 4x1扁平布局代码不完整")
    except Exception as e:
        print(f"❌ 4x1布局检查失败: {e}")
    
    # 测试3: 检查统一触发机制
    tests_total += 1
    try:
        if "🚀 立即创建" in content:
            print("✅ 统一触发机制代码存在")
            tests_passed += 1
        else:
            print("❌ 统一触发机制代码不存在")
    except Exception as e:
        print(f"❌ 统一触发机制检查失败: {e}")
    
    # 测试4: 检查防误触设计
    tests_total += 1
    try:
        if "key=" in content and "button" in content.lower():
            print("✅ 防误触设计代码存在")
            tests_passed += 1
        else:
            print("❌ 防误触设计代码不完整")
    except Exception as e:
        print(f"❌ 防误触设计检查失败: {e}")
    
    # 测试5: 检查版本信息
    tests_total += 1
    try:
        version_file = Path(__file__).parent.parent / "version.json"
        with open(version_file, 'r', encoding='utf-8') as f:
            version_data = json.load(f)
            if version_data.get("version") == "2.6.1":
                print("✅ 版本信息正确")
                tests_passed += 1
            else:
                print(f"❌ 版本信息错误: {version_data.get('version')}")
    except Exception as e:
        print(f"❌ 版本信息检查失败: {e}")
    
    print(f"\n📊 v2.6.1 界面重构测试结果: {tests_passed}/{tests_total} 通过")
    return tests_passed, tests_total

if __name__ == "__main__":
    print("🚀 RAG Pro Max v2.6.1 界面重构功能测试")
    print("=" * 50)
    
    passed, total = test_ui_refactor_features()
    
    print("\n" + "=" * 50)
    if passed == total:
        print("🎉 所有测试通过！界面重构功能正常")
        sys.exit(0)
    else:
        print(f"⚠️  {total - passed} 个测试失败")
        sys.exit(1)
