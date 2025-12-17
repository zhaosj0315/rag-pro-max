#!/usr/bin/env python3
"""
公共工具函数 - 合并重复的基础工具函数
"""

import os
import gc
import psutil
import torch
import re
import time
from typing import Optional

def cleanup_memory():
    """统一的内存清理函数"""
    gc.collect()
    
    # CUDA 清理
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    # MPS 清理 (Apple Silicon)
    if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        torch.mps.empty_cache()

def sanitize_filename(filename: str) -> str:
    """统一的文件名清理函数"""
    # 移除或替换非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除多余的空格和点
    filename = re.sub(r'\s+', ' ', filename).strip()
    filename = filename.strip('.')
    # 限制长度
    if len(filename) > 200:
        filename = filename[:200]
    return filename or "unnamed"

def format_bytes(bytes_value: int) -> str:
    """统一的字节格式化函数"""
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(bytes_value)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"

def get_memory_stats() -> dict:
    """统一的内存统计函数"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        system_memory = psutil.virtual_memory()
        
        return {
            'process_memory': memory_info.rss,
            'process_memory_formatted': format_bytes(memory_info.rss),
            'system_total': system_memory.total,
            'system_available': system_memory.available,
            'system_used': system_memory.used,
            'system_percent': system_memory.percent,
            'system_total_formatted': format_bytes(system_memory.total),
            'system_available_formatted': format_bytes(system_memory.available),
            'system_used_formatted': format_bytes(system_memory.used)
        }
    except Exception:
        return {
            'process_memory': 0,
            'process_memory_formatted': '0 B',
            'system_total': 0,
            'system_available': 0,
            'system_used': 0,
            'system_percent': 0,
            'system_total_formatted': '0 B',
            'system_available_formatted': '0 B',
            'system_used_formatted': '0 B'
        }

def cleanup_temp_files(temp_dir: str = "temp_uploads", max_age_hours: int = 24) -> int:
    """统一的临时文件清理函数"""
    if not os.path.exists(temp_dir):
        return 0
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    cleaned_count = 0
    
    try:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        cleaned_count += 1
                except (OSError, IOError):
                    continue
            
            # 清理空目录
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                except (OSError, IOError):
                    continue
    except Exception:
        pass
    
    return cleaned_count

def get_file_stats(file_path: str) -> dict:
    """统一的文件统计函数"""
    try:
        stat = os.stat(file_path)
        return {
            'size': stat.st_size,
            'size_formatted': format_bytes(stat.st_size),
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'is_file': os.path.isfile(file_path),
            'is_dir': os.path.isdir(file_path),
            'exists': True
        }
    except (OSError, IOError):
        return {
            'size': 0,
            'size_formatted': '0 B',
            'modified': 0,
            'created': 0,
            'is_file': False,
            'is_dir': False,
            'exists': False
        }
