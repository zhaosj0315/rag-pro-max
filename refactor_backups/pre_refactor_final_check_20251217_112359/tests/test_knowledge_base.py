#!/usr/bin/env python3
"""
知识库管理功能测试
测试知识库管理的核心功能和接口
"""

import os
import sys
import tempfile
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestKnowledgeBase(unittest.TestCase):
    """知识库管理功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_kb_manager(self):
        """测试知识库管理器"""
        from src.kb.kb_manager import KBManager
        
        manager = KBManager()
        
        # 验证初始化
        self.assertIsNotNone(manager)
    
    def test_kb_loader(self):
        """测试知识库加载器"""
        from src.kb.kb_loader import KnowledgeBaseLoader
        
        loader = KnowledgeBaseLoader(self.test_dir)
        
        # 验证初始化
        self.assertIsNotNone(loader)
        self.assertEqual(loader.output_base, self.test_dir)
    
    def test_kb_processor(self):
        """测试知识库处理器"""
        from src.kb.kb_processor import KnowledgeBaseProcessor
        
        processor = KnowledgeBaseProcessor()
        
        # 验证初始化
        self.assertIsNotNone(processor)
    
    def test_kb_operations(self):
        """测试知识库操作"""
        from src.kb.kb_operations import KBOperations
        
        operations = KBOperations()
        
        # 验证初始化
        self.assertIsNotNone(operations)
    
    def test_document_viewer(self):
        """测试文档查看器"""
        from src.kb.document_viewer import DocumentViewer
        
        viewer = DocumentViewer()
        
        # 验证初始化
        self.assertIsNotNone(viewer)
    
    def test_incremental_updater(self):
        """测试增量更新器"""
        from src.kb.incremental_updater import IncrementalUpdater
        
        updater = IncrementalUpdater()
        
        # 验证初始化
        self.assertIsNotNone(updater)

def run_knowledge_base_tests():
    """运行知识库管理测试"""
    print("=" * 60)
    print("  知识库管理功能测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKnowledgeBase)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_knowledge_base_tests()
    sys.exit(0 if success else 1)
