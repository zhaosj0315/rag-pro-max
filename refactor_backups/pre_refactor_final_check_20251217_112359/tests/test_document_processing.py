#!/usr/bin/env python3
"""
文档处理功能测试
测试文档处理的核心功能和接口
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestDocumentProcessing(unittest.TestCase):
    """文档处理功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_load_single_file_optimized(self):
        """测试单文件加载优化函数"""
        from src.file_processor import load_single_file_optimized
        
        # 创建测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("这是一个测试文档，包含中文内容。\nThis is a test document with English content.")
        
        # 测试文件加载
        result = load_single_file_optimized((test_file, "test.txt", ".txt"))
        
        # 验证结果
        self.assertIsNotNone(result)
        docs, filename, status, message, mode = result
        self.assertEqual(status, 'success')
        self.assertGreater(len(docs), 0)
        self.assertIn("测试文档", docs[0].text)
    
    def test_scan_directory_safe(self):
        """测试安全目录扫描函数"""
        from src.file_processor import scan_directory_safe
        
        # 创建测试文件
        test_files = ["doc1.txt", "doc2.txt", "doc3.md"]
        for filename in test_files:
            filepath = os.path.join(self.test_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"内容 of {filename}")
        
        # 测试目录扫描
        docs, result = scan_directory_safe(self.test_dir)
        
        # 验证结果
        self.assertGreater(len(docs), 0)
        summary = result.get_summary()
        self.assertGreater(summary['success'], 0)
    
    def test_pdf_page_reader(self):
        """测试PDF页码读取器"""
        from src.utils.pdf_page_reader import PDFPageReader
        
        reader = PDFPageReader()
        
        # 验证初始化
        self.assertIsNotNone(reader)
        self.assertEqual(reader.supported_suffixes, ['.pdf'])
        
        # 测试错误处理
        with self.assertRaises(FileNotFoundError):
            reader.load_data("/nonexistent/file.pdf")
    
    def test_multimodal_processor(self):
        """测试多模态处理器"""
        from src.processors.multimodal_processor import MultimodalProcessor
        
        processor = MultimodalProcessor()
        
        # 验证初始化
        self.assertIsNotNone(processor)
        self.assertIn('.jpg', processor.supported_image_formats)
        self.assertIn('.pdf', processor.supported_table_formats)
        
        # 测试文件类型检测
        self.assertEqual(processor.detect_file_type("test.jpg"), 'image')
        self.assertEqual(processor.detect_file_type("test.pdf"), 'pdf_multimodal')
        self.assertEqual(processor.detect_file_type("test.txt"), 'text')

def run_document_processing_tests():
    """运行文档处理测试"""
    print("=" * 60)
    print("  文档处理功能测试")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDocumentProcessing)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_document_processing_tests()
    sys.exit(0 if success else 1)
