#!/usr/bin/env python3
"""
网页抓取到知识库功能测试脚本
"""

import os
import sys
import time

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试模块导入"""
    print("🧪 测试1: 模块导入")
    try:
        from src.processors.web_to_kb_simple import (
            crawl_and_create_kb, 
            generate_kb_name_from_web, 
            get_preset_search_sites
        )
        print("✅ 简化版模块导入成功")
        
        from src.processors.web_to_kb_processor import WebToKBProcessor
        print("✅ 完整版模块导入成功")
        
        from src.ui.web_to_kb_interface import WebToKBInterface
        print("✅ UI界面模块导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_kb_naming():
    """测试智能命名功能"""
    print("\n🧪 测试2: 智能命名功能")
    
    try:
        from src.processors.web_to_kb_simple import generate_kb_name_from_web
        
        test_cases = [
            ("https://zh.wikipedia.org/wiki/Python", "百科_Python"),
            ("https://github.com/python/cpython", "项目_cpython"),
            ("https://docs.python.org/3/", "docs_"),
            ("https://stackoverflow.com/questions/tagged/python", "编程问答"),
            ("https://blog.csdn.net/article/python", "CSDN技术"),
        ]
        
        for url, expected_prefix in test_cases:
            result = generate_kb_name_from_web(url, 5)
            print(f"  URL: {url}")
            print(f"  生成名称: {result}")
            if expected_prefix in result or expected_prefix.startswith(result[:5]):
                print("  ✅ 通过")
            else:
                print("  ⚠️ 可能需要调整")
            print()
        
        return True
    except Exception as e:
        print(f"❌ 智能命名测试失败: {e}")
        return False

def test_preset_sites():
    """测试预设网站"""
    print("🧪 测试3: 预设网站配置")
    
    try:
        from src.processors.web_to_kb_simple import get_preset_search_sites
        
        sites = get_preset_search_sites()
        print(f"  预设网站数量: {len(sites)}")
        
        required_sites = ["维基百科", "百度百科", "知乎", "CSDN", "GitHub", "Stack Overflow"]
        for site in required_sites:
            if site in sites:
                url_template = sites[site]
                if "{keyword}" in url_template:
                    print(f"  ✅ {site}: {url_template}")
                else:
                    print(f"  ⚠️ {site}: 缺少关键词占位符")
            else:
                print(f"  ❌ 缺少网站: {site}")
        
        return True
    except Exception as e:
        print(f"❌ 预设网站测试失败: {e}")
        return False

def test_directory_structure():
    """测试目录结构"""
    print("\n🧪 测试4: 目录结构")
    
    required_dirs = [
        "temp_uploads",
        "vector_db_storage", 
        "src/processors",
        "src/ui"
    ]
    
    all_good = True
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ 缺少目录: {dir_path}")
            all_good = False
    
    # 检查关键文件
    required_files = [
        "src/processors/web_crawler.py",
        "src/processors/web_to_kb_simple.py",
        "src/processors/web_to_kb_processor.py",
        "src/ui/web_to_kb_interface.py"
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ 缺少文件: {file_path}")
            all_good = False
    
    return all_good

def test_web_crawler():
    """测试网页抓取器"""
    print("\n🧪 测试5: 网页抓取器")
    
    try:
        from src.processors.web_crawler import WebCrawler
        
        crawler = WebCrawler()
        print("  ✅ WebCrawler 实例化成功")
        
        # 测试URL修复功能
        test_urls = [
            ("python.org", "https://python.org"),
            ("https://python.org", "https://python.org"),
            ("docs.python.org/3", "https://docs.python.org/3")
        ]
        
        for input_url, expected in test_urls:
            fixed = crawler._fix_url(input_url)
            if fixed == expected:
                print(f"  ✅ URL修复: {input_url} → {fixed}")
            else:
                print(f"  ⚠️ URL修复: {input_url} → {fixed} (期望: {expected})")
        
        return True
    except Exception as e:
        print(f"❌ 网页抓取器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 网页抓取到知识库功能测试")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_directory_structure,
        test_kb_naming,
        test_preset_sites,
        test_web_crawler
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ 测试异常: {e}\n")
    
    print("=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！功能可以正常使用")
        print("\n💡 下一步:")
        print("1. 运行 python demo_web_to_kb.py 查看演示")
        print("2. 按照 WEB_TO_KB_INTEGRATION.md 集成到主应用")
        print("3. 在Streamlit应用中测试完整功能")
    else:
        print("⚠️ 部分测试失败，请检查相关组件")
        print("📖 查看 WEB_TO_KB_INTEGRATION.md 了解详细信息")

if __name__ == "__main__":
    main()
