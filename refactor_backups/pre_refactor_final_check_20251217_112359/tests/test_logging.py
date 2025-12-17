"""日志系统单元测试"""

import unittest
import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logging import LogManager


class TestLogManager(unittest.TestCase):
    """日志管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.logger = LogManager(log_dir=self.test_dir, enable_terminal=False)
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_init(self):
        """测试初始化"""
        self.assertTrue(os.path.exists(self.test_dir))
        # 日志文件在第一次写入时创建
        self.logger.info("Test")
        self.assertTrue(os.path.exists(self.logger.log_file))
    
    def test_log_levels(self):
        """测试日志级别"""
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.success("Success message")
        
        # 验证日志文件
        with open(self.logger.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 5)
        
        levels = [json.loads(line)['level'] for line in lines]
        self.assertEqual(levels, ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'SUCCESS'])
    
    def test_log_with_stage(self):
        """测试带阶段的日志"""
        self.logger.info("Test message", stage="TestStage")
        
        with open(self.logger.log_file, 'r', encoding='utf-8') as f:
            entry = json.loads(f.readline())
        
        self.assertEqual(entry['stage'], "TestStage")
        self.assertEqual(entry['message'], "Test message")
    
    def test_log_with_details(self):
        """测试带详情的日志"""
        details = {"key": "value", "count": 42}
        self.logger.info("Test message", details=details)
        
        with open(self.logger.log_file, 'r', encoding='utf-8') as f:
            entry = json.loads(f.readline())
        
        self.assertEqual(entry['details'], details)
    
    def test_timer(self):
        """测试计时器"""
        import time
        
        self.logger.start_timer("test")
        time.sleep(0.1)
        elapsed = self.logger.end_timer("test")
        
        self.assertGreater(elapsed, 0.09)
        self.assertLess(elapsed, 0.2)
    
    def test_timer_context(self):
        """测试计时上下文"""
        import time
        
        with self.logger.timer("test_context", log_result=False):
            time.sleep(0.1)
        
        # 验证没有崩溃
        self.assertTrue(True)
    
    def test_stage_context(self):
        """测试阶段上下文"""
        with self.logger.stage("TestStage"):
            self.logger.info("Inside stage")
        
        with open(self.logger.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        self.assertEqual(len(lines), 3)  # 开始 + 内部 + 完成
        
        first = json.loads(lines[0])
        last = json.loads(lines[2])
        
        self.assertIn("开始", first['message'])
        self.assertIn("完成", last['message'])
    
    def test_get_log_file(self):
        """测试获取日志文件路径"""
        log_file = self.logger.get_log_file()
        self.assertTrue(log_file.endswith('.jsonl'))
        
        # 写入后文件存在
        self.logger.info("Test")
        self.assertTrue(os.path.exists(log_file))
    
    def test_global_logger(self):
        """测试全局日志管理器"""
        from src.logging.log_manager import get_logger, set_logger
        
        # 重置全局logger
        import src.logging.log_manager as lm
        lm._global_logger = None
        
        logger1 = get_logger()
        logger2 = get_logger()
        
        self.assertIs(logger1, logger2)
        
        new_logger = LogManager(log_dir=self.test_dir, enable_terminal=False)
        set_logger(new_logger)
        
        logger3 = get_logger()
        self.assertIs(logger3, new_logger)


def run_tests():
    """运行测试"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLogManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
