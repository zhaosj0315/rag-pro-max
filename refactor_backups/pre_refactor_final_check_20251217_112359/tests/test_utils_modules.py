#!/usr/bin/env python3
"""
工具模块功能测试
测试工具类模块的功能和接口
"""

import os
import sys
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestUtilsModules(unittest.TestCase):
    """工具模块功能测试"""
    
    def test_model_manager(self):
        """测试模型管理器"""
        try:
            from src.utils.model_manager import ModelManager
            self.assertTrue(callable(ModelManager))
        except ImportError:
            self.skipTest("ModelManager类不存在")
    
    def test_resource_monitor(self):
        """测试资源监控器"""
        try:
            from src.utils.resource_monitor import ResourceMonitor
            self.assertTrue(callable(ResourceMonitor))
            
            # 测试初始化
            monitor = ResourceMonitor()
            self.assertIsNotNone(monitor)
        except ImportError:
            self.skipTest("ResourceMonitor类不存在")
    
    def test_gpu_optimizer(self):
        """测试GPU优化器"""
        from src.utils.gpu_optimizer import GPUOptimizer
        
        # 验证类存在
        self.assertTrue(callable(GPUOptimizer))
    
    def test_enhanced_cache(self):
        """测试增强缓存"""
        try:
            from src.utils.enhanced_cache import EnhancedCache
            self.assertTrue(callable(EnhancedCache))
        except ImportError:
            self.skipTest("EnhancedCache类不存在")
    
    def test_parallel_executor(self):
        """测试并行执行器"""
        from src.utils.parallel_executor import ParallelExecutor
        
        # 验证类存在
        self.assertTrue(callable(ParallelExecutor))
    
    def test_app_utils(self):
        """测试应用工具"""
        try:
            from src.utils.app_utils import AppUtils
            self.assertTrue(callable(AppUtils))
        except ImportError:
            self.skipTest("AppUtils类不存在")
    
    def test_pdf_page_reader(self):
        """测试PDF页码读取器"""
        from src.utils.pdf_page_reader import PDFPageReader
        
        # 验证类存在
        self.assertTrue(callable(PDFPageReader))
        
        # 测试初始化
        reader = PDFPageReader()
        self.assertIsNotNone(reader)
    
    def test_safe_parallel_tasks(self):
        """测试安全并行任务"""
        try:
            from src.utils.safe_parallel_tasks import process_node_worker
            self.assertTrue(callable(process_node_worker))
        except ImportError:
            self.skipTest("process_node_worker函数不存在")

def run_utils_module_tests():
    """运行工具模块测试"""
    print("=" * 60)
    print("  工具模块功能测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUtilsModules)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_utils_module_tests()
    sys.exit(0 if success else 1)
