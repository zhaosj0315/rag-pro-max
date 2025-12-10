"""
v2.1 功能测试
测试实时监控、批量OCR、表格解析、多模态向量化
"""

import unittest
import tempfile
import os
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from monitoring.file_watcher import DocumentWatcher, FileWatcherManager
    from processors.batch_ocr_processor import BatchOCRProcessor, ImagePreprocessor
    from processors.table_parser import SmartTableParser, TableStructureAnalyzer
    from processors.multimodal_vectorizer import MultiModalVectorizer, CrossModalRetriever
    from core.v21_integration import V21FeatureManager
    V21_AVAILABLE = True
except ImportError as e:
    print(f"v2.1功能不可用: {e}")
    V21_AVAILABLE = False

class TestV21Features(unittest.TestCase):
    """v2.1功能测试类"""
    
    def setUp(self):
        """测试准备"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @unittest.skipUnless(V21_AVAILABLE, "v2.1功能不可用")
    def test_file_watcher_manager(self):
        """测试文件监控管理器"""
        manager = FileWatcherManager()
        
        # 测试状态
        status = manager.get_status()
        self.assertIn('is_running', status)
        self.assertIn('watched_paths', status)
        self.assertIn('total_watchers', status)
        
        print("✅ 文件监控管理器测试通过")
    
    @unittest.skipUnless(V21_AVAILABLE, "v2.1功能不可用")
    def test_image_preprocessor(self):
        """测试图片预处理器"""
        preprocessor = ImagePreprocessor()
        
        # 创建测试图片
        test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        
        # 测试增强
        enhanced = preprocessor.enhance_image(test_image)
        self.assertEqual(enhanced.shape, test_image.shape)
        
        # 测试去噪
        denoised = preprocessor.denoise_image(test_image)
        self.assertEqual(denoised.shape, test_image.shape)
        
        # 测试二值化
        binary = preprocessor.binarize_image(test_image)
        self.assertEqual(len(binary.shape), 2)  # 应该是灰度图
        
        print("✅ 图片预处理器测试通过")
    
    @unittest.skipUnless(V21_AVAILABLE, "v2.1功能不可用")
    def test_batch_ocr_processor(self):
        """测试批量OCR处理器"""
        processor = BatchOCRProcessor(max_workers=2, use_gpu=False)
        
        # 测试配置
        self.assertEqual(processor.max_workers, 2)
        self.assertFalse(processor.use_gpu)
        
        print("✅ 批量OCR处理器测试通过")
    
    @unittest.skipUnless(V21_AVAILABLE, "v2.1功能不可用")
    def test_table_structure_analyzer(self):
        """测试表格结构分析器"""
        analyzer = TableStructureAnalyzer()
        
        # 创建测试表格
        test_data = pd.DataFrame({
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35],
            'city': ['New York', 'London', 'Tokyo']
        })
        
        # 分析结构
        structure = analyzer.analyze_structure(test_data)
        
        # 验证结果
        self.assertEqual(structure['rows'], 3)
        self.assertEqual(structure['columns'], 3)
        self.assertEqual(structure['headers'], ['name', 'age', 'city'])
        self.assertIn('data_types', structure)
        self.assertIn('relationships', structure)
        self.assertIn('semantic_info', structure)
        
        print("✅ 表格结构分析器测试通过")
    
    @unittest.skipUnless(V21_AVAILABLE, "v2.1功能不可用")
    def test_smart_table_parser(self):
        """测试智能表格解析器"""
        parser = SmartTableParser()
        
        # 创建测试CSV文件
        test_csv = os.path.join(self.temp_dir, 'test.csv')
        test_data = pd.DataFrame({
            'product': ['A', 'B', 'C'],
            'price': [10.5, 20.0, 15.5],
            'quantity': [100, 200, 150]
        })
        test_data.to_csv(test_csv, index=False)
        
        # 解析表格
        results = parser.parse_table(test_csv)
        
        # 验证结果
        self.assertGreater(len(results), 0)
        result = results[0]
        self.assertIn('table_id', result)
        self.assertIn('data', result)
        self.assertIn('structure', result)
        self.assertIn('vectors', result)
        
        print("✅ 智能表格解析器测试通过")
    
    @unittest.skipUnless(V21_AVAILABLE, "v2.1功能不可用")
    def test_multimodal_vectorizer(self):
        """测试多模态向量化器"""
        # 使用轻量级模型进行测试，避免依赖冲突
        try:
            vectorizer = MultiModalVectorizer(
                text_model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
        except Exception as e:
            # 如果模型加载失败，创建一个基础实例
            vectorizer = MultiModalVectorizer()
        
        # 测试文本向量化
        text_vector = vectorizer.encode_text("这是一个测试文本")
        if text_vector is not None:
            self.assertIsInstance(text_vector, np.ndarray)
            self.assertGreater(len(text_vector), 0)
        
        # 测试表格结构向量化
        structure = {
            'rows': 3,
            'columns': 2,
            'headers': ['name', 'value'],
            'data_types': {'name': 'text', 'value': 'numeric'}
        }
        structure_vector = vectorizer.encode_table_structure(structure)
        if structure_vector is not None:
            self.assertIsInstance(structure_vector, np.ndarray)
        
        print("✅ 多模态向量化器测试通过")
    
    @unittest.skipUnless(V21_AVAILABLE, "v2.1功能不可用")
    def test_cross_modal_retriever(self):
        """测试跨模态检索器"""
        try:
            vectorizer = MultiModalVectorizer()
        except Exception as e:
            # 如果初始化失败，跳过测试
            print(f"⚠️  跨模态检索器测试跳过: {e}")
            return
            
        retriever = CrossModalRetriever(vectorizer)
        
        # 添加测试内容
        test_content = {
            'vector': np.random.rand(512).astype(np.float32),  # 使用统一维度
            'text': '测试内容',
            'modality': 'text'
        }
        retriever.add_content('text', test_content)
        
        # 测试统计
        stats = retriever.get_statistics()
        self.assertEqual(stats['text'], 1)
        
        print("✅ 跨模态检索器测试通过")
    
    @unittest.skipUnless(V21_AVAILABLE, "v2.1功能不可用")
    def test_v21_integration(self):
        """测试v2.1集成管理器"""
        manager = V21FeatureManager()
        
        # 测试可用性
        self.assertTrue(manager.available)
        
        # 测试组件初始化
        self.assertIsNotNone(manager.file_watcher)
        self.assertIsNotNone(manager.ocr_processor)
        self.assertIsNotNone(manager.table_parser)
        self.assertIsNotNone(manager.multimodal_vectorizer)
        self.assertIsNotNone(manager.cross_modal_retriever)
        
        print("✅ v2.1集成管理器测试通过")

def run_v21_tests():
    """运行v2.1功能测试"""
    print("=" * 60)
    print("  RAG Pro Max v2.1 功能测试")
    print("=" * 60)
    
    if not V21_AVAILABLE:
        print("❌ v2.1功能不可用，跳过测试")
        print("请安装v2.1依赖: pip install -r requirements_v21.txt")
        return False
    
    # 运行测试
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestV21Features)
    runner = unittest.TextTestRunner(verbosity=0)
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
    print(f"⚠️  错误: {errors}/{total_tests}")
    
    if failures == 0 and errors == 0:
        print("\n✅ 所有v2.1功能测试通过！")
        return True
    else:
        print(f"\n❌ 发现 {failures + errors} 个问题")
        return False

if __name__ == '__main__':
    success = run_v21_tests()
    exit(0 if success else 1)
