#!/usr/bin/env python3
"""
Stage 15 重构模块测试
测试新提取的环境配置、消息渲染、自动摘要和主控制器模块
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestStage15Modules(unittest.TestCase):
    """Stage 15 重构模块测试"""
    
    def test_environment_module_import(self):
        """测试环境配置模块导入"""
        try:
            from src.core.environment import initialize_environment, setup_environment, suppress_warnings
            self.assertTrue(callable(initialize_environment))
            self.assertTrue(callable(setup_environment))
            self.assertTrue(callable(suppress_warnings))
            print("✅ 环境配置模块导入成功")
        except Exception as e:
            self.fail(f"❌ 环境配置模块导入失败: {e}")
    
    def test_message_renderer_import(self):
        """测试消息渲染器导入"""
        try:
            from src.ui.message_renderer import MessageRenderer
            self.assertTrue(hasattr(MessageRenderer, 'render_messages'))
            self.assertTrue(hasattr(MessageRenderer, 'render_quote_preview'))
            print("✅ 消息渲染器导入成功")
        except Exception as e:
            self.fail(f"❌ 消息渲染器导入失败: {e}")
    
    def test_auto_summary_import(self):
        """测试自动摘要模块导入"""
        try:
            from src.summary.auto_summary import AutoSummaryGenerator
            self.assertTrue(hasattr(AutoSummaryGenerator, 'should_generate_summary'))
            self.assertTrue(hasattr(AutoSummaryGenerator, 'generate_summary'))
            print("✅ 自动摘要模块导入成功")
        except Exception as e:
            self.fail(f"❌ 自动摘要模块导入失败: {e}")
    
    def test_main_controller_import(self):
        """测试主控制器导入"""
        try:
            from src.core.main_controller import MainController
            controller = MainController("/tmp")
            self.assertIsNotNone(controller)
            self.assertTrue(hasattr(controller, 'handle_kb_loading'))
            self.assertTrue(hasattr(controller, 'handle_queue_processing'))
            print("✅ 主控制器导入成功")
        except Exception as e:
            self.fail(f"❌ 主控制器导入失败: {e}")
    
    def test_environment_setup(self):
        """测试环境设置功能"""
        try:
            from src.core.environment import setup_environment
            import os
            
            # 测试环境设置
            setup_environment()
            
            # 验证环境变量
            self.assertEqual(os.environ.get('HF_HUB_OFFLINE'), '1')
            self.assertEqual(os.environ.get('TRANSFORMERS_OFFLINE'), '1')
            self.assertEqual(os.environ.get('TOKENIZERS_PARALLELISM'), 'false')
            
            print("✅ 环境设置功能正常")
        except Exception as e:
            self.fail(f"❌ 环境设置功能失败: {e}")
    
    def test_auto_summary_should_generate(self):
        """测试自动摘要判断逻辑"""
        try:
            from src.summary.auto_summary import AutoSummaryGenerator
            
            # 测试应该生成摘要的情况
            should_generate = AutoSummaryGenerator.should_generate_summary(
                "test_kb", Mock(), []
            )
            self.assertTrue(should_generate)
            
            # 测试不应该生成摘要的情况
            should_generate = AutoSummaryGenerator.should_generate_summary(
                "test_kb", Mock(), [{"role": "user", "content": "test"}]
            )
            self.assertFalse(should_generate)
            
            print("✅ 自动摘要判断逻辑正常")
        except Exception as e:
            self.fail(f"❌ 自动摘要判断逻辑失败: {e}")
    
    def test_main_controller_initialization(self):
        """测试主控制器初始化"""
        try:
            from src.core.main_controller import MainController
            
            controller = MainController("/tmp/test")
            
            # 验证属性
            self.assertEqual(controller.output_base, "/tmp/test")
            self.assertIsNotNone(controller.kb_loader)
            self.assertIsNotNone(controller.query_processor)
            self.assertIsNotNone(controller.queue_manager)
            
            print("✅ 主控制器初始化正常")
        except Exception as e:
            self.fail(f"❌ 主控制器初始化失败: {e}")
    
    def test_module_integration(self):
        """测试模块集成"""
        try:
            # 测试所有新模块能否同时导入
            from src.core.environment import initialize_environment
            from src.ui.message_renderer import MessageRenderer
            from src.summary.auto_summary import AutoSummaryGenerator
            from src.core.main_controller import MainController
            
            print("✅ Stage 15 所有模块集成正常")
        except Exception as e:
            self.fail(f"❌ Stage 15 模块集成失败: {e}")

def run_tests():
    """运行测试"""
    print("=" * 60)
    print("  Stage 15 重构模块测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestStage15Modules)
    
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
        print("\n🎉 所有测试通过！Stage 15 模块重构成功。")
        return True
    else:
        print(f"\n⚠️ 发现 {failures + errors} 个问题，需要修复。")
        
        # 显示详细错误信息
        if result.failures:
            print("\n失败详情:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\n错误详情:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
        
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
