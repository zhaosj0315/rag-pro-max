"""聊天历史管理器单元测试"""

import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.chat import HistoryManager


class TestHistoryManager(unittest.TestCase):
    """历史管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.original_dir = HistoryManager.HISTORY_DIR
        HistoryManager.HISTORY_DIR = self.test_dir
    
    def tearDown(self):
        """测试后清理"""
        HistoryManager.HISTORY_DIR = self.original_dir
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_load_empty(self):
        """测试加载空历史"""
        messages = HistoryManager.load("test_kb")
        self.assertEqual(messages, [])
    
    def test_save_and_load(self):
        """测试保存和加载"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        success = HistoryManager.save("test_kb", messages)
        self.assertTrue(success)
        
        loaded = HistoryManager.load("test_kb")
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0]["content"], "Hello")
        self.assertEqual(loaded[1]["content"], "Hi there!")
    
    def test_clear(self):
        """测试清空历史"""
        messages = [{"role": "user", "content": "Test"}]
        HistoryManager.save("test_kb", messages)
        
        self.assertTrue(HistoryManager.exists("test_kb"))
        
        success = HistoryManager.clear("test_kb")
        self.assertTrue(success)
        self.assertFalse(HistoryManager.exists("test_kb"))
    
    def test_exists(self):
        """测试存在检查"""
        self.assertFalse(HistoryManager.exists("test_kb"))
        
        HistoryManager.save("test_kb", [{"role": "user", "content": "Test"}])
        self.assertTrue(HistoryManager.exists("test_kb"))
    
    def test_multiple_kb(self):
        """测试多个知识库"""
        messages1 = [{"role": "user", "content": "KB1"}]
        messages2 = [{"role": "user", "content": "KB2"}]
        
        HistoryManager.save("kb1", messages1)
        HistoryManager.save("kb2", messages2)
        
        loaded1 = HistoryManager.load("kb1")
        loaded2 = HistoryManager.load("kb2")
        
        self.assertEqual(loaded1[0]["content"], "KB1")
        self.assertEqual(loaded2[0]["content"], "KB2")


def run_tests():
    """运行测试"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHistoryManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
