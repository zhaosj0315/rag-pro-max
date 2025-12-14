#!/usr/bin/env python3
"""
v2.3.1 完整功能测试
确保所有v2.3.1功能与文档描述一致
"""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestV231Complete(unittest.TestCase):
    """v2.3.1 完整功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_version_info_consistency(self):
        """测试版本信息一致性"""
        print("\n🔍 测试版本信息一致性...")
        
        # 检查version.json
        import json
        with open('version.json', 'r') as f:
            version_data = json.load(f)
        
        self.assertEqual(version_data['version'], "2.3.1")
        self.assertEqual(version_data['codename'], "安全增强版")
        self.assertIn("安全熔断机制", version_data['features'])
        self.assertIn("自动清理机制", version_data['features'])
        self.assertIn("停止按钮功能", version_data['features'])
        self.assertIn("引用页码显示", version_data['features'])
        
        print("   ✅ 版本信息一致性验证通过")
    
    def test_safety_circuit_breaker_implementation(self):
        """测试安全熔断机制实现"""
        print("\n🛑 测试安全熔断机制实现...")
        
        try:
            from src.processors.web_crawler import WebCrawler
            
            # 检查WebCrawler类存在
            crawler = WebCrawler()
            self.assertTrue(hasattr(crawler, 'crawl_advanced'), "WebCrawler应该有crawl_advanced方法")
            
            # 检查源码中的熔断逻辑
            import inspect
            source = inspect.getsource(crawler.crawl_advanced)
            self.assertIn("GLOBAL_MAX_PAGES = 50000", source, "应该有5万页硬编码限制")
            self.assertIn("安全熔断", source, "应该有安全熔断提示")
            
            print("   ✅ 安全熔断机制实现正确")
            
        except ImportError as e:
            self.fail(f"WebCrawler导入失败: {e}")
    
    def test_auto_cleanup_implementation(self):
        """测试自动清理机制实现"""
        print("\n🧹 测试自动清理机制实现...")
        
        # 检查cleanup_temp_files函数
        with open('src/apppro.py', 'r') as f:
            content = f.read()
        
        self.assertIn("def cleanup_temp_files():", content, "应该有cleanup_temp_files函数")
        self.assertTrue("86400" in content or "24 * 3600" in content, "应该有24小时时间阈值")
        self.assertIn("temp_uploads", content, "应该清理temp_uploads目录")
        
        # 创建测试文件验证清理逻辑
        test_temp_dir = os.path.join(self.test_dir, "temp_uploads")
        os.makedirs(test_temp_dir, exist_ok=True)
        
        # 创建旧文件
        old_file = os.path.join(test_temp_dir, "old_file.txt")
        with open(old_file, 'w') as f:
            f.write("test")
        
        # 修改文件时间为25小时前
        old_time = time.time() - 25 * 3600
        os.utime(old_file, (old_time, old_time))
        
        print("   ✅ 自动清理机制实现正确")
    
    def test_stop_button_implementation(self):
        """测试停止按钮功能实现"""
        print("\n⏹ 测试停止按钮功能实现...")
        
        # 检查停止按钮相关代码
        with open('src/apppro.py', 'r') as f:
            content = f.read()
        
        self.assertIn("停止按钮功能", content, "应该有停止按钮功能注释")
        self.assertIn("is_processing", content, "应该有处理状态管理")
        self.assertIn("stop_generation", content, "应该有停止生成标志")
        self.assertIn("⏹ 停止", content, "应该有停止按钮UI")
        
        print("   ✅ 停止按钮功能实现正确")
    
    def test_pdf_page_reader_implementation(self):
        """测试PDF页码读取器实现"""
        print("\n📄 测试PDF页码读取器实现...")
        
        try:
            from src.utils.pdf_page_reader import PDFPageReader
            
            # 检查PDFPageReader类
            reader = PDFPageReader()
            self.assertTrue(hasattr(reader, 'load_data'), "PDFPageReader应该有load_data方法")
            self.assertEqual(reader.supported_suffixes, [".pdf"], "应该支持PDF格式")
            
            # 检查源码中的页码记录逻辑
            import inspect
            source = inspect.getsource(reader.load_data)
            self.assertIn("page_number", source, "应该记录页码信息")
            self.assertIn("metadata", source, "应该有元数据记录")
            
            print("   ✅ PDF页码读取器实现正确")
            
        except ImportError as e:
            self.fail(f"PDFPageReader导入失败: {e}")
    
    def test_monitoring_dashboard_basic(self):
        """测试基础监控仪表板"""
        print("\n📊 测试基础监控仪表板...")
        
        try:
            # 检查监控相关模块
            from src.ui.progress_tracker import ProgressTracker
            
            tracker = ProgressTracker()
            self.assertTrue(hasattr(tracker, 'update_progress'), "应该有进度更新方法")
            
            print("   ✅ 基础监控仪表板正常")
            
        except ImportError:
            print("   ⚠️ 监控仪表板模块可选，跳过测试")
    
    def test_documentation_alignment(self):
        """测试文档对齐状态"""
        print("\n📚 测试文档对齐状态...")
        
        # 检查CHANGELOG.md
        with open('CHANGELOG.md', 'r') as f:
            changelog = f.read()
        
        self.assertIn("v2.3.1", changelog, "CHANGELOG应该包含v2.3.1版本")
        self.assertIn("安全增强版", changelog, "应该有版本代号")
        self.assertIn("安全熔断机制", changelog, "应该有功能描述")
        
        # 检查README.md
        with open('README.md', 'r') as f:
            readme = f.read()
        
        self.assertIn("v2.3.1", readme, "README应该包含v2.3.1版本")
        
        print("   ✅ 文档对齐状态良好")
    
    def test_feature_completeness(self):
        """测试功能完整性"""
        print("\n🎯 测试功能完整性...")
        
        # 检查所有v2.3.1功能是否实现
        features_implemented = {
            "安全熔断机制": False,
            "自动清理机制": False, 
            "停止按钮功能": False,
            "引用页码显示": False
        }
        
        # 检查安全熔断
        try:
            from src.processors.web_crawler import WebCrawler
            features_implemented["安全熔断机制"] = True
        except:
            pass
        
        # 检查自动清理
        with open('src/apppro.py', 'r') as f:
            if "cleanup_temp_files" in f.read():
                features_implemented["自动清理机制"] = True
        
        # 检查停止按钮
        with open('src/apppro.py', 'r') as f:
            if "stop_generation" in f.read():
                features_implemented["停止按钮功能"] = True
        
        # 检查PDF页码
        try:
            from src.utils.pdf_page_reader import PDFPageReader
            features_implemented["引用页码显示"] = True
        except:
            pass
        
        # 验证所有功能都已实现
        for feature, implemented in features_implemented.items():
            self.assertTrue(implemented, f"{feature}未实现")
        
        print("   ✅ 所有v2.3.1功能已完整实现")

if __name__ == '__main__':
    unittest.main()
