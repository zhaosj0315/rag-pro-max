"""日志模块测试"""

import os
import sys
import tempfile
import shutil
import time
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.logging import LogManager


class TestLogManager:
    """测试 LogManager 类"""
    
    def __init__(self):
        self.temp_dir = None
        self.logger = None
    
    def setup(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = LogManager(log_dir=self.temp_dir, enable_terminal=False)
        return True
    
    def teardown(self):
        """测试后清理"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        return True
    
    def test_init(self):
        """测试初始化"""
        assert self.logger is not None, "日志管理器创建失败"
        assert os.path.exists(self.temp_dir), "日志目录不存在"
        assert os.path.exists(self.logger.log_file), "日志文件不存在"
        return True
    
    def test_log_levels(self):
        """测试日志级别"""
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.success("Success message")
        
        # 读取日志文件
        with open(self.logger.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 5, f"日志条数错误: {len(lines)}"
        
        # 验证每条日志
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'SUCCESS']
        for i, line in enumerate(lines):
            entry = json.loads(line)
            assert entry['level'] == levels[i], f"日志级别错误: {entry['level']}"
        
        return True
    
    def test_log_with_stage(self):
        """测试带阶段的日志"""
        self.logger.info("Test message", stage="TestStage")
        
        with open(self.logger.log_file, 'r', encoding='utf-8') as f:
            entry = json.loads(f.readline())
        
        assert entry['stage'] == "TestStage", "阶段信息错误"
        assert entry['message'] == "Test message", "消息内容错误"
        
        return True
    
    def test_log_with_details(self):
        """测试带详情的日志"""
        details = {"key1": "value1", "key2": 123}
        self.logger.info("Test message", details=details)
        
        with open(self.logger.log_file, 'r', encoding='utf-8') as f:
            entry = json.loads(f.readline())
        
        assert entry['details'] == details, "详情信息错误"
        
        return True
    
    def test_timer(self):
        """测试计时器"""
        self.logger.start_timer("test")
        time.sleep(0.1)
        elapsed = self.logger.end_timer("test")
        
        assert elapsed >= 0.1, f"计时错误: {elapsed}"
        assert elapsed < 0.2, f"计时误差过大: {elapsed}"
        
        return True
    
    def test_timer_context(self):
        """测试计时上下文"""
        with self.logger.timer("test_context", log_result=False):
            time.sleep(0.1)
        
        # 验证没有崩溃即可
        return True
    
    def test_stage_context(self):
        """测试阶段上下文"""
        with self.logger.stage("TestStage"):
            time.sleep(0.05)
        
        # 读取日志
        with open(self.logger.log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        assert len(lines) == 2, f"日志条数错误: {len(lines)}"
        
        start_entry = json.loads(lines[0])
        end_entry = json.loads(lines[1])
        
        assert "开始" in start_entry['message'], "开始消息错误"
        assert "完成" in end_entry['message'], "完成消息错误"
        
        return True
    
    def test_get_log_file(self):
        """测试获取日志文件路径"""
        log_file = self.logger.get_log_file()
        assert log_file == self.logger.log_file, "日志文件路径不匹配"
        assert os.path.exists(log_file), "日志文件不存在"
        
        return True
    
    def test_global_logger(self):
        """测试全局日志管理器"""
        from src.logging.log_manager import get_logger, set_logger
        
        # 获取全局日志
        logger1 = get_logger()
        logger2 = get_logger()
        
        assert logger1 is logger2, "全局日志不是单例"
        
        # 设置新的全局日志
        new_logger = LogManager(log_dir=self.temp_dir, enable_terminal=False)
        set_logger(new_logger)
        
        logger3 = get_logger()
        assert logger3 is new_logger, "设置全局日志失败"
        
        return True


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  日志模块测试")
    print("="*60 + "\n")
    
    tester = TestLogManager()
    test_methods = [m for m in dir(tester) if m.startswith('test_')]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for method_name in test_methods:
        total_tests += 1
        test_name = method_name.replace('test_', '').replace('_', ' ').title()
        
        try:
            tester.setup()
            method = getattr(tester, method_name)
            result = method()
            tester.teardown()
            
            if result:
                print(f"  ✅ {test_name}")
                passed_tests += 1
            else:
                print(f"  ❌ {test_name} - 返回 False")
                failed_tests.append(method_name)
        except Exception as e:
            print(f"  ❌ {test_name} - {str(e)}")
            failed_tests.append(method_name)
            try:
                tester.teardown()
            except:
                pass
    
    # 打印总结
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    print(f"✅ 通过: {passed_tests}/{total_tests}")
    print(f"❌ 失败: {len(failed_tests)}/{total_tests}")
    
    if failed_tests:
        print(f"\n失败的测试:")
        for test in failed_tests:
            print(f"  - {test}")
        print("\n❌ 部分测试失败")
        return False
    else:
        print("\n✅ 所有测试通过！")
        return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
