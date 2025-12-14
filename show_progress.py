#!/usr/bin/env python3
"""
实时进度显示工具 - 简化版
"""

import re
import sys
from datetime import datetime

def analyze_log_simple(log_text):
    """简化日志分析"""
    lines = log_text.strip().split('\n')
    
    # OCR统计
    ocr_files = 0
    ocr_pages = 0
    ocr_time = 0
    ocr_failed = 0
    
    # 向量化统计  
    vector_nodes = 0
    vector_progress = 0
    
    # 时间线
    steps = []
    
    for line in lines:
        # OCR处理
        if "使用优化OCR处理器处理" in line:
            match = re.search(r'(\d+) 页', line)
            if match:
                ocr_files += 1
                ocr_pages += int(match.group(1))
        
        elif "OCR处理完成:" in line:
            match = re.search(r'(\d+\.?\d*)秒', line)
            if match:
                ocr_time += float(match.group(1))
            if "⚠️  OCR未提取到文本内容" in line:
                ocr_failed += 1
        
        # 向量化
        elif "解析文档片段" in line and "共" in line:
            match = re.search(r'共 (\d+) 个', line)
            if match:
                vector_nodes = int(match.group(1))
        
        elif "Generating embeddings:" in line and "%" in line:
            match = re.search(r'(\d+)%', line)
            if match:
                vector_progress = max(vector_progress, int(match.group(1)))
        
        # 步骤时间线
        elif re.search(r'\[\d{2}:\d{2}:\d{2}\].*步骤', line):
            time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', line)
            step_match = re.search(r'步骤 (\d+)/(\d+)', line)
            if time_match and step_match:
                steps.append({
                    'time': time_match.group(1),
                    'step': f"{step_match.group(1)}/{step_match.group(2)}"
                })
    
    return {
        'ocr': {
            'files': ocr_files,
            'pages': ocr_pages,
            'time_min': ocr_time / 60,
            'failed': ocr_failed,
            'success_rate': ((ocr_files - ocr_failed) / ocr_files * 100) if ocr_files > 0 else 0,
            'speed': ocr_pages / ocr_time if ocr_time > 0 else 0
        },
        'vector': {
            'nodes': vector_nodes,
            'progress': vector_progress
        },
        'steps': steps
    }

def print_quick_summary(stats):
    """打印快速摘要"""
    print("🚀 RAG Pro Max 处理进度")
    print("=" * 40)
    
    # OCR摘要
    ocr = stats['ocr']
    if ocr['files'] > 0:
        print(f"🔍 OCR: {ocr['files']}文件, {ocr['pages']:,}页")
        print(f"   ✅ 成功率: {ocr['success_rate']:.0f}%")
        print(f"   ⏱️  耗时: {ocr['time_min']:.1f}分钟")
        print(f"   🚀 速度: {ocr['speed']:.1f}页/秒")
    
    # 向量化摘要
    vector = stats['vector']
    if vector['nodes'] > 0:
        print(f"🧠 向量化: {vector['nodes']:,}片段")
        print(f"   📈 进度: {vector['progress']}%")
    
    # 时间线
    if stats['steps']:
        print(f"⏰ 最新步骤:")
        for step in stats['steps'][-2:]:  # 显示最后2个步骤
            print(f"   [{step['time']}] 步骤{step['step']}")
    
    print("=" * 40)

if __name__ == "__main__":
    # 从用户提供的日志中分析
    sample_log = """
🔍 检测到扫描版PDF，启用增强OCR处理...
📊 使用优化OCR处理器处理 4 页
✅ OCR处理完成: 3.1秒, 1.3页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 122 页
✅ OCR处理完成: 307.3秒, 2.8页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 39 页
✅ OCR处理完成: 205.7秒, 2.8页/秒
⚠️  OCR未提取到文本内容
📊 使用优化OCR处理器处理 221 页
✅ OCR处理完成: 205.7秒, 2.8页/秒
⚠️  OCR未提取到文本内容
ℹ️ [06:39:40] 📂 [步骤 4/6] 构建文件清单
ℹ️ [06:39:40] 📂 [步骤 5/6] 解析文档片段 (共 27940 个)
ℹ️ [06:39:53] 📂 [步骤 6/6] 向量化和索引构建
Generating embeddings: 100%|##########| 2048/2048 [01:32<00:00, 22.17it/s]
Generating embeddings: 44%|####3     | 900/2048 [00:41<00:51, 22.34it/s]
"""
    
    stats = analyze_log_simple(sample_log)
    print_quick_summary(stats)
