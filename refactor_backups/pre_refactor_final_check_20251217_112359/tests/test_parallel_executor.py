#!/usr/bin/env python3
"""
并行执行器测试
Stage 6 - 测试并行执行管理器
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.parallel_executor import ParallelExecutor


def dummy_task(x):
    """测试任务：计算平方"""
    return x * x


def test_parallel_executor_init():
    """测试初始化"""
    print("\n测试1: 初始化")
    executor = ParallelExecutor()
    assert executor.max_workers >= 2, "max_workers应该至少为2"
    print(f"✅ 初始化成功，max_workers={executor.max_workers}")


def test_should_parallelize():
    """测试并行判断逻辑"""
    print("\n测试2: 并行判断逻辑")
    executor = ParallelExecutor()
    
    # 任务数太少，不应该并行
    assert not executor.should_parallelize(5, threshold=10), "5个任务不应该并行"
    print("✅ 少量任务判断正确（串行）")
    
    # 任务数足够，应该并行
    assert executor.should_parallelize(20, threshold=10), "20个任务应该并行"
    print("✅ 大量任务判断正确（并行）")


def test_execute_serial():
    """测试串行执行"""
    print("\n测试3: 串行执行")
    executor = ParallelExecutor()
    tasks = list(range(5))
    results = executor.execute(dummy_task, tasks, threshold=10)
    
    expected = [0, 1, 4, 9, 16]
    assert results == expected, f"结果不匹配: {results} != {expected}"
    print(f"✅ 串行执行正确: {results}")


def test_execute_parallel():
    """测试并行执行"""
    print("\n测试4: 并行执行")
    executor = ParallelExecutor()
    tasks = list(range(20))
    results = executor.execute(dummy_task, tasks, threshold=10)
    
    expected = [x * x for x in range(20)]
    assert results == expected, f"结果不匹配"
    print(f"✅ 并行执行正确: 处理了 {len(results)} 个任务")


def test_execute_with_progress():
    """测试带进度的执行"""
    print("\n测试5: 带进度的执行")
    executor = ParallelExecutor()
    tasks = list(range(15))
    
    progress = []
    def callback(completed, total):
        progress.append((completed, total))
    
    results = executor.execute_with_progress(dummy_task, tasks, callback, threshold=10)
    
    expected = [x * x for x in range(15)]
    assert results == expected, "结果不匹配"
    assert len(progress) == 15, f"进度回调次数不对: {len(progress)}"
    assert progress[-1] == (15, 15), "最后的进度应该是 (15, 15)"
    print(f"✅ 带进度执行正确: {len(progress)} 次回调")


if __name__ == "__main__":
    print("=" * 60)
    print("并行执行器测试")
    print("=" * 60)
    
    try:
        test_parallel_executor_init()
        test_should_parallelize()
        test_execute_serial()
        test_execute_parallel()
        test_execute_with_progress()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
