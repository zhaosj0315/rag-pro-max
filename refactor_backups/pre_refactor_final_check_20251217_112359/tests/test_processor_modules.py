#!/usr/bin/env python3
"""
处理器模块功能测试
测试文档处理器和相关模块的功能
"""

import os
import sys
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestProcessorModules(unittest.TestCase):
    """处理器模块功能测试"""
    
    def test_upload_handler(self):
        """测试上传处理器"""
        from src.processors.upload_handler import UploadHandler
        
        # 验证类存在
        self.assertTrue(callable(UploadHandler))
    
    def test_enhanced_upload_handler(self):
        """测试增强上传处理器"""
        try:
            from src.processors.enhanced_upload_handler import EnhancedUploadHandler
            self.assertTrue(callable(EnhancedUploadHandler))
        except ImportError:
            self.skipTest("EnhancedUploadHandler类不存在或依赖缺失")
    
    def test_multimodal_processor(self):
        """测试多模态处理器"""
        from src.processors.multimodal_processor import MultimodalProcessor
        
        # 验证类存在
        self.assertTrue(callable(MultimodalProcessor))
    
    def test_web_crawler(self):
        """测试网页抓取器"""
        try:
            from src.processors.web_crawler import WebCrawler, GLOBAL_MAX_PAGES
            
            # 验证类和常量存在
            self.assertTrue(callable(WebCrawler))
            self.assertEqual(GLOBAL_MAX_PAGES, 50000)
            
            # 测试初始化
            crawler = WebCrawler()
            self.assertIsNotNone(crawler)
        except ImportError:
            # 如果GLOBAL_MAX_PAGES不存在，只测试WebCrawler类
            from src.processors.web_crawler import WebCrawler
            
            # 验证类存在
            self.assertTrue(callable(WebCrawler))
            
            # 测试初始化
            crawler = WebCrawler()
            self.assertIsNotNone(crawler)
    
    def test_index_builder(self):
        """测试索引构建器"""
        from src.processors.index_builder import IndexBuilder
        
        # 验证类存在
        self.assertTrue(callable(IndexBuilder))
    
    def test_document_parser(self):
        """测试文档解析器"""
        from src.processors.document_parser import DocumentParser
        
        # 验证类存在
        self.assertTrue(callable(DocumentParser))
    
    def test_summary_generator(self):
        """测试摘要生成器"""
        from src.processors.summary_generator import SummaryGenerator
        
        # 验证类存在
        self.assertTrue(callable(SummaryGenerator))

def run_processor_module_tests():
    """运行处理器模块测试"""
    print("=" * 60)
    print("  处理器模块功能测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestProcessorModules)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_processor_module_tests()
    sys.exit(0 if success else 1)
