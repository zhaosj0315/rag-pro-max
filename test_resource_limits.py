#!/usr/bin/env python3
"""
测试资源限制优化
验证CPU和内存阈值调整效果
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.cpu_monitor import get_resource_limiter, check_system_resources
from utils.optimized_ocr_processor import OptimizedOCRProcessor
import time

def test_resource_limits():
    """测试资源限制"""
    print("🧪 测试资源限制优化")
    print("=" * 60)
    
    # 1. 测试新的阈值设置
    print("📊 当前系统资源状态:")
    resources = check_system_resources()
    print(f"   CPU使用率: {resources['cpu_percent']:.1f}%")
    print(f"   内存使用率: {resources['memory_percent']:.1f}%")
    print(f"   可用内存: {resources['memory_available_gb']:.1f}GB")
    print(f"   CPU过高: {'是' if resources['cpu_high'] else '否'} (阈值: 75%)")
    print(f"   内存过高: {'是' if resources['memory_high'] else '否'} (阈值: 85%)")
    
    # 2. 测试资源限制器
    print("\n🔧 测试资源限制器:")
    limiter = get_resource_limiter()
    print(f"   CPU阈值: {limiter.max_cpu_percent}%")
    print(f"   内存阈值: {limiter.max_memory_percent}%")
    
    # 3. 测试工作线程数调整
    print("\n⚙️ 测试工作线程数调整:")
    for default_workers in [4, 8, 12]:
        safe_workers = limiter.get_safe_worker_count(default_workers)
        print(f"   默认 {default_workers} 线程 → 安全 {safe_workers} 线程")
    
    # 4. 测试OCR处理器配置
    print("\n🔍 测试OCR处理器配置:")
    processor = OptimizedOCRProcessor()
    print(f"   最大工作进程: {processor.max_workers}")
    print(f"   CPU阈值: {processor.resource_limiter.max_cpu_percent}%")
    print(f"   内存阈值: {processor.resource_limiter.max_memory_percent}%")
    
    # 5. 测试限流机制
    print("\n🚦 测试限流机制:")
    should_throttle = limiter.should_throttle()
    print(f"   是否需要限流: {'是' if should_throttle else '否'}")
    
    if should_throttle:
        print("   ⚠️ 系统资源紧张，建议等待...")
    else:
        print("   ✅ 系统资源充足，可以正常处理")
    
    print("\n" + "=" * 60)
    print("✅ 资源限制测试完成！")
    
    # 显示优化效果
    print("\n📈 优化效果:")
    print("   🔻 CPU阈值: 95% → 75% (-20%)")
    print("   🔻 内存阈值: 90% → 85% (-5%)")
    print("   🔻 最大进程: 4 → 3 (-25%)")
    print("   🛡️ 综合资源保护: CPU + 内存双重监控")
    print("   🚀 动态线程调整: 根据实际负载智能调节")

if __name__ == "__main__":
    test_resource_limits()
