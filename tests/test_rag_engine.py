#!/usr/bin/env python3
"""
RAG引擎功能测试
测试RAG引擎的核心功能和接口
"""

import os
import sys
import tempfile
import unittest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestRAGEngine(unittest.TestCase):
    """RAG引擎功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_rag_engine_creation(self):
        """测试RAG引擎创建"""
        from src.rag_engine import create_rag_engine
        
        # 验证函数存在
        self.assertTrue(callable(create_rag_engine))
    
    def test_query_processor(self):
        """测试查询处理器"""
        from src.query.query_processor import QueryProcessor
        
        processor = QueryProcessor()
        
        # 验证初始化
        self.assertIsNotNone(processor)
    
    def test_query_rewriter(self):
        """测试查询重写器"""
        from src.query.query_rewriter import QueryRewriter
        
        rewriter = QueryRewriter()
        
        # 验证初始化
        self.assertIsNotNone(rewriter)
    
    def test_query_handler(self):
        """测试查询处理器"""
        from src.query.query_handler import QueryHandler
        
        handler = QueryHandler()
        
        # 验证初始化
        self.assertIsNotNone(handler)
    
    def test_chat_engine(self):
        """测试聊天引擎"""
        from src.chat.chat_engine import ChatEngine
        
        # 验证类存在
        self.assertTrue(callable(ChatEngine))

def run_rag_engine_tests():
    """运行RAG引擎测试"""
    print("=" * 60)
    print("  RAG引擎功能测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRAGEngine)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_rag_engine_tests()
    sys.exit(0 if success else 1)
