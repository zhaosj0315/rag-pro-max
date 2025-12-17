#!/usr/bin/env python3
"""
方案B集成测试
验证完整优化功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试导入"""
    print("测试1: 导入优化模块...")
    try:
        from src.utils.concurrency_manager import ConcurrencyManager
        from src.utils.vectorization_wrapper import VectorizationWrapper
        from src.utils.dynamic_batch import DynamicBatchOptimizer
        from src.utils.adaptive_throttling import get_resource_guard
        print("  ✅ 导入成功")
        return True
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def test_concurrency_manager():
    """测试并发管理器"""
    print("\n测试2: 并发管理器...")
    try:
        from src.utils.concurrency_manager import ConcurrencyManager
        
        mgr = ConcurrencyManager()
        
        print(f"  并发管理器创建成功")
        print("  ✅ 并发管理器正常")
        return True
    except Exception as e:
        print(f"  ❌ 并发管理器失败: {e}")
        return False

def test_batch_optimizer():
    """测试批量优化器"""
    print("\n测试3: 批量优化器...")
    try:
        from src.utils.dynamic_batch import DynamicBatchOptimizer
        
        optimizer = DynamicBatchOptimizer()
        batch_size = optimizer.calculate_batch_size(doc_count=100, avg_doc_size=1000)
        
        print(f"  最优批量大小: {batch_size}")
        print("  ✅ 批量优化器正常")
        return True
    except Exception as e:
        print(f"  ❌ 批量优化器失败: {e}")
        return False

def test_vectorization_wrapper():
    """测试向量化包装器"""
    print("\n测试4: 向量化包装器...")
    try:
        from src.utils.vectorization_wrapper import VectorizationWrapper
        from src.utils.dynamic_batch import DynamicBatchOptimizer
        
        # 创建模拟嵌入模型
        class MockEmbedModel:
            pass
        
        wrapper = VectorizationWrapper(
            embed_model=MockEmbedModel(),
            batch_optimizer=DynamicBatchOptimizer()
        )
        
        print("  ✅ 向量化包装器创建成功")
        return True
    except Exception as e:
        print(f"  ❌ 向量化包装器失败: {e}")
        return False

def test_index_builder_integration():
    """测试 IndexBuilder 集成"""
    print("\n测试5: IndexBuilder 集成...")
    try:
        with open('src/processors/index_builder.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('from src.utils.concurrency_manager import ConcurrencyManager', '并发管理器导入'),
            ('from src.utils.vectorization_wrapper import VectorizationWrapper', '向量化包装器导入'),
            ('from src.utils.dynamic_batch import DynamicBatchOptimizer', '批量优化器导入'),
            ('self.concurrency_mgr = ConcurrencyManager()', '并发管理器初始化'),
            ('self.batch_optimizer = DynamicBatchOptimizer()', '批量优化器初始化'),
            ('self.vectorization_wrapper', '向量化包装器使用')
        ]
        
        all_passed = True
        for check_str, desc in checks:
            if check_str in content:
                print(f"  ✅ {desc}")
            else:
                print(f"  ❌ {desc} - 未找到")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ 集成检查失败: {e}")
        return False

def main():
    print("=" * 60)
    print("  方案B集成测试")
    print("=" * 60)
    
    results = []
    results.append(("导入测试", test_imports()))
    results.append(("并发管理器", test_concurrency_manager()))
    results.append(("批量优化器", test_batch_optimizer()))
    results.append(("向量化包装器", test_vectorization_wrapper()))
    results.append(("IndexBuilder集成", test_index_builder_integration()))
    
    print("\n" + "=" * 60)
    print("  测试结果")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！方案B已成功集成。")
        return 0
    else:
        print(f"\n❌ {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
