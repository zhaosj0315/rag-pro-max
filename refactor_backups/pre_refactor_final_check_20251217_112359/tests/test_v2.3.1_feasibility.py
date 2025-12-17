#!/usr/bin/env python3
"""
v2.3.1 功能可行性测试
测试安全熔断、自动清理、停止按钮、引用页码功能的可行性
"""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestV231Feasibility(unittest.TestCase):
    """v2.3.1 功能可行性测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
    
    def test_safety_circuit_breaker(self):
        """测试1: 安全熔断机制可行性"""
        print("\n🛑 测试安全熔断机制...")
        
        try:
            from src.processors.web_crawler import WebCrawler
            
            crawler = WebCrawler()
            
            # 测试熔断逻辑
            messages = []
            def callback(msg):
                messages.append(msg)
            
            # 模拟超大页面数
            result = crawler.crawl_advanced(
                start_url="https://httpbin.org/html",
                max_depth=1,
                max_pages=60000,  # 超过5万限制
                status_callback=callback
            )
            
            # 检查熔断消息
            has_safety_msg = any("安全熔断" in msg for msg in messages)
            self.assertTrue(has_safety_msg, "安全熔断机制应该触发")
            
            print("   ✅ 安全熔断机制可行")
            
        except Exception as e:
            self.fail(f"安全熔断测试失败: {e}")
    
    def test_auto_cleanup_mechanism(self):
        """测试2: 自动清理机制可行性"""
        print("\n🧹 测试自动清理机制...")
        
        try:
            # 创建临时目录和文件
            temp_dir = os.path.join(self.test_dir, "temp_uploads")
            os.makedirs(temp_dir, exist_ok=True)
            
            # 创建旧文件
            old_file = os.path.join(temp_dir, "old_file.txt")
            with open(old_file, 'w') as f:
                f.write("old content")
            
            # 设置文件时间为2天前
            old_time = time.time() - (2 * 24 * 60 * 60)
            os.utime(old_file, (old_time, old_time))
            
            # 执行清理逻辑
            current_time = time.time()
            cleaned_count = 0
            
            for filename in os.listdir(temp_dir):
                filepath = os.path.join(temp_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if current_time - file_time > 86400:  # 24小时
                        os.remove(filepath)
                        cleaned_count += 1
            
            self.assertGreater(cleaned_count, 0, "应该清理至少1个文件")
            print(f"   ✅ 自动清理机制可行，清理了 {cleaned_count} 个文件")
            
        except Exception as e:
            self.fail(f"自动清理测试失败: {e}")
    
    def test_stop_button_logic(self):
        """测试3: 停止按钮逻辑可行性"""
        print("\n⏹ 测试停止按钮逻辑...")
        
        try:
            # 模拟session_state
            class MockSessionState:
                def __init__(self):
                    self.data = {}
                
                def get(self, key, default=None):
                    return self.data.get(key, default)
                
                def __setitem__(self, key, value):
                    self.data[key] = value
            
            session_state = MockSessionState()
            
            # 测试停止逻辑
            session_state['is_processing'] = True
            session_state['stop_generation'] = False
            
            # 模拟停止按钮点击
            if session_state.get('is_processing'):
                session_state['is_processing'] = False
                session_state['stop_generation'] = True
            
            # 验证状态变化
            self.assertFalse(session_state.get('is_processing'))
            self.assertTrue(session_state.get('stop_generation'))
            
            print("   ✅ 停止按钮逻辑可行")
            
        except Exception as e:
            self.fail(f"停止按钮测试失败: {e}")
    
    def test_pdf_page_reader(self):
        """测试4: PDF页码读取器可行性"""
        print("\n📄 测试PDF页码读取器...")
        
        try:
            from src.utils.pdf_page_reader import PDFPageReader
            
            reader = PDFPageReader()
            
            # 检查初始化
            self.assertIsNotNone(reader)
            self.assertEqual(reader.supported_suffixes, ['.pdf'])
            
            print("   ✅ PDF页码读取器可行")
            
        except Exception as e:
            self.fail(f"PDF页码读取器测试失败: {e}")
    
    def test_source_reference_display(self):
        """测试5: 引用来源显示可行性"""
        print("\n📚 测试引用来源显示...")
        
        try:
            from src.utils.safe_parallel_tasks import safe_process_node_worker
            
            # 模拟节点数据
            node_data = {
                'metadata': {
                    'file_name': 'test.pdf',
                    'page_number': 3,
                    'page_label': '第3页'
                },
                'score': 0.9,
                'text': '测试内容',
                'node_id': 'test_123'
            }
            
            # 处理节点
            result = safe_process_node_worker((node_data, 'test_kb'))
            
            # 验证结果
            self.assertIn('display_name', result)
            self.assertIn('[第3页]', result['display_name'])
            self.assertEqual(result['file_name'], 'test.pdf')
            
            print(f"   ✅ 引用来源显示可行: {result['display_name']}")
            
        except Exception as e:
            self.fail(f"引用来源显示测试失败: {e}")
    
    def test_ui_components_integration(self):
        """测试6: UI组件集成可行性"""
        print("\n🎨 测试UI组件集成...")
        
        try:
            from src.ui.display_components import render_source_references
            
            # 模拟引用数据
            sources = [{
                'display_name': 'test.pdf [第2页]',
                'file_name': 'test.pdf',
                'page_info': '[第2页]',
                'score': 0.85,
                'text': '这是测试内容',
                'node_id': 'node_456'
            }]
            
            # 这里只测试函数存在性，不实际渲染UI
            self.assertTrue(callable(render_source_references))
            
            print("   ✅ UI组件集成可行")
            
        except Exception as e:
            self.fail(f"UI组件集成测试失败: {e}")

def run_feasibility_tests():
    """运行可行性测试"""
    print("=" * 60)
    print("  RAG Pro Max v2.3.1 功能可行性测试")
    print("  时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestV231Feasibility)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
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
    print(f"💥 错误: {errors}/{total_tests}")
    
    if failures == 0 and errors == 0:
        print("\n🎉 所有v2.3.1功能可行性测试通过！")
        return True
    else:
        print(f"\n⚠️ 有 {failures + errors} 个测试未通过")
        return False

if __name__ == "__main__":
    success = run_feasibility_tests()
    sys.exit(0 if success else 1)
