#!/usr/bin/env python3
"""
CPU 限制功能测试脚本
测试CPU使用率限制是否正常工作
"""

import time
import threading
from src.utils.cpu_throttle import CPUThrottle, safe_parallel_execute

def cpu_intensive_task(n):
    """CPU密集型任务"""
    result = 0
    for i in range(n * 1000000):
        result += i * i
    return result

def test_cpu_throttle():
    """测试CPU限制功能"""
    print("🧪 开始测试CPU限制功能...")
    
    # 创建CPU限制器
    throttle = CPUThrottle(max_cpu_percent=90.0, check_interval=0.2)
    throttle.start_monitoring()
    
    try:
        # 创建大量CPU密集型任务
        tasks = [100] * 20  # 20个CPU密集型任务
        
        print(f"📋 准备执行 {len(tasks)} 个CPU密集型任务...")
        print("⚠️  如果CPU使用率超过90%，系统会自动限流")
        
        start_time = time.time()
        
        # 使用安全的并行执行
        results = safe_parallel_execute(
            func=cpu_intensive_task,
            tasks=tasks,
            max_workers=8,
            cpu_limit=90.0
        )
        
        end_time = time.time()
        
        print(f"✅ 任务完成！")
        print(f"⏱️  总耗时: {end_time - start_time:.2f} 秒")
        print(f"📊 完成任务数: {len([r for r in results if r is not None])}/{len(tasks)}")
        
        if throttle.is_throttling:
            print("⚠️  当前仍在限流中，CPU使用率过高")
        else:
            print("✅ CPU使用率正常")
            
    finally:
        throttle.stop_monitoring()
        print("🛑 CPU监控已停止")

def test_manual_cpu_spike():
    """手动创建CPU峰值测试"""
    print("\n🔥 手动创建CPU峰值测试...")
    
    def cpu_burner():
        """CPU燃烧器"""
        end_time = time.time() + 5  # 运行5秒
        while time.time() < end_time:
            _ = sum(i * i for i in range(10000))
    
    # 启动多个CPU燃烧线程
    threads = []
    for i in range(8):  # 8个线程
        t = threading.Thread(target=cpu_burner)
        threads.append(t)
        t.start()
    
    # 等待完成
    for t in threads:
        t.join()
    
    print("🔥 CPU峰值测试完成")

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️  CPU 限制功能测试")
    print("=" * 60)
    
    # 测试1: CPU限制功能
    test_cpu_throttle()
    
    # 等待一下
    time.sleep(2)
    
    # 测试2: 手动CPU峰值
    test_manual_cpu_spike()
    
    print("\n✅ 所有测试完成！")
    print("💡 如果系统没有自动关机，说明CPU限制功能正常工作")
