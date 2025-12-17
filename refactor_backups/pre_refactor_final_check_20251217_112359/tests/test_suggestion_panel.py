"""
推荐问题面板单元测试
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestSuggestionPanel(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.mock_messages = [
            {"role": "user", "content": "什么是Python？"},
            {"role": "assistant", "content": "Python是一种编程语言..."}
        ]
        self.mock_chat_engine = Mock()
        self.mock_chat_engine._llm = Mock()
    
    @patch('streamlit.session_state')
    @patch('streamlit.divider')
    @patch('streamlit.markdown')
    @patch('streamlit.button')
    def test_show_suggestions_with_history(self, mock_button, mock_markdown, mock_divider, mock_session_state):
        """测试显示历史推荐问题"""
        # 模拟session_state
        mock_session_state.get.return_value = ["问题1", "问题2", "问题3"]
        mock_button.return_value = False
        
        from src.ui.suggestion_panel import show_suggestions_panel
        
        result = show_suggestions_panel("test_kb", self.mock_chat_engine, self.mock_messages)
        
        # 验证调用
        mock_divider.assert_called_once()
        mock_markdown.assert_called_with("##### 🚀 追问推荐")
        self.assertEqual(mock_button.call_count, 4)  # 3个问题 + 1个继续推荐按钮
        self.assertIsNone(result)
    
    @patch('streamlit.session_state')
    def test_show_suggestions_no_messages(self, mock_session_state):
        """测试无消息时不显示推荐"""
        from src.ui.suggestion_panel import show_suggestions_panel
        
        result = show_suggestions_panel("test_kb", self.mock_chat_engine, [])
        self.assertIsNone(result)
    
    @patch('streamlit.session_state')
    def test_show_suggestions_no_assistant_message(self, mock_session_state):
        """测试最后一条不是assistant消息时不显示推荐"""
        from src.ui.suggestion_panel import show_suggestions_panel
        
        user_only_messages = [{"role": "user", "content": "测试"}]
        result = show_suggestions_panel("test_kb", self.mock_chat_engine, user_only_messages)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
