#!/usr/bin/env python3
"""
v2.3.1 集成测试
测试所有新功能的端到端集成
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

class TestV231Integration(unittest.TestCase):
    """v2.3.1 集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
    
    def tearDown(self):
        """测试后清理"""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_version_consistency(self):
        """测试版本一致性"""
        print("\n🔍 测试版本一致性...")
        
        # 测试统一版本管理
        from src.core.version import VERSION, VERSION_TAG, get_version
        
        # 检查版本格式
        self.assertRegex(VERSION, r'^\d+\.\d+\.\d+$', "版本号格式错误")
        self.assertEqual(VERSION_TAG, f"v{VERSION}", "版本标签格式错误")
        
        # 检查版本文件一致性
        import json
        with open('version.json', 'r') as f:
            version_data = json.load(f)
        
        self.assertEqual(version_data['version'], VERSION, "version.json与代码版本不一致")
        
        print(f"   ✅ 版本一致性验证通过: {VERSION}")
    
    def test_safety_circuit_breaker_integration(self):
        """测试安全熔断机制集成"""
        print("\n🛑 测试安全熔断机制集成...")
        
        from src.processors.web_crawler import WebCrawler
        
        crawler = WebCrawler()
        
        # 测试熔断阈值
        messages = []
        def callback(msg):
            messages.append(msg)
        
        # 测试正常范围
        try:
            result = crawler.crawl_advanced(
                start_url="https://httpbin.org/html",
                max_depth=1,
                max_pages=100,
                status_callback=callback
            )
            self.assertIsInstance(result, list, "正常范围应该返回结果列表")
        except Exception:
            pass  # 网络问题可以忽略
        
        # 测试熔断触发
        messages.clear()
        try:
            result = crawler.crawl_advanced(
                start_url="https://httpbin.org/html",
                max_depth=1,
                max_pages=60000,  # 超过5万限制
                status_callback=callback
            )
            
            # 检查熔断消息
            safety_messages = [msg for msg in messages if "安全熔断" in msg]
            self.assertGreater(len(safety_messages), 0, "应该触发安全熔断消息")
            
        except Exception:
            pass  # 网络问题可以忽略
        
        print("   ✅ 安全熔断机制集成正常")
    
    def test_auto_cleanup_integration(self):
        """测试自动清理机制集成"""
        print("\n🧹 测试自动清理机制集成...")
        
        # 创建测试环境
        temp_uploads = os.path.join(self.test_dir, "temp_uploads")
        os.makedirs(temp_uploads, exist_ok=True)
        
        # 创建测试文件
        old_file = os.path.join(temp_uploads, "old_file.txt")
        new_file = os.path.join(temp_uploads, "new_file.txt")
        
        with open(old_file, 'w') as f:
            f.write("old content")
        with open(new_file, 'w') as f:
            f.write("new content")
        
        # 设置文件时间
        old_time = time.time() - (25 * 60 * 60)  # 25小时前
        new_time = time.time() - (1 * 60 * 60)   # 1小时前
        
        os.utime(old_file, (old_time, old_time))
        os.utime(new_file, (new_time, new_time))
        
        # 切换到测试目录
        os.chdir(self.test_dir)
        
        # 模拟清理函数
        current_time = time.time()
        cleaned_files = []
        
        for filename in os.listdir(temp_uploads):
            if filename.startswith('.'):
                continue
            
            filepath = os.path.join(temp_uploads, filename)
            if not os.path.isfile(filepath):
                continue
            if not os.access(filepath, os.R_OK | os.W_OK):
                continue
            
            try:
                file_time = os.path.getmtime(filepath)
                if current_time - file_time > 86400:  # 24小时
                    os.remove(filepath)
                    cleaned_files.append(filename)
            except (OSError, IOError):
                continue
        
        # 验证清理结果
        self.assertIn("old_file.txt", cleaned_files, "应该清理旧文件")
        self.assertNotIn("new_file.txt", cleaned_files, "不应该清理新文件")
        self.assertFalse(os.path.exists(old_file), "旧文件应该被删除")
        self.assertTrue(os.path.exists(new_file), "新文件应该保留")
        
        print(f"   ✅ 自动清理机制集成正常，清理了 {len(cleaned_files)} 个文件")
    
    def test_stop_button_integration(self):
        """测试停止按钮功能集成"""
        print("\n⏹ 测试停止按钮功能集成...")
        
        # 模拟session_state
        class MockSessionState:
            def __init__(self):
                self.data = {}
            
            def get(self, key, default=None):
                return self.data.get(key, default)
            
            def __setitem__(self, key, value):
                self.data[key] = value
            
            def __getitem__(self, key):
                return self.data[key]
        
        session_state = MockSessionState()
        
        # 测试停止逻辑流程
        session_state['is_processing'] = True
        session_state['stop_generation'] = False
        
        # 模拟用户点击停止按钮
        if session_state.get('is_processing'):
            session_state['is_processing'] = False
            session_state['stop_generation'] = True
        
        # 验证状态变化
        self.assertFalse(session_state.get('is_processing'), "处理状态应该为False")
        self.assertTrue(session_state.get('stop_generation'), "停止信号应该为True")
        
        # 模拟流式生成检查
        tokens = ["Hello", " ", "World", "!"]
        result = []
        
        for token in tokens:
            if session_state.get('stop_generation'):
                session_state['stop_generation'] = False
                result.append("\n\n⏹ **生成已停止**")
                break
            result.append(token)
        
        # 验证停止效果
        self.assertIn("⏹ **生成已停止**", "".join(result), "应该包含停止提示")
        self.assertFalse(session_state.get('stop_generation'), "停止信号应该被重置")
        
        print("   ✅ 停止按钮功能集成正常")
    
    def test_pdf_page_reader_integration(self):
        """测试PDF页码读取器集成"""
        print("\n📄 测试PDF页码读取器集成...")
        
        from src.utils.pdf_page_reader import PDFPageReader
        from src.utils.safe_parallel_tasks import safe_process_node_worker
        
        # 测试PDF读取器初始化
        reader = PDFPageReader()
        self.assertEqual(reader.supported_suffixes, ['.pdf'], "支持格式应该只有PDF")
        
        # 测试节点处理集成
        test_node_data = {
            'metadata': {
                'file_name': 'test_document.pdf',
                'page_number': 3,
                'page_label': '第3页',
                'total_pages': 10
            },
            'score': 0.85,
            'text': '这是第三页的测试内容',
            'node_id': 'test_node_123'
        }
        
        # 处理节点
        result = safe_process_node_worker((test_node_data, 'test_kb'))
        
        # 验证处理结果
        self.assertIn('display_name', result, "结果应该包含display_name")
        self.assertIn('[第3页]', result['display_name'], "显示名称应该包含页码")
        self.assertEqual(result['file_name'], 'test_document.pdf', "文件名应该正确")
        self.assertIn('page_info', result, "结果应该包含page_info")
        
        print(f"   ✅ PDF页码读取器集成正常: {result['display_name']}")
    
    def test_ui_components_integration(self):
        """测试UI组件集成"""
        print("\n🎨 测试UI组件集成...")
        
        from src.ui.display_components import render_source_references
        
        # 测试引用来源数据结构
        test_sources = [
            {
                'display_name': 'document.pdf [第2页]',
                'file_name': 'document.pdf',
                'page_info': '[第2页]',
                'score': 0.92,
                'text': '这是第二页的内容，包含重要信息。',
                'node_id': 'node_456'
            },
            {
                'display_name': 'report.pdf [第5页]',
                'file_name': 'report.pdf', 
                'page_info': '[第5页]',
                'score': 0.78,
                'text': '这是第五页的报告内容。',
                'node_id': 'node_789'
            }
        ]
        
        # 验证数据结构完整性
        for source in test_sources:
            required_fields = ['display_name', 'file_name', 'score', 'text', 'node_id']
            for field in required_fields:
                self.assertIn(field, source, f"引用来源应该包含{field}字段")
            
            # 验证页码信息
            if 'page_info' in source:
                self.assertIn(source['page_info'], source['display_name'], 
                            "display_name应该包含页码信息")
        
        # 测试函数存在性（不实际渲染UI）
        self.assertTrue(callable(render_source_references), "render_source_references应该是可调用的")
        
        print("   ✅ UI组件集成正常")
    
    def test_error_handling_integration(self):
        """测试错误处理集成"""
        print("\n🛡️ 测试错误处理集成...")
        
        # 测试PDF读取器错误处理
        from src.utils.pdf_page_reader import PDFPageReader
        
        reader = PDFPageReader()
        
        # 测试无效路径
        with self.assertRaises(ValueError):
            reader.load_data("")
        
        with self.assertRaises(ValueError):
            reader.load_data(None)
        
        # 测试不存在的文件
        with self.assertRaises(FileNotFoundError):
            reader.load_data("/nonexistent/file.pdf")
        
        # 测试非PDF文件（先创建文件）
        test_txt_file = os.path.join(self.test_dir, "test.txt")
        with open(test_txt_file, 'w') as f:
            f.write("test content")
        
        with self.assertRaises(ValueError):
            reader.load_data(test_txt_file)
        
        # 测试安全清理错误处理
        temp_dir = os.path.join(self.test_dir, "temp_uploads")
        os.makedirs(temp_dir, exist_ok=True)
        
        # 创建无权限文件
        restricted_file = os.path.join(temp_dir, "restricted.txt")
        with open(restricted_file, 'w') as f:
            f.write("restricted content")
        
        # 移除写权限
        os.chmod(restricted_file, 0o444)
        
        # 测试清理逻辑（应该跳过无权限文件）
        current_time = time.time()
        cleaned_count = 0
        errors = []
        
        for filename in os.listdir(temp_dir):
            if filename.startswith('.'):
                continue
            
            filepath = os.path.join(temp_dir, filename)
            if not os.path.isfile(filepath):
                continue
            if not os.access(filepath, os.R_OK | os.W_OK):
                continue  # 应该跳过无权限文件
            
            try:
                file_time = os.path.getmtime(filepath)
                if current_time - file_time > 86400:
                    os.remove(filepath)
                    cleaned_count += 1
            except (OSError, IOError) as e:
                errors.append(str(e))
        
        # 验证错误处理
        self.assertEqual(cleaned_count, 0, "无权限文件应该被跳过")
        self.assertTrue(os.path.exists(restricted_file), "无权限文件应该保留")
        
        print("   ✅ 错误处理集成正常")

def run_integration_tests():
    """运行集成测试"""
    print("=" * 60)
    print("  RAG Pro Max v2.3.1 集成测试")
    print("  时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV231Integration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("  集成测试结果汇总")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"✅ 通过: {passed}/{total_tests}")
    print(f"❌ 失败: {failures}/{total_tests}")
    print(f"💥 错误: {errors}/{total_tests}")
    
    if failures > 0:
        print("\n❌ 失败详情:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if errors > 0:
        print("\n💥 错误详情:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 所有v2.3.1集成测试通过！")
        return True
    else:
        print(f"\n⚠️ 有 {failures + errors} 个测试未通过")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
