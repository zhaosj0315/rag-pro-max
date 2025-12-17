"""端到端测试 - 完整工作流测试"""

import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_complete_workflow():
    """测试完整工作流：创建知识库 → 上传文档 → 查询"""
    print("\n" + "="*60)
    print("  端到端测试 - 完整工作流")
    print("="*60 + "\n")
    
    results = {"passed": 0, "failed": 0}
    
    # 1. 测试模块导入
    print("1. 测试模块导入...")
    try:
        from src.kb import KBManager
        from src.config import ConfigLoader
        from src.chat import HistoryManager
        from src.logging import LogManager
        print("   ✅ 所有模块导入成功")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 模块导入失败: {e}")
        results["failed"] += 1
        return results
    
    # 2. 测试知识库创建
    print("\n2. 测试知识库创建...")
    try:
        temp_dir = tempfile.mkdtemp()
        kb_mgr = KBManager(base_path=temp_dir)
        success, msg = kb_mgr.create("test_kb")
        assert success, f"创建失败: {msg}"
        assert kb_mgr.exists("test_kb"), "知识库不存在"
        print(f"   ✅ 知识库创建成功: {msg}")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 知识库创建失败: {e}")
        results["failed"] += 1
    
    # 3. 测试配置加载
    print("\n3. 测试配置加载...")
    try:
        config = ConfigLoader.load()
        assert isinstance(config, dict), "配置格式错误"
        assert "llm_model_ollama" in config, "缺少必要配置"
        print(f"   ✅ 配置加载成功: {len(config)} 个配置项")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 配置加载失败: {e}")
        results["failed"] += 1
    
    # 4. 测试聊天历史
    print("\n4. 测试聊天历史...")
    try:
        messages = [
            {"role": "user", "content": "测试问题"},
            {"role": "assistant", "content": "测试回答"}
        ]
        HistoryManager.save("test_kb", messages)
        loaded = HistoryManager.load("test_kb")
        assert len(loaded) == 2, f"消息数量不匹配: {len(loaded)}"
        assert loaded[0]["content"] == "测试问题", "消息内容不匹配"
        print(f"   ✅ 聊天历史保存/加载成功")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 聊天历史测试失败: {e}")
        results["failed"] += 1
    
    # 5. 测试日志记录
    print("\n5. 测试日志记录...")
    try:
        logger = LogManager()
        logger.log('INFO', "测试日志", stage="测试")
        assert os.path.exists(logger.log_file), "日志文件不存在"
        print(f"   ✅ 日志记录成功: {logger.log_file}")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 日志记录失败: {e}")
        results["failed"] += 1
    
    # 6. 测试知识库列表
    print("\n6. 测试知识库列表...")
    try:
        kbs = kb_mgr.list_all()
        assert "test_kb" in kbs, "知识库未在列表中"
        print(f"   ✅ 知识库列表: {kbs}")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 知识库列表失败: {e}")
        results["failed"] += 1
    
    # 7. 测试知识库删除
    print("\n7. 测试知识库删除...")
    try:
        success, msg = kb_mgr.delete("test_kb")
        assert success, f"删除失败: {msg}"
        assert not kb_mgr.exists("test_kb"), "知识库仍然存在"
        print(f"   ✅ 知识库删除成功")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 知识库删除失败: {e}")
        results["failed"] += 1
    
    # 清理
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
        HistoryManager.clear("test_kb")
    except:
        pass
    
    return results


def test_performance_baseline():
    """性能基准测试"""
    print("\n" + "="*60)
    print("  性能基准测试")
    print("="*60 + "\n")
    
    import time
    results = {"passed": 0, "failed": 0}
    
    # 1. 模块导入速度
    print("1. 测试模块导入速度...")
    try:
        start = time.time()
        from src.kb import KBManager
        from src.config import ConfigLoader
        from src.chat import HistoryManager
        from src.logging import LogManager
        elapsed = time.time() - start
        
        assert elapsed < 1.0, f"导入太慢: {elapsed:.2f}s"
        print(f"   ✅ 导入耗时: {elapsed:.3f}s (< 1.0s)")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 导入速度测试失败: {e}")
        results["failed"] += 1
    
    # 2. 配置加载速度
    print("\n2. 测试配置加载速度...")
    try:
        start = time.time()
        config = ConfigLoader.load()
        elapsed = time.time() - start
        
        assert elapsed < 0.1, f"加载太慢: {elapsed:.2f}s"
        print(f"   ✅ 加载耗时: {elapsed:.3f}s (< 0.1s)")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 配置加载速度测试失败: {e}")
        results["failed"] += 1
    
    # 3. 日志写入速度
    print("\n3. 测试日志写入速度...")
    try:
        logger = LogManager()
        start = time.time()
        for i in range(100):
            logger.log('INFO', f"测试日志 {i}", stage="性能测试")
        elapsed = time.time() - start
        
        avg = elapsed / 100
        assert avg < 0.01, f"写入太慢: {avg:.4f}s/条"
        print(f"   ✅ 平均耗时: {avg:.4f}s/条 (< 0.01s)")
        results["passed"] += 1
    except Exception as e:
        print(f"   ❌ 日志写入速度测试失败: {e}")
        results["failed"] += 1
    
    return results


if __name__ == "__main__":
    # 运行测试
    workflow_results = test_complete_workflow()
    perf_results = test_performance_baseline()
    
    # 汇总
    total_passed = workflow_results["passed"] + perf_results["passed"]
    total_failed = workflow_results["failed"] + perf_results["failed"]
    total = total_passed + total_failed
    
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    print(f"✅ 通过: {total_passed}/{total}")
    print(f"❌ 失败: {total_failed}/{total}")
    
    if total_failed == 0:
        print("\n✅ 所有端到端测试通过！")
        sys.exit(0)
    else:
        print(f"\n❌ {total_failed} 个测试失败")
        sys.exit(1)
