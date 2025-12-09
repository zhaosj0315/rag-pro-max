#!/usr/bin/env python3
"""RAG Pro Max v1.5.0 可行性测试"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_new_modules():
    """测试新模块导入"""
    print("\n" + "="*60)
    print("  1. 新模块导入测试")
    print("="*60)
    
    try:
        from src.utils.query_cache import QueryCache, get_cache
        print("✅ query_cache: PASS")
    except Exception as e:
        print(f"❌ query_cache: FAIL - {e}")
        return False
    
    try:
        from src.chat.suggestion_engine import SuggestionEngine
        print("✅ suggestion_engine: PASS")
    except Exception as e:
        print(f"❌ suggestion_engine: FAIL - {e}")
        return False
    
    try:
        from src.utils.error_handler import ErrorHandler, handle_errors
        print("✅ error_handler: PASS")
    except Exception as e:
        print(f"❌ error_handler: FAIL - {e}")
        return False
    
    return True


def test_query_cache():
    """测试查询缓存"""
    print("\n" + "="*60)
    print("  2. 查询缓存功能测试")
    print("="*60)
    
    try:
        from src.utils.query_cache import QueryCache
        
        cache = QueryCache(max_size=10)
        
        # 测试设置和获取
        cache.set("test query", "test_kb", 5, ("result", []))
        result = cache.get("test query", "test_kb", 5)
        
        if result is not None:
            print("✅ 缓存设置和获取: PASS")
        else:
            print("❌ 缓存设置和获取: FAIL")
            return False
        
        # 测试统计
        stats = cache.get_stats()
        if stats['size'] == 1:
            print("✅ 缓存统计: PASS")
        else:
            print("❌ 缓存统计: FAIL")
            return False
        
        # 测试清空
        cache.clear()
        if cache.get_stats()['size'] == 0:
            print("✅ 缓存清空: PASS")
        else:
            print("❌ 缓存清空: FAIL")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 查询缓存测试: FAIL - {e}")
        return False


def test_suggestion_engine():
    """测试推荐引擎"""
    print("\n" + "="*60)
    print("  3. 推荐引擎功能测试")
    print("="*60)
    
    try:
        from src.chat.suggestion_engine import SuggestionEngine
        
        engine = SuggestionEngine()
        
        # 测试生成（使用降级策略）
        questions = engine.generate("测试上下文", num_questions=3)
        
        if len(questions) > 0:
            print(f"✅ 推荐问题生成: PASS ({len(questions)} 个问题)")
        else:
            print("⚠️  推荐问题生成: WARNING (使用降级策略)")
        
        # 测试队列
        engine.add_to_queue("测试问题")
        if engine.get_stats()['queue_count'] == 1:
            print("✅ 队列管理: PASS")
        else:
            print("❌ 队列管理: FAIL")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 推荐引擎测试: FAIL - {e}")
        return False


def test_error_handler():
    """测试错误处理"""
    print("\n" + "="*60)
    print("  4. 错误处理功能测试")
    print("="*60)
    
    try:
        from src.utils.error_handler import ErrorHandler
        
        # 测试错误消息生成
        error = ValueError("测试错误")
        msg = ErrorHandler.handle_error(error, "测试上下文")
        
        if "测试上下文" in msg and "数据格式错误" in msg:
            print("✅ 错误消息生成: PASS")
        else:
            print("❌ 错误消息生成: FAIL")
            return False
        
        # 测试恢复建议
        recovery_msg = ErrorHandler.with_recovery(error, "测试上下文")
        
        if "建议" in recovery_msg:
            print("✅ 恢复建议: PASS")
        else:
            print("❌ 恢复建议: FAIL")
            return False
        
        # 测试安全执行
        def test_func():
            return "success"
        
        success, result = ErrorHandler.safe_execute(test_func)
        
        if success and result == "success":
            print("✅ 安全执行: PASS")
        else:
            print("❌ 安全执行: FAIL")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 错误处理测试: FAIL - {e}")
        return False


def test_log_manager_extended():
    """测试扩展的 LogManager"""
    print("\n" + "="*60)
    print("  5. LogManager 扩展功能测试")
    print("="*60)
    
    try:
        from src.logging.log_manager import LogManager
        
        logger = LogManager(enable_terminal=False)
        
        # 测试新方法
        logger.start_operation("测试操作")
        logger.processing("处理中")
        logger.complete_operation("测试操作")
        print("✅ 操作日志方法: PASS")
        
        logger.data_summary("测试数据", {"key": "value"})
        print("✅ 数据摘要方法: PASS")
        
        logger.separator("测试分隔符")
        print("✅ 分隔符方法: PASS")
        
        # 测试计时器
        with logger.timer("测试计时", show_result=False):
            pass
        print("✅ 计时器: PASS")
        
        # 测试性能指标
        metrics = logger.get_metrics()
        if "测试计时" in metrics:
            print("✅ 性能指标: PASS")
        else:
            print("❌ 性能指标: FAIL")
            return False
        
        return True
    except Exception as e:
        print(f"❌ LogManager 扩展测试: FAIL - {e}")
        return False


def test_syntax():
    """测试语法"""
    print("\n" + "="*60)
    print("  6. 语法检查")
    print("="*60)
    
    try:
        import py_compile
        
        files = [
            'src/utils/query_cache.py',
            'src/chat/suggestion_engine.py',
            'src/utils/error_handler.py',
            'src/logging/log_manager.py'
        ]
        
        for file in files:
            py_compile.compile(file, doraise=True)
            print(f"✅ {file}: PASS")
        
        return True
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  RAG Pro Max v1.5.0 可行性测试")
    print("="*60)
    
    tests = [
        ("新模块导入", test_new_modules),
        ("查询缓存", test_query_cache),
        ("推荐引擎", test_suggestion_engine),
        ("错误处理", test_error_handler),
        ("LogManager扩展", test_log_manager_extended),
        ("语法检查", test_syntax),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！v1.5.0 可以发布。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查后再发布。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
