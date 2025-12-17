"""
Logger 接口兼容性测试
确保所有 logger 调用参数正确
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.logger import logger


def test_log_kb_complete():
    """测试 log_kb_complete 接口"""
    print("测试 log_kb_complete...")
    
    # 正确的调用方式
    try:
        logger.log_kb_complete(kb_name="test_kb", doc_count=10)
        print("✅ log_kb_complete 参数正确")
    except TypeError as e:
        print(f"❌ log_kb_complete 参数错误: {e}")
        raise


def test_log_kb_start():
    """测试 log_kb_start 接口"""
    print("测试 log_kb_start...")
    
    try:
        logger.log_kb_start(kb_name="test_kb")
        print("✅ log_kb_start 参数正确")
    except TypeError as e:
        print(f"❌ log_kb_start 参数错误: {e}")
        raise


def test_log_kb_read_success():
    """测试 log_kb_read_success 接口"""
    print("测试 log_kb_read_success...")
    
    try:
        logger.log_kb_read_success(doc_count=10, file_count=5, kb_name="test_kb")
        print("✅ log_kb_read_success 参数正确")
    except TypeError as e:
        print(f"❌ log_kb_read_success 参数错误: {e}")
        raise


def test_all_logger_methods():
    """测试所有 logger 方法是否存在"""
    print("\n测试所有 logger 方法...")
    
    required_methods = [
        'log_kb_start',
        'log_kb_complete',
        'log_kb_load_index',
        'log_kb_scan_path',
        'log_kb_read_success',
        'log_kb_mount_start',
        'log_kb_mount_success',
        'log_kb_mount_error',
        'log_user_question',
        'log_retrieval_start',
        'log_retrieval_result',
        'log_answer_complete',
        'log_file_upload'
    ]
    
    for method in required_methods:
        assert hasattr(logger, method), f"❌ 缺少方法: {method}"
    
    print(f"✅ 所有 {len(required_methods)} 个方法都存在")


if __name__ == "__main__":
    print("=" * 60)
    print("Logger 接口兼容性测试")
    print("=" * 60)
    
    try:
        test_log_kb_start()
        test_log_kb_complete()
        test_log_kb_read_success()
        test_all_logger_methods()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
