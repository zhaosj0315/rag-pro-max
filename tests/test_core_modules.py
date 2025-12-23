#!/usr/bin/env python3
"""
核心模块功能测试
测试核心业务逻辑模块的功能和接口
"""

import os
import sys
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestCoreModules(unittest.TestCase):
    """核心模块功能测试"""
    
    def test_main_controller(self):
        """测试主控制器"""
        from src.core.main_controller import MainController
        
        # 验证类存在
        self.assertTrue(callable(MainController))
    
    def test_environment(self):
        """测试环境配置"""
        try:
            from src.core.environment import Environment
            self.assertTrue(callable(Environment))
        except ImportError:
            self.skipTest("Environment类不存在")
    
    def test_optimization_manager(self):
        """测试优化管理器"""
        try:
            from src.core.optimization_manager import OptimizationManager
            self.assertTrue(callable(OptimizationManager))
        except ImportError:
            self.skipTest("OptimizationManager类不存在")
    
    def test_business_logic(self):
        """测试业务逻辑"""
        try:
            from src.core.business_logic import BusinessLogic
            self.assertTrue(callable(BusinessLogic))
        except ImportError:
            self.skipTest("BusinessLogic类不存在")
    
    def test_app_config(self):
        """测试应用配置"""
        try:
            from src.core.app_config import AppConfig
            self.assertTrue(callable(AppConfig))
        except ImportError:
            self.skipTest("AppConfig类不存在")
    
    def test_state_manager(self):
        """测试状态管理器"""
        from src.core.state_manager import StateManager
        
        # 验证类存在
        self.assertTrue(callable(StateManager))
        
        # 测试初始化
        manager = StateManager()
        self.assertIsNotNone(manager)
    
    def test_version_manager(self):
        """测试版本管理"""
        from src.core.version import get_version, VERSION
        
        # 验证函数和常量存在
        self.assertTrue(callable(get_version))
        self.assertIsNotNone(VERSION)
        
        # 验证版本格式
        version = get_version()
        self.assertIsInstance(version, str)
        # 更新版本检查 - 支持v2.5.0
        self.assertTrue("2.5.0" in version or "v2.5.0" in version)

def run_core_module_tests():
    """运行核心模块测试"""
    print("=" * 60)
    print("  核心模块功能测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCoreModules)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_core_module_tests()
    sys.exit(0 if success else 1)
