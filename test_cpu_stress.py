#!/usr/bin/env python3
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import time

def cpu_intensive_task(n):
    """CPU密集型任务"""
    total = 0
    for i in range(n * 100000):
        total += i * i
    return total

def test_cpu_utilization():
    """测试CPU利用率"""
    print("🔥 CPU压力测试开始...")
    
    # 使用所有CPU核心
    workers = mp.cpu_count()
    tasks = [1000] * (workers * 2)  # 创建更多任务
    
    print(f"💪 启动 {workers} 进程处理 {len(tasks)} 个任务")
    
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(cpu_intensive_task, tasks))
    
    end_time = time.time()
    
    print(f"✅ 测试完成: {end_time - start_time:.2f}秒")
    print(f"📊 现在检查系统监控，CPU使用率应该接近100%")

if __name__ == "__main__":
    test_cpu_utilization()
