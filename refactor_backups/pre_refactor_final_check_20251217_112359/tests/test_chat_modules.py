"""
聊天模块测试
Stage 7 - 测试聊天引擎和建议管理器
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.chat.suggestion_manager import SuggestionManager


class MockSessionState(dict):
    """Mock Streamlit session_state"""
    def __getattr__(self, key):
        return self.get(key)
    
    def __setattr__(self, key, value):
        self[key] = value


class TestSuggestionManager(unittest.TestCase):
    """测试追问建议管理器"""
    
    def setUp(self):
        """测试前准备"""
        self.patcher = patch('src.chat.suggestion_manager.st')
        self.mock_st = self.patcher.start()
        self.mock_st.session_state = MockSessionState()
    
    def tearDown(self):
        """测试后清理"""
        self.patcher.stop()
    
    def test_get_suggestions_history_empty(self):
        """测试获取空的追问历史"""
        history = SuggestionManager.get_suggestions_history()
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 0)
    
    def test_get_suggestions_history_existing(self):
        """测试获取已有的追问历史"""
        self.mock_st.session_state['suggestions_history'] = ['问题1', '问题2']
        history = SuggestionManager.get_suggestions_history()
        self.assertEqual(len(history), 2)
        self.assertIn('问题1', history)
    
    def test_add_suggestions(self):
        """测试添加追问建议"""
        SuggestionManager.add_suggestions(['新问题1', '新问题2'])
        history = self.mock_st.session_state['suggestions_history']
        self.assertEqual(len(history), 2)
    
    def test_add_suggestions_dedup(self):
        """测试添加追问建议（去重）"""
        self.mock_st.session_state['suggestions_history'] = ['问题1']
        SuggestionManager.add_suggestions(['问题1', '问题2'])
        history = self.mock_st.session_state['suggestions_history']
        # 问题1 应该被去重
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1], '问题2')
    
    def test_clear_suggestions(self):
        """测试清空追问历史"""
        self.mock_st.session_state['suggestions_history'] = ['问题1', '问题2']
        SuggestionManager.clear_suggestions()
        self.assertEqual(len(self.mock_st.session_state['suggestions_history']), 0)


class TestChatEngineIntegration(unittest.TestCase):
    """测试聊天引擎集成（轻量级测试）"""
    
    def test_chat_engine_import(self):
        """测试聊天引擎模块导入"""
        try:
            from src.chat.chat_engine import ChatEngine
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"导入失败: {e}")
    
    def test_chat_engine_init(self):
        """测试聊天引擎初始化"""
        from src.chat.chat_engine import ChatEngine
        
        mock_engine = Mock()
        chat_engine = ChatEngine(mock_engine, "test_kb")
        
        self.assertEqual(chat_engine.kb_name, "test_kb")
        self.assertIsNotNone(chat_engine.executor)


if __name__ == '__main__':
    unittest.main()
