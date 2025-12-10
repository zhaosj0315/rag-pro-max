"""
RAG Pro Max v2.0 功能测试
测试增量更新、API扩展、多模态支持
"""

import unittest
import tempfile
import os
import json
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入要测试的模块
try:
    from src.kb.incremental_updater import IncrementalUpdater
    from src.processors.multimodal_processor import MultimodalProcessor
    from src.core.v2_integration import V2Integration
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"模块导入失败: {e}")
    MODULES_AVAILABLE = False


class TestIncrementalUpdater(unittest.TestCase):
    """测试增量更新功能"""
    
    def setUp(self):
        if not MODULES_AVAILABLE:
            self.skipTest("模块不可用")
        
        self.temp_dir = tempfile.mkdtemp()
        self.updater = IncrementalUpdater(self.temp_dir)
    
    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_file_hash_calculation(self):
        """测试文件哈希计算"""
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # 计算哈希
        hash1 = self.updater._calculate_file_hash(test_file)
        self.assertIsInstance(hash1, str)
        self.assertEqual(len(hash1), 32)  # MD5哈希长度
        
        # 相同内容应该产生相同哈希
        hash2 = self.updater._calculate_file_hash(test_file)
        self.assertEqual(hash1, hash2)
    
    def test_change_detection(self):
        """测试文件变化检测"""
        # 创建测试文件
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("original content")
        
        # 首次检测应该是新文件
        changes = self.updater.get_changed_files([test_file])
        self.assertIn(test_file, changes['new'])
        
        # 标记为已处理
        self.updater.mark_files_processed([test_file])
        
        # 再次检测应该是未变化
        changes = self.updater.get_changed_files([test_file])
        self.assertIn(test_file, changes['unchanged'])
        
        # 修改文件
        with open(test_file, 'w') as f:
            f.write("modified content")
        
        # 检测应该发现修改
        changes = self.updater.get_changed_files([test_file])
        self.assertIn(test_file, changes['modified'])
    
    def test_metadata_persistence(self):
        """测试元数据持久化"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # 标记文件已处理
        self.updater.mark_files_processed([test_file])
        
        # 创建新的更新器实例
        new_updater = IncrementalUpdater(self.temp_dir)
        
        # 应该能加载之前的元数据
        changes = new_updater.get_changed_files([test_file])
        self.assertIn(test_file, changes['unchanged'])


class TestMultimodalProcessor(unittest.TestCase):
    """测试多模态处理功能"""
    
    def setUp(self):
        if not MODULES_AVAILABLE:
            self.skipTest("模块不可用")
        
        self.processor = MultimodalProcessor()
    
    def test_file_type_detection(self):
        """测试文件类型检测"""
        test_cases = [
            ('test.jpg', 'image'),
            ('test.png', 'image'),
            ('test.pdf', 'pdf_multimodal'),
            ('test.xlsx', 'table'),
            ('test.csv', 'table'),
            ('test.txt', 'text')
        ]
        
        for filename, expected_type in test_cases:
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(filename)[1], delete=False) as f:
                detected_type = self.processor.detect_file_type(f.name)
                # PDF文件在supported_table_formats中，但detect_file_type优先返回pdf_multimodal
                if filename == 'test.pdf':
                    self.assertEqual(detected_type, 'pdf_multimodal')
                else:
                    self.assertEqual(detected_type, expected_type)
                os.unlink(f.name)
    
    def test_supported_formats(self):
        """测试支持格式查询"""
        formats = self.processor.get_supported_formats()
        
        self.assertIn('images', formats)
        self.assertIn('tables', formats)
        self.assertIn('ocr_available', formats)
        self.assertIn('table_extraction_available', formats)
        
        self.assertIsInstance(formats['images'], list)
        self.assertIsInstance(formats['tables'], list)
        self.assertIsInstance(formats['ocr_available'], bool)
        self.assertIsInstance(formats['table_extraction_available'], bool)
    
    @patch('src.processors.multimodal_processor.HAS_OCR', True)
    @patch('src.processors.multimodal_processor.pytesseract')
    @patch('src.processors.multimodal_processor.Image')
    def test_image_ocr_mock(self, mock_image, mock_pytesseract):
        """测试图片OCR（模拟）"""
        # 模拟OCR结果
        mock_pytesseract.image_to_string.return_value = "测试文字"
        mock_pytesseract.image_to_data.return_value = {'conf': ['90', '85', '95']}
        mock_pytesseract.Output.DICT = 'dict'
        
        # 模拟图片
        mock_img = Mock()
        mock_img.size = (800, 600)
        mock_img.format = 'JPEG'
        mock_image.open.return_value = mock_img
        
        # 创建临时图片文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(b'fake image data')
            temp_path = f.name
        
        try:
            result = self.processor.extract_text_from_image(temp_path)
            
            self.assertEqual(result['text'], '测试文字')
            self.assertGreater(result['confidence'], 0)
            self.assertEqual(result['image_size'], (800, 600))
            self.assertEqual(result['format'], 'JPEG')
            
        finally:
            os.unlink(temp_path)


class TestV2Integration(unittest.TestCase):
    """测试v2.0集成功能"""
    
    def setUp(self):
        if not MODULES_AVAILABLE:
            self.skipTest("模块不可用")
        
        self.integration = V2Integration()
    
    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.integration.kb_manager)
        self.assertIsNotNone(self.integration.multimodal_processor)
    
    @patch('streamlit.warning')
    @patch('streamlit.subheader')
    def test_incremental_ui_no_kb(self, mock_subheader, mock_warning):
        """测试增量更新UI（无知识库）"""
        self.integration.render_incremental_update_ui("")
        mock_warning.assert_called_once_with("请先选择知识库")
    
    @patch('streamlit.warning')
    @patch('streamlit.subheader')
    def test_multimodal_ui_no_kb(self, mock_subheader, mock_warning):
        """测试多模态UI（无知识库）"""
        self.integration.render_multimodal_ui("")
        mock_warning.assert_called_once_with("请先选择知识库")


def run_v2_tests():
    """运行v2.0功能测试"""
    print("=" * 60)
    print("  RAG Pro Max v2.0 功能测试")
    print("=" * 60)
    
    if not MODULES_AVAILABLE:
        print("❌ 模块导入失败，跳过测试")
        return False
    
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加测试用例
    test_classes = [
        TestIncrementalUpdater,
        TestMultimodalProcessor,
        TestV2Integration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
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
        print("\n✅ 所有v2.0功能测试通过！")
        return True
    else:
        print(f"\n❌ 发现 {failures + errors} 个问题")
        return False


if __name__ == "__main__":
    run_v2_tests()
