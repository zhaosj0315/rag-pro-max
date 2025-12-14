#!/usr/bin/env python3
"""
实时处理日志查看器
"""

import sys
import os
import re
from datetime import datetime
from collections import defaultdict

def parse_ocr_logs(log_content):
    """解析OCR日志"""
    ocr_files = []
    total_pages = 0
    total_time = 0
    success_count = 0
    failed_count = 0
    
    lines = log_content.split('\n')
    current_file = {}
    
    for line in lines:
        # 检测OCR开始
        if "使用优化OCR处理器处理" in line:
            match = re.search(r'处理 (\d+) 页', line)
            if match:
                pages = int(match.group(1))
                current_file = {'pages': pages, 'start_time': datetime.now()}
                total_pages += pages
        
        # 检测OCR完成
        elif "OCR处理完成:" in line:
            match = re.search(r'(\d+\.?\d*)秒, (\d+\.?\d*)页/秒', line)
            if match:
                duration = float(match.group(1))
                speed = float(match.group(2))
                total_time += duration
                
                # 检查下一行是否有失败信息
                success = True
                if "⚠️  OCR未提取到文本内容" in line:
                    success = False
                    failed_count += 1
                else:
                    success_count += 1
                
                ocr_files.append({
                    'pages': current_file.get('pages', 0),
                    'duration': duration,
                    'speed': speed,
                    'success': success
                })
    
    return {
        'files': ocr_files,
        'total_files': len(ocr_files),
        'total_pages': total_pages,
        'total_time': total_time,
        'success_count': success_count,
        'failed_count': failed_count,
        'success_rate': (success_count / len(ocr_files) * 100) if ocr_files else 0,
        'avg_speed': total_pages / total_time if total_time > 0 else 0
    }

def parse_vector_logs(log_content):
    """解析向量化日志"""
    vector_info = {
        'total_nodes': 0,
        'batches': [],
        'current_progress': 0
    }
    
    lines = log_content.split('\n')
    
    for line in lines:
        # 解析总节点数
        if "解析文档片段" in line and "共" in line:
            match = re.search(r'共 (\d+) 个', line)
            if match:
                vector_info['total_nodes'] = int(match.group(1))
        
        # 解析向量化进度
        elif "Generating embeddings:" in line:
            # 提取进度信息
            if "%" in line:
                match = re.search(r'(\d+)%.*?(\d+)/(\d+)', line)
                if match:
                    progress = int(match.group(1))
                    current = int(match.group(2))
                    total = int(match.group(3))
                    
                    vector_info['batches'].append({
                        'progress': progress,
                        'current': current,
                        'total': total
                    })
                    vector_info['current_progress'] = progress
    
    return vector_info

def parse_timeline(log_content):
    """解析时间线"""
    timeline = []
    lines = log_content.split('\n')
    
    for line in lines:
        # 查找时间戳和步骤信息
        time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', line)
        if time_match:
            timestamp = time_match.group(1)
            
            # 查找步骤信息
            step_match = re.search(r'步骤 (\d+)/(\d+)', line)
            if step_match:
                current_step = int(step_match.group(1))
                total_steps = int(step_match.group(2))
                
                # 提取描述
                description = line.split(']', 2)[-1].strip() if ']' in line else line
                
                timeline.append({
                    'time': timestamp,
                    'step': current_step,
                    'total_steps': total_steps,
                    'description': description
                })
    
    return timeline

def print_summary_report(log_content):
    """打印汇总报告"""
    print("=" * 80)
    print("📊 RAG Pro Max 处理日志分析报告")
    print("=" * 80)
    
    # OCR分析
    ocr_stats = parse_ocr_logs(log_content)
    print(f"\n🔍 OCR处理统计:")
    print(f"   📄 总文件数: {ocr_stats['total_files']}")
    print(f"   📑 总页数: {ocr_stats['total_pages']:,}")
    print(f"   ✅ 成功文件: {ocr_stats['success_count']}")
    print(f"   ❌ 失败文件: {ocr_stats['failed_count']}")
    print(f"   📊 成功率: {ocr_stats['success_rate']:.1f}%")
    print(f"   ⏱️  总耗时: {ocr_stats['total_time']:.1f}秒 ({ocr_stats['total_time']/60:.1f}分钟)")
    print(f"   🚀 平均速度: {ocr_stats['avg_speed']:.1f}页/秒")
    
    # 向量化分析
    vector_stats = parse_vector_logs(log_content)
    print(f"\n🧠 向量化统计:")
    print(f"   📝 文档片段: {vector_stats['total_nodes']:,}")
    print(f"   📦 处理批次: {len(vector_stats['batches'])}")
    if vector_stats['batches']:
        last_batch = vector_stats['batches'][-1]
        print(f"   📈 当前进度: {last_batch['progress']}% ({last_batch['current']:,}/{last_batch['total']:,})")
    
    # 时间线分析
    timeline = parse_timeline(log_content)
    if timeline:
        print(f"\n⏰ 处理时间线:")
        for event in timeline:
            print(f"   [{event['time']}] 步骤{event['step']}/{event['total_steps']}: {event['description']}")
    
    # 性能分析
    print(f"\n📈 性能分析:")
    if ocr_stats['total_files'] > 0:
        avg_pages_per_file = ocr_stats['total_pages'] / ocr_stats['total_files']
        print(f"   📄 平均每文件页数: {avg_pages_per_file:.1f}页")
        
        if ocr_stats['success_count'] > 0:
            successful_files = [f for f in ocr_stats['files'] if f['success']]
            speeds = [f['speed'] for f in successful_files]
            if speeds:
                min_speed = min(speeds)
                max_speed = max(speeds)
                print(f"   🚀 速度范围: {min_speed:.1f} - {max_speed:.1f}页/秒")
    
    print("=" * 80)

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 从文件读取日志
        log_file = sys.argv[1]
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                log_content = f.read()
        else:
            print(f"❌ 日志文件不存在: {log_file}")
            return
    else:
        # 从标准输入读取日志
        print("📝 请粘贴日志内容，然后按 Ctrl+D (macOS/Linux) 或 Ctrl+Z (Windows) 结束:")
        log_content = sys.stdin.read()
    
    if log_content.strip():
        print_summary_report(log_content)
    else:
        print("❌ 没有检测到日志内容")

if __name__ == "__main__":
    main()
