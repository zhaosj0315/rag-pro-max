#!/usr/bin/env python3
"""
阿里云文档爬虫测试 - 验证链接提取效果
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_aliyun_crawler():
    """测试阿里云文档爬虫"""
    print("🧪 测试阿里云文档爬虫...")
    
    try:
        from src.processors.web_crawler import WebCrawler
        import tempfile
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            crawler = WebCrawler(temp_dir)
            
            # 测试URL
            test_url = "https://help.aliyun.com/"
            
            print(f"📂 开始测试爬取: {test_url}")
            print("⚙️ 设置: 递归深度2, 每层50页")
            
            def status_callback(msg):
                print(f"  {msg}")
            
            # 执行爬取
            saved_files = crawler.crawl_advanced(
                start_url=test_url,
                max_depth=2,
                max_pages=50,  # 增加每层页数
                exclude_patterns=[],
                parser_type="documentation",
                status_callback=status_callback
            )
            
            print(f"\n📊 爬取结果:")
            print(f"  总页面数: {len(saved_files)}")
            
            # 分析保存的文件
            if saved_files:
                print(f"\n📄 保存的文件:")
                for i, file_path in enumerate(saved_files[:10]):  # 显示前10个
                    file_name = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    print(f"  {i+1}. {file_name} ({file_size} bytes)")
                
                if len(saved_files) > 10:
                    print(f"  ... 还有 {len(saved_files) - 10} 个文件")
            
            return len(saved_files)
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 0

def analyze_link_extraction():
    """分析链接提取效果"""
    print("\n🔍 分析链接提取效果...")
    
    try:
        import requests
        from bs4 import BeautifulSoup
        from src.processors.web_crawler import WebCrawler
        import tempfile
        
        # 获取阿里云首页
        url = "https://help.aliyun.com/"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 创建爬虫实例
        with tempfile.TemporaryDirectory() as temp_dir:
            crawler = WebCrawler(temp_dir)
            
            # 提取链接
            links = crawler._extract_links(soup, url)
            
            print(f"📊 链接提取统计:")
            print(f"  发现链接数: {len(links)}")
            
            # 分析链接类型
            doc_links = [l for l in links if any(k in l.lower() for k in ['doc', 'help', 'guide'])]
            product_links = [l for l in links if any(k in l.lower() for k in ['product', 'service'])]
            
            print(f"  文档类链接: {len(doc_links)}")
            print(f"  产品类链接: {len(product_links)}")
            
            # 显示前10个链接
            print(f"\n🔗 前10个链接:")
            for i, link in enumerate(links[:10]):
                print(f"  {i+1}. {link}")
            
            return len(links)
            
    except Exception as e:
        print(f"❌ 链接分析失败: {e}")
        return 0

def main():
    """主函数"""
    print("=" * 60)
    print("  阿里云文档爬虫测试")
    print("=" * 60)
    
    # 分析链接提取
    link_count = analyze_link_extraction()
    
    # 测试实际爬取
    if link_count > 0:
        print(f"\n✅ 链接提取正常，发现 {link_count} 个链接")
        
        # 询问是否进行实际爬取测试
        print("\n🤔 是否进行实际爬取测试？(这可能需要几分钟)")
        print("   输入 'y' 继续，其他键跳过...")
        
        # 由于这是自动化脚本，我们直接进行小规模测试
        print("🚀 进行小规模爬取测试...")
        page_count = test_aliyun_crawler()
        
        print(f"\n📊 最终结果:")
        print(f"  发现链接: {link_count} 个")
        print(f"  成功爬取: {page_count} 页")
        
        if page_count < 10:
            print("\n⚠️  爬取页面较少，可能的原因:")
            print("  1. 网站有反爬机制")
            print("  2. 链接过滤太严格")
            print("  3. 网络连接问题")
            print("  4. 需要增加每层页数限制")
        else:
            print(f"\n✅ 爬取效果良好！")
    else:
        print("❌ 链接提取失败，无法进行爬取测试")

if __name__ == "__main__":
    main()
