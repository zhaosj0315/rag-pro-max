#!/usr/bin/env python3
"""
OCR优化测试脚本
测试多进程OCR的CPU利用率
"""

import multiprocessing as mp
import psutil
import time
from concurrent.futures import ProcessPoolExecutor

def test_cpu_detection():
    """测试CPU检测和进程数计算"""
    print("=== OCR优化测试 ===")
    
    # 获取系统信息
    cpu_count = mp.cpu_count()
    cpu_usage = psutil.cpu_percent(interval=1.0)
    memory = psutil.virtual_memory()
    
    print(f"💻 CPU核心数: {cpu_count}")
    print(f"💻 当前CPU使用率: {cpu_usage:.1f}%")
    print(f"💾 内存使用率: {memory.percent:.1f}%")
    
    # 模拟不同页数的进程数计算
    test_pages = [5, 20, 50, 100]
    
    for pages in test_pages:
        # 动态调整进程数：充分利用CPU资源
        if cpu_usage < 30:  # CPU空闲时使用更多进程
            max_workers = min(cpu_count, pages, 12)  # 最多12进程
        elif cpu_usage < 60:
            max_workers = min(cpu_count - 2, pages, 8)
        else:
            max_workers = min(cpu_count // 2, pages, 4)
        
        print(f"📄 {pages:3d}页 → 使用 {max_workers:2d} 进程 (CPU: {cpu_usage:.1f}%)")
    
    print("\n=== 优化建议 ===")
    if cpu_usage < 20:
        print("✅ CPU空闲，可以使用最大进程数进行OCR")
    elif cpu_usage < 50:
        print("⚡ CPU适中，使用中等进程数")
    else:
        print("⚠️  CPU繁忙，建议减少进程数或稍后处理")

def dummy_ocr_task(page_num):
    """模拟OCR处理时间（必须在模块级别）"""
    time.sleep(0.1)
    return f"Page {page_num} processed"

def simulate_ocr_workload():
    """模拟OCR工作负载"""
    print("\n=== 模拟OCR工作负载 ===")
    pages = list(range(1, 21))  # 20页
    
    baseline_time = None
    
    # 测试不同进程数的性能
    for workers in [1, 4, 8, 12]:
        if workers > mp.cpu_count():
            continue
            
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(dummy_ocr_task, pages))
        
        end_time = time.time()
        duration = end_time - start_time
        
        if baseline_time is None:
            baseline_time = duration
            speedup = 1.0
        else:
            speedup = baseline_time / duration
        
        print(f"🔄 {workers:2d}进程: {duration:.2f}秒 (加速比: {speedup:.1f}x)")

if __name__ == "__main__":
    test_cpu_detection()
    simulate_ocr_workload()
