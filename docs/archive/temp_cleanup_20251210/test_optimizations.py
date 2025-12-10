#!/usr/bin/env python3
"""
优化功能集成测试
"""

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.optimization_manager import optimization_manager
from src.utils.enhanced_cache import enhanced_cache
from src.utils.gpu_optimizer import gpu_optimizer
from src.processors.multimodal_processor import multimodal_processor

def test_gpu_optimization():
    """测试GPU优化"""
    print("🎯 测试GPU优化...")
    
    try:
        gpu_optimizer.optimize_gpu_utilization()
        stats = gpu_optimizer.get_gpu_stats()
        print(f"✅ GPU设备: {stats.get('device', 'cpu')}")
        return True
    except Exception as e:
        print(f"❌ GPU优化失败: {e}")
        return False

def test_cache_system():
    """测试缓存系统"""
    print("💾 测试缓存系统...")
    
    try:
        # 测试缓存存储和获取
        test_data = {"answer": "测试回答", "sources": []}
        enhanced_cache.set("测试查询", "测试知识库", test_data)
        
        cached_result = enhanced_cache.get("测试查询", "测试知识库")
        
        if cached_result:
            print("✅ 缓存存储/获取正常")
            stats = enhanced_cache.get_stats()
            print(f"✅ 缓存统计: {stats}")
            return True
        else:
            print("❌ 缓存获取失败")
            return False
            
    except Exception as e:
        print(f"❌ 缓存测试失败: {e}")
        return False

def test_multimodal_support():
    """测试多模态支持"""
    print("📄 测试多模态支持...")
    
    try:
        supported_formats = multimodal_processor.get_supported_formats()
        print(f"✅ 支持格式: {supported_formats}")
        
        # 测试处理能力
        if supported_formats['images'] and supported_formats['tables']:
            print("✅ 多模态处理器就绪")
            return True
        else:
            print("❌ 多模态支持不完整")
            return False
            
    except Exception as e:
        print(f"❌ 多模态测试失败: {e}")
        return False

def test_optimization_manager():
    """测试优化管理器"""
    print("🚀 测试优化管理器...")
    
    try:
        optimization_manager.initialize_all_optimizations()
        status = optimization_manager.get_optimization_status()
        
        print(f"✅ 优化状态: {status['enabled']}")
        print(f"✅ 统计信息: {status['stats']}")
        return True
        
    except Exception as e:
        print(f"❌ 优化管理器测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 RAG Pro Max 优化功能集成测试")
    print("=" * 50)
    
    tests = [
        ("GPU优化", test_gpu_optimization),
        ("缓存系统", test_cache_system),
        ("多模态支持", test_multimodal_support),
        ("优化管理器", test_optimization_manager)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}测试...")
        if test_func():
            passed += 1
            print(f"✅ {test_name}测试通过")
        else:
            print(f"❌ {test_name}测试失败")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有优化功能测试通过！")
        return True
    else:
        print(f"⚠️ {total - passed} 个测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
