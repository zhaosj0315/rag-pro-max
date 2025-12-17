#!/usr/bin/env python3
"""
实时爬虫监控
显示当前正在爬取的URL和进度
"""

import os
import time
import json
from pathlib import Path
from datetime import datetime

def monitor_crawl_progress():
    """监控爬取进度"""
    print("🔍 RAG Pro Max 爬虫监控")
    print("=" * 50)
    
    # 监控临时文件夹
    temp_dir = Path("temp_uploads")
    
    while True:
        try:
            # 查找最新的爬取会话
            crawl_dirs = []
            if temp_dir.exists():
                for item in temp_dir.iterdir():
                    if item.is_dir() and item.name.startswith("Search_"):
                        crawl_dirs.append(item)
            
            if not crawl_dirs:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 等待爬取任务...")
                time.sleep(2)
                continue
            
            # 获取最新的爬取目录
            latest_dir = max(crawl_dirs, key=lambda x: x.stat().st_mtime)
            
            # 统计文件数量
            files = list(latest_dir.glob("*.txt"))
            file_count = len(files)
            
            # 获取最新文件
            if files:
                latest_file = max(files, key=lambda x: x.stat().st_mtime)
                latest_time = datetime.fromtimestamp(latest_file.stat().st_mtime)
                
                # 尝试读取文件内容获取URL信息
                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # 提取URL（假设文件开头有URL信息）
                    lines = content.split('\n')
                    url_info = "未知URL"
                    for line in lines[:5]:  # 检查前5行
                        if 'http' in line:
                            url_info = line.strip()
                            break
                    
                    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] 📁 {latest_dir.name} | 📄 {file_count} 个文件 | 🔗 最新: {url_info[:80]}...", end="")
                    
                except Exception:
                    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] 📁 {latest_dir.name} | 📄 {file_count} 个文件 | ⏰ {latest_time.strftime('%H:%M:%S')}", end="")
            else:
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] 📁 {latest_dir.name} | 📄 0 个文件 | 🔍 准备中...", end="")
            
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n👋 监控已停止")
            break
        except Exception as e:
            print(f"\n❌ 监控错误: {e}")
            time.sleep(2)

def show_crawl_stats():
    """显示爬取统计"""
    print("\n📊 爬取统计信息")
    print("-" * 30)
    
    # 检查爬取统计文件
    stats_file = Path("app_logs/crawl_stats.json")
    if stats_file.exists():
        try:
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)
            
            if stats:
                latest_session = stats[-1]
                print(f"📅 最新会话: {latest_session.get('session_id', 'N/A')}")
                print(f"🕐 开始时间: {latest_session.get('start_time', 'N/A')}")
                print(f"📄 总URL数: {latest_session.get('total_urls', 0)}")
                print(f"✅ 成功: {latest_session.get('successful_urls', 0)}")
                print(f"❌ 失败: {latest_session.get('failed_urls', 0)}")
                print(f"📊 成功率: {latest_session.get('total_urls', 0) and (latest_session.get('successful_urls', 0) / latest_session.get('total_urls', 1) * 100):.1f}%")
            else:
                print("📄 暂无统计数据")
                
        except Exception as e:
            print(f"❌ 读取统计失败: {e}")
    else:
        print("📄 统计文件不存在")

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        show_crawl_stats()
    else:
        try:
            monitor_crawl_progress()
        except KeyboardInterrupt:
            print("\n👋 再见！")

if __name__ == "__main__":
    main()
