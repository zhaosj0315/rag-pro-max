#!/usr/bin/env python3
"""
网页抓取到知识库功能演示脚本
演示如何从网页内容直接创建知识库
"""

import os
import sys
import time

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.processors.web_to_kb_simple import crawl_and_create_kb, get_preset_search_sites


def demo_direct_crawl():
    """演示直接URL抓取"""
    print("🌐 演示1: 直接URL抓取")
    print("=" * 50)
    
    # 测试URL
    test_url = "https://docs.python.org/3/tutorial/"
    
    def status_callback(message):
        print(f"📡 {message}")
    
    print(f"正在抓取: {test_url}")
    
    result = crawl_and_create_kb(
        url=test_url,
        max_depth=2,
        max_pages=5,
        status_callback=status_callback
    )
    
    if result["success"]:
        print(f"\n✅ {result['message']}")
        print(f"📚 知识库名称: {result['kb_name']}")
        print(f"📄 抓取页面数: {result['files_count']}")
        print(f"📁 文件位置: {result['crawler_output_dir']}")
        
        # 显示抓取的文件
        print("\n📋 抓取的文件:")
        for i, file_path in enumerate(result['files'][:3], 1):
            filename = os.path.basename(file_path)
            print(f"  {i}. {filename}")
        if len(result['files']) > 3:
            print(f"  ... 还有 {len(result['files']) - 3} 个文件")
    else:
        print(f"❌ {result['message']}")
    
    print()


def demo_keyword_search():
    """演示关键词搜索"""
    print("🔍 演示2: 关键词搜索")
    print("=" * 50)
    
    keyword = "Python编程"
    sites = ["维基百科", "百度百科"]
    
    def status_callback(message):
        print(f"🔍 {message}")
    
    print(f"搜索关键词: {keyword}")
    print(f"搜索网站: {', '.join(sites)}")
    
    result = crawl_and_create_kb(
        keyword=keyword,
        sites=sites,
        max_pages=8,
        status_callback=status_callback
    )
    
    if result["success"]:
        print(f"\n✅ {result['message']}")
        print(f"📚 知识库名称: {result['kb_name']}")
        print(f"📄 抓取页面数: {result['files_count']}")
        
        # 显示抓取的文件
        print("\n📋 抓取的文件:")
        for i, file_path in enumerate(result['files'][:3], 1):
            filename = os.path.basename(file_path)
            print(f"  {i}. {filename}")
        if len(result['files']) > 3:
            print(f"  ... 还有 {len(result['files']) - 3} 个文件")
    else:
        print(f"❌ {result['message']}")
    
    print()


def show_preset_sites():
    """显示预设网站"""
    print("🌍 预设搜索网站")
    print("=" * 50)
    
    sites = get_preset_search_sites()
    for i, (name, url_template) in enumerate(sites.items(), 1):
        print(f"{i}. {name}")
        print(f"   模板: {url_template}")
        print()


def main():
    """主函数"""
    print("🚀 网页抓取到知识库功能演示")
    print("=" * 60)
    print()
    
    # 检查必要目录
    required_dirs = ["temp_uploads", "vector_db_storage"]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"📁 创建目录: {dir_name}")
    
    print()
    
    # 显示预设网站
    show_preset_sites()
    
    # 演示功能
    try:
        # 演示1: 直接抓取（使用简单的测试URL）
        print("开始演示...")
        time.sleep(2)
        
        # 使用一个简单的测试URL
        test_url = "https://httpbin.org/html"  # 简单的HTML测试页面
        
        def status_callback(message):
            print(f"📡 {message}")
        
        print("🌐 测试直接URL抓取...")
        result = crawl_and_create_kb(
            url=test_url,
            max_depth=1,
            max_pages=1,
            kb_name="测试知识库",
            status_callback=status_callback
        )
        
        if result["success"]:
            print(f"✅ 测试成功！")
            print(f"📚 知识库: {result['kb_name']}")
            print(f"📄 文件数: {result['files_count']}")
        else:
            print(f"❌ 测试失败: {result['message']}")
        
        print("\n" + "=" * 60)
        print("🎉 演示完成！")
        print()
        print("💡 使用方法:")
        print("1. 在Streamlit应用中，选择'🌐 网页抓取'标签页")
        print("2. 输入网址或关键词")
        print("3. 点击'抓取并创建知识库'")
        print("4. 系统会自动创建知识库并切换到该知识库")
        print("5. 现在可以开始与知识库对话了！")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        print("请检查网络连接和依赖包是否正确安装")


if __name__ == "__main__":
    main()
