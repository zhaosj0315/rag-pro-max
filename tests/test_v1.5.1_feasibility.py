"""
RAG Pro Max v1.5.1 可行性测试
测试性能监控、推荐问题优化、错误恢复功能
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


def test_suggestion_engine_enhanced():
    """测试推荐引擎增强功能"""
    try:
        from src.chat.suggestion_engine import SuggestionEngine
        
        engine = SuggestionEngine("test_kb")
        
        # 测试自定义推荐
        engine.add_custom_suggestion("测试问题1")
        engine.add_custom_suggestion("测试问题2")
        assert len(engine.get_custom_suggestions()) == 2
        
        # 测试删除
        engine.remove_custom_suggestion("测试问题1")
        assert len(engine.get_custom_suggestions()) == 1
        
        # 测试统计
        stats = engine.get_stats()
        assert 'custom_count' in stats
        assert stats['custom_count'] == 1
        
        # 测试历史
        engine.history = ["问题1", "问题2", "问题3"]
        history = engine.get_history(limit=2)
        assert len(history) == 2
        
        print("✅ 推荐引擎增强: PASS")
        return True
    except Exception as e:
        print(f"❌ 推荐引擎增强: FAIL - {e}")
        return False


def test_suggestion_panel():
    """测试推荐问题管理面板"""
    try:
        from src.ui.suggestion_panel import SuggestionPanel
        from src.chat.suggestion_engine import SuggestionEngine
        
        engine = SuggestionEngine("test_kb")
        panel = SuggestionPanel(engine)
        
        assert panel.engine is not None
        
        print("✅ 推荐问题面板: PASS")
        return True
    except Exception as e:
        print(f"❌ 推荐问题面板: FAIL - {e}")
        return False


def test_error_handler_enhanced():
    """测试错误处理增强功能"""
    try:
        from src.utils.error_handler import ErrorHandler, retry_on_error
        import time
        
        # 测试重试机制
        attempt_count = [0]
        
        @retry_on_error(max_retries=3, delay=0.05, backoff=1.5)
        def flaky_function():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise ConnectionError("模拟错误")
            return "成功"
        
        result = flaky_function()
        assert result == "成功"
        assert attempt_count[0] == 3
        
        # 测试错误消息
        try:
            raise FileNotFoundError("test.txt")
        except Exception as e:
            msg = ErrorHandler.with_recovery(e, "测试")
            assert "建议" in msg
        
        print("✅ 错误处理增强: PASS")
        return True
    except Exception as e:
        print(f"❌ 错误处理增强: FAIL - {e}")
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
        "src/ui/suggestion_panel.py",
        "src/chat/suggestion_engine.py",
        "src/utils/error_handler.py",
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
        ("1. 性能监控模块", test_performance_monitor_import),
        ("2. 推荐引擎增强", test_suggestion_engine_enhanced),
        ("3. 推荐问题面板", test_suggestion_panel),
        ("4. 错误处理增强", test_error_handler_enhanced),
        ("5. LogManager 指标", test_logger_metrics),
        ("6. 语法检查", test_syntax_check),
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

