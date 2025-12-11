#!/usr/bin/env python3
"""
直接OCR性能测试
模拟真实OCR工作负载
"""

import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import time
import os

def simulate_ocr_task(page_info):
    """模拟OCR任务（CPU密集型）"""
    page_num, complexity = page_info
    
    # 模拟OCR的CPU密集计算
    total = 0
    iterations = complexity * 50000  # 根据复杂度调整计算量
    
    for i in range(iterations):
        total += (i * i) % 1000
        if i % 10000 == 0:
            # 模拟OCR的I/O操作
            time.sleep(0.001)
    
    return page_num, f"OCR结果_{total % 1000}"

def test_ocr_performance():
    """测试OCR性能"""
    print("🔍 OCR性能测试开始...")
    
    # 模拟不同复杂度的页面
    pages = []
    for i in range(50):  # 50页文档
        complexity = 10 + (i % 5)  # 复杂度10-14
        pages.append((i+1, complexity))
    
    print(f"📄 模拟处理 {len(pages)} 页文档")
    
    # 测试不同进程数的性能
    for workers in [1, 4, 8, 12, 14]:
        print(f"\n🔄 测试 {workers} 进程:")
        
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(simulate_ocr_task, pages))
        
        end_time = time.time()
        duration = end_time - start_time
        pages_per_sec = len(pages) / duration
        
        print(f"   ⏱️  耗时: {duration:.2f}秒")
        print(f"   📊 速度: {pages_per_sec:.1f}页/秒")
        print(f"   💻 理论CPU使用率: {min(workers/14*100, 100):.0f}%")

def test_real_multiprocessing():
    """测试真实的多进程调度"""
    print("\n🚀 真实多进程调度测试...")
    
    def heavy_computation(n):
        """重计算任务"""
        result = 0
        for i in range(n * 200000):
            result += (i * i * i) % 1000
        return result
    
    # 创建足够多的任务来占满所有CPU
    tasks = [100] * 28  # 28个任务，每个CPU核心2个
    
    print(f"💪 启动 14 进程处理 {len(tasks)} 个重计算任务")
    print("📊 监控CPU使用率，应该能看到所有核心都被激活")
    
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=14) as executor:
        results = list(executor.map(heavy_computation, tasks))
    
    end_time = time.time()
    
    print(f"✅ 完成: {end_time - start_time:.2f}秒")
    print("📈 如果所有核心都激活了，说明多进程调度正常")

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 OCR多核调度测试")
    print("=" * 60)
    
    test_ocr_performance()
    test_real_multiprocessing()
    
    print("\n" + "=" * 60)
    print("💡 测试结论:")
    print("   如果看到CPU使用率接近100%，说明多核调度正常")
    print("   如果还是12%，可能是:")
    print("   1. 系统限制了Python多进程")
    print("   2. 当前OCR处理不是CPU密集型")
    print("   3. 需要重启应用使优化生效")
    print("=" * 60)
