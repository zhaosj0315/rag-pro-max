#!/usr/bin/env python3
"""
Stage 16 重构模块测试
测试新提取的侧边栏配置、页面样式和工具函数模块
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestStage16Modules(unittest.TestCase):
    """Stage 16 重构模块测试"""
    
    def test_sidebar_config_import(self):
        """测试侧边栏配置模块导入"""
        try:
            from src.ui.sidebar_config import SidebarConfig
            self.assertTrue(hasattr(SidebarConfig, 'render_sidebar'))
            self.assertTrue(hasattr(SidebarConfig, 'extract_config_values'))
            print("✅ 侧边栏配置模块导入成功")
        except Exception as e:
            self.fail(f"❌ 侧边栏配置模块导入失败: {e}")
    
    def test_page_style_import(self):
        """测试页面样式模块导入"""
        try:
            from src.ui.page_style import PageStyle
            self.assertTrue(hasattr(PageStyle, 'setup_page_config'))
            self.assertTrue(hasattr(PageStyle, 'apply_custom_css'))
            self.assertTrue(hasattr(PageStyle, 'setup_page'))
            print("✅ 页面样式模块导入成功")
        except Exception as e:
            self.fail(f"❌ 页面样式模块导入失败: {e}")
    
    def test_app_utils_import(self):
        """测试应用工具函数导入"""
        try:
            from src.utils.app_utils import (
                get_kb_embedding_dim,
                generate_doc_summary,
                initialize_session_state,
                show_first_time_guide,
                handle_kb_switching
            )
            self.assertTrue(callable(get_kb_embedding_dim))
            self.assertTrue(callable(generate_doc_summary))
            self.assertTrue(callable(initialize_session_state))
            print("✅ 应用工具函数导入成功")
        except Exception as e:
            self.fail(f"❌ 应用工具函数导入失败: {e}")
    
    def test_page_style_css_generation(self):
        """测试页面样式 CSS 生成"""
        try:
            from src.ui.page_style import PageStyle
            css = PageStyle._get_custom_css()
            self.assertIsInstance(css, str)
            self.assertIn("<style>", css)
            self.assertIn("</style>", css)
            self.assertIn(".main .block-container", css)
            print("✅ 页面样式 CSS 生成正常")
        except Exception as e:
            self.fail(f"❌ 页面样式 CSS 生成失败: {e}")
    
    def test_kb_embedding_dim_detection(self):
        """测试知识库维度检测"""
        try:
            from src.utils.app_utils import get_kb_embedding_dim
            
            # 测试不存在的路径
            dim = get_kb_embedding_dim("/nonexistent/path")
            self.assertIsNone(dim)
            
            print("✅ 知识库维度检测功能正常")
        except Exception as e:
            self.fail(f"❌ 知识库维度检测失败: {e}")
    
    def test_session_state_initialization(self):
        """测试 session state 初始化"""
        try:
            from src.utils.app_utils import initialize_session_state
            
            # 模拟 streamlit session_state
            class MockSessionState:
                def __init__(self):
                    pass
                
                def __contains__(self, key):
                    return hasattr(self, key)
                
                def __setitem__(self, key, value):
                    setattr(self, key, value)
            
            mock_session_state = MockSessionState()
            
            with patch('streamlit.session_state', mock_session_state):
                initialize_session_state()
                
                # 验证初始化的属性
                self.assertTrue(hasattr(mock_session_state, 'messages'))
                self.assertTrue(hasattr(mock_session_state, 'chat_engine'))
                self.assertTrue(hasattr(mock_session_state, 'question_queue'))
                
            print("✅ Session state 初始化正常")
        except Exception as e:
            self.fail(f"❌ Session state 初始化失败: {e}")
    
    def test_sidebar_config_extract_values(self):
        """测试侧边栏配置值提取"""
        try:
            from src.ui.sidebar_config import SidebarConfig
            
            test_config = {
                'llm_provider': 'OpenAI',
                'llm_url': 'https://api.openai.com/v1',
                'llm_model': 'gpt-3.5-turbo',
                'llm_key': 'test-key',
                'embed_provider': 'HuggingFace',
                'embed_model': 'BAAI/bge-small-zh-v1.5',
                'embed_url': '',
                'embed_key': ''
            }
            
            extracted = SidebarConfig.extract_config_values(test_config)
            
            self.assertEqual(extracted['llm_provider'], 'OpenAI')
            self.assertEqual(extracted['embed_model'], 'BAAI/bge-small-zh-v1.5')
            
            print("✅ 侧边栏配置值提取正常")
        except Exception as e:
            self.fail(f"❌ 侧边栏配置值提取失败: {e}")
    
    def test_module_integration(self):
        """测试模块集成"""
        try:
            # 测试所有新模块能否同时导入
            from src.ui.sidebar_config import SidebarConfig
            from src.ui.page_style import PageStyle
            from src.utils.app_utils import initialize_session_state
            
            print("✅ Stage 16 所有模块集成正常")
        except Exception as e:
            self.fail(f"❌ Stage 16 模块集成失败: {e}")

def run_tests():
    """运行测试"""
    print("=" * 60)
    print("  Stage 16 重构模块测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStage16Modules)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"✅ 通过: {passed}/{total_tests}")
    print(f"❌ 失败: {failures}/{total_tests}")
    print(f"💥 错误: {errors}/{total_tests}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 所有测试通过！Stage 16 模块重构成功。")
        return True
    else:
        print(f"\n⚠️ 发现 {failures + errors} 个问题，需要修复。")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
