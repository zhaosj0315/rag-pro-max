#!/usr/bin/env python3
"""
UI组件功能测试
测试用户界面组件的核心功能和接口
"""

import os
import sys
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestUIComponents(unittest.TestCase):
    """UI组件功能测试"""
    
    def test_display_components(self):
        """测试显示组件"""
        from src.ui.display_components import render_source_references, render_message_stats
        
        # 验证函数存在
        self.assertTrue(callable(render_source_references))
        self.assertTrue(callable(render_message_stats))
    
    def test_model_selectors(self):
        """测试模型选择器"""
        from src.ui.model_selectors import render_ollama_model_selector, render_openai_model_selector
        
        # 验证函数存在
        self.assertTrue(callable(render_ollama_model_selector))
        self.assertTrue(callable(render_openai_model_selector))
    
    def test_config_forms(self):
        """测试配置表单"""
        from src.ui.config_forms import render_basic_config
        
        # 验证函数存在
        self.assertTrue(callable(render_basic_config))
    
    def test_monitoring_dashboard(self):
        """测试监控仪表板"""
        try:
            from src.ui.monitoring_dashboard import render_system_monitor
            
            # 验证函数存在
            self.assertTrue(callable(render_system_monitor))
        except ImportError:
            self.skipTest("监控仪表板模块不存在")
    
    def test_progress_tracker(self):
        """测试进度追踪器"""
        from src.ui.progress_tracker import ProgressTracker
        
        # 验证类存在
        self.assertTrue(callable(ProgressTracker))
        
        # 测试初始化
        tracker = ProgressTracker()
        self.assertIsNotNone(tracker)
    
    def test_message_renderer(self):
        """测试消息渲染器"""
        from src.ui.message_renderer import MessageRenderer
        
        # 验证类存在
        self.assertTrue(callable(MessageRenderer))
    
    def test_page_style(self):
        """测试页面样式"""
        from src.ui.page_style import PageStyle
        
        # 验证类存在
        self.assertTrue(callable(PageStyle))

def run_ui_component_tests():
    """运行UI组件测试"""
    print("=" * 60)
    print("  UI组件功能测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUIComponents)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_ui_component_tests()
    sys.exit(0 if success else 1)
