#!/usr/bin/env python3
"""查看网页爬取日志工具"""

import os
import json
import argparse
from datetime import datetime, timedelta


def view_crawl_logs(date=None, keyword=None):
    """查看爬取日志"""
    log_dir = "app_logs"
    
    if not os.path.exists(log_dir):
        print("❌ 日志目录不存在")
        return
    
    # 确定日志文件
    if date:
        log_file = f"log_{date}.jsonl"
    else:
        # 使用今天的日志
        today = datetime.now().strftime('%Y%m%d')
        log_file = f"log_{today}.jsonl"
    
    log_path = os.path.join(log_dir, log_file)
    
    if not os.path.exists(log_path):
        print(f"❌ 日志文件不存在: {log_path}")
        return
    
    print(f"📋 查看爬取日志: {log_file}")
    print("=" * 60)
    
    crawl_logs = []
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    message = log_entry.get('message', '')
                    
                    # 筛选爬取相关日志
                    if any(keyword in message for keyword in ['🌐 网页爬取', '🔍 关键词搜索', '🌐 开始网页爬取', '🔍 开始关键词搜索']):
                        if keyword is None or keyword.lower() in message.lower():
                            crawl_logs.append(log_entry)
                except json.JSONDecodeError:
                    continue
    
    except Exception as e:
        print(f"❌ 读取日志失败: {e}")
        return
    
    if not crawl_logs:
        print("📝 没有找到爬取相关的日志")
        return
    
    print(f"📊 找到 {len(crawl_logs)} 条爬取日志:")
    print()
    
    current_session = None
    
    for log in crawl_logs:
        timestamp = log.get('timestamp', '')
        level = log.get('level', 'INFO')
        message = log.get('message', '')
        
        # 格式化时间
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%H:%M:%S')
        except:
            time_str = timestamp
        
        # 检测新的爬取会话
        if '开始网页爬取' in message or '开始关键词搜索' in message:
            if current_session:
                print()  # 分隔不同会话
            current_session = message
            print(f"🚀 [{time_str}] {message}")
        elif '爬取完成' in message or '搜索完成' in message:
            print(f"✅ [{time_str}] {message}")
            current_session = None
        else:
            # 缩进显示详细日志
            print(f"   [{time_str}] {message}")
    
    print()
    print("=" * 60)
    print(f"📈 统计: 共 {len(crawl_logs)} 条爬取日志")


def main():
    parser = argparse.ArgumentParser(description='查看网页爬取日志')
    parser.add_argument('--date', help='指定日期 (格式: 20241214)')
    parser.add_argument('--keyword', help='关键词筛选')
    
    args = parser.parse_args()
    
    view_crawl_logs(args.date, args.keyword)


if __name__ == "__main__":
    main()
