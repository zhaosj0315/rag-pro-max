#!/usr/bin/env python3
"""
RAG Pro Max v2.2.2 可行性测试
测试资源保护和日志记录功能
"""

import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_resource_protection():
    """测试资源保护机制"""
    print("🛡️ 测试资源保护机制")
    try:
        from utils.cpu_monitor import get_resource_limiter, check_system_resources
        
        # 测试资源限制器
        limiter = get_resource_limiter()
        assert limiter.max_cpu_percent == 75.0, f"CPU阈值应为75%，实际为{limiter.max_cpu_percent}%"
        assert limiter.max_memory_percent == 85.0, f"内存阈值应为85%，实际为{limiter.max_memory_percent}%"
        
        # 测试系统资源检查
        resources = check_system_resources()
        assert 'cpu_percent' in resources
        assert 'memory_percent' in resources
        assert 'cpu_high' in resources
        assert 'memory_high' in resources
        
        print("   ✅ 资源保护机制正常")
        return True
    except Exception as e:
        print(f"   ❌ 资源保护测试失败: {e}")
        return False

def test_ocr_logging():
    """测试OCR日志记录"""
    print("📊 测试OCR日志记录")
    try:
        from utils.optimized_ocr_processor import get_ocr_processor
        
        # 创建日志目录
        os.makedirs('app_logs', exist_ok=True)
        
        # 获取OCR处理器
        processor = get_ocr_processor()
        
        # 测试统计功能
        stats = processor.get_statistics()
        required_keys = ['total_files_processed', 'total_processing_time', 
                        'session_duration', 'avg_time_per_file', 
                        'files_per_minute', 'session_start_time']
        
        for key in required_keys:
            assert key in stats, f"统计信息缺少字段: {key}"
        
        # 测试日志文件
        log_file = 'app_logs/ocr_processing.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                content = f.read()
                assert len(content) > 0, "日志文件为空"
        
        print("   ✅ OCR日志记录正常")
        return True
    except Exception as e:
        print(f"   ❌ OCR日志测试失败: {e}")
        return False

def test_log_viewer():
    """测试日志查看工具"""
    print("🔧 测试日志查看工具")
    try:
        # 检查日志查看器文件
        log_viewer = 'view_ocr_logs.py'
        assert os.path.exists(log_viewer), f"日志查看器不存在: {log_viewer}"
        
        # 检查文件可执行
        with open(log_viewer, 'r') as f:
            content = f.read()
            assert 'view_ocr_logs' in content, "日志查看器函数缺失"
            assert 'argparse' in content, "命令行参数解析缺失"
        
        print("   ✅ 日志查看工具正常")
        return True
    except Exception as e:
        print(f"   ❌ 日志查看工具测试失败: {e}")
        return False

def test_documentation():
    """测试文档完整性"""
    print("📚 测试文档完整性")
    try:
        docs = [
            'docs/OCR_LOGGING_SYSTEM.md',
            'docs/RESOURCE_PROTECTION_V2.md',
            'RELEASE_NOTES_v2.2.2.md',
            'CHANGELOG.md'
        ]
        
        for doc in docs:
            assert os.path.exists(doc), f"文档缺失: {doc}"
            with open(doc, 'r') as f:
                content = f.read()
                assert len(content) > 100, f"文档内容过少: {doc}"
        
        print("   ✅ 文档完整性正常")
        return True
    except Exception as e:
        print(f"   ❌ 文档测试失败: {e}")
        return False

def test_version_info():
    """测试版本信息"""
    print("📋 测试版本信息")
    try:
        import json
        
        # 检查版本文件
        with open('version.json', 'r') as f:
            version_info = json.load(f)
        
        assert version_info['version'] == '2.2.2', f"版本号错误: {version_info['version']}"
        assert version_info['codename'] == '资源保护增强版', f"代号错误: {version_info['codename']}"
        assert 'OCR日志记录系统' in version_info['features'], "功能列表缺少OCR日志记录"
        
        print("   ✅ 版本信息正常")
        return True
    except Exception as e:
        print(f"   ❌ 版本信息测试失败: {e}")
        return False

def test_test_scripts():
    """测试测试脚本"""
    print("🧪 测试测试脚本")
    try:
        test_scripts = [
            'test_resource_limits.py',
            'test_ocr_logging.py'
        ]
        
        for script in test_scripts:
            assert os.path.exists(script), f"测试脚本缺失: {script}"
            with open(script, 'r') as f:
                content = f.read()
                assert 'def test_' in content, f"测试脚本格式错误: {script}"
        
        print("   ✅ 测试脚本正常")
        return True
    except Exception as e:
        print(f"   ❌ 测试脚本测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 RAG Pro Max v2.2.2 可行性测试")
    print("=" * 60)
    
    tests = [
        ("资源保护机制", test_resource_protection),
        ("OCR日志记录", test_ocr_logging),
        ("日志查看工具", test_log_viewer),
        ("文档完整性", test_documentation),
        ("版本信息", test_version_info),
        ("测试脚本", test_test_scripts)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        result = test_func()
        if result:
            passed += 1
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有测试通过！v2.2.2 功能完整，可以发布。")
        return True
    else:
        print(f"\n⚠️ 有 {total - passed} 个测试失败，需要修复后再发布。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
