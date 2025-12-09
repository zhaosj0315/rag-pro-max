"""
RAG Pro Max v1.5.1 可行性测试
测试性能监控面板功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_performance_monitor_import():
    """测试性能监控模块导入"""
    try:
        from src.ui.performance_monitor import PerformanceMonitor, get_monitor
        print("✅ performance_monitor: PASS")
        return True
    except Exception as e:
        print(f"❌ performance_monitor: FAIL - {e}")
        return False


def test_performance_monitor_creation():
    """测试性能监控器创建"""
    try:
        from src.ui.performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor()
        assert monitor.logger is not None
        print("✅ 监控器创建: PASS")
        return True
    except Exception as e:
        print(f"❌ 监控器创建: FAIL - {e}")
        return False


def test_logger_metrics():
    """测试 LogManager 性能指标"""
    try:
        from src.logging import LogManager
        logger = LogManager()
        
        # 测试计时器
        logger.start_timer("test")
        import time
        time.sleep(0.1)
        elapsed = logger.end_timer("test")
        
        assert elapsed >= 0.1
        assert elapsed < 0.2
        
        # 测试指标获取
        metrics = logger.get_metrics()
        assert isinstance(metrics, dict)
        
        print("✅ LogManager 指标: PASS")
        return True
    except Exception as e:
        print(f"❌ LogManager 指标: FAIL - {e}")
        return False


def test_syntax_check():
    """语法检查"""
    import py_compile
    
    files = [
        "src/ui/performance_monitor.py",
    ]
    
    all_pass = True
    for file in files:
        try:
            py_compile.compile(file, doraise=True)
            print(f"✅ {file}: PASS")
        except py_compile.PyCompileError as e:
            print(f"❌ {file}: FAIL - {e}")
            all_pass = False
    
    return all_pass


def main():
    print("\n" + "="*60)
    print("  RAG Pro Max v1.5.1 可行性测试")
    print("="*60 + "\n")
    
    tests = [
        ("1. 模块导入测试", test_performance_monitor_import),
        ("2. 监控器创建测试", test_performance_monitor_creation),
        ("3. LogManager 指标测试", test_logger_metrics),
        ("4. 语法检查", test_syntax_check),
    ]
    
    results = []
    for name, test_func in tests:
        print("\n" + "="*60)
        print(f"  {name}")
        print("="*60)
        results.append(test_func())
    
    # 汇总
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！v1.5.1 可以发布。")
        return 0
    else:
        print(f"\n❌ 有 {total - passed} 个测试失败，请修复后再发布。")
        return 1


if __name__ == "__main__":
    exit(main())
