"""
IndexBuilder修复功能单元测试
"""
import unittest
import tempfile
import os
from unittest.mock import Mock, patch
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class TestIndexBuilderFixes(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test.txt")
        with open(self.test_file, 'w', encoding='utf-8') as f:
            f.write("测试内容")
    
    def tearDown(self):
        """测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.processors.index_builder.get_file_info')
    def test_build_manifest_single_file(self, mock_get_file_info):
        """测试单文件清单构建"""
        from src.processors.index_builder import IndexBuilder
        
        # 模拟get_file_info返回
        mock_get_file_info.return_value = {
            'name': 'test.txt',
            'size': 100,
            'type': 'text'
        }
        
        builder = IndexBuilder()
        callback = Mock()
        
        result = builder._build_manifest(self.test_file, callback)
        
        # 验证结果
        self.assertEqual(len(result), 1)
        self.assertIn('test.txt', result)
        self.assertEqual(result['test.txt']['doc_ids'], [])
        
        # 验证回调
        callback.assert_any_call("step", 4, "构建文件清单")
        callback.assert_any_call("info", "清单完成: 1 个文件已登记")
    
    def test_build_manifest_nonexistent_file(self):
        """测试不存在文件的处理"""
        from src.processors.index_builder import IndexBuilder
        
        builder = IndexBuilder()
        callback = Mock()
        
        result = builder._build_manifest("/nonexistent/file.txt", callback)
        
        # 验证返回空字典
        self.assertEqual(result, {})
        callback.assert_any_call("error", "路径不存在: /nonexistent/file.txt")
    
    def test_build_manifest_no_permission(self):
        """测试无权限文件的处理"""
        from src.processors.index_builder import IndexBuilder
        
        # 创建无权限文件
        no_perm_file = os.path.join(self.temp_dir, "no_perm.txt")
        with open(no_perm_file, 'w') as f:
            f.write("test")
        os.chmod(no_perm_file, 0o000)  # 移除所有权限
        
        try:
            builder = IndexBuilder()
            callback = Mock()
            
            result = builder._build_manifest(no_perm_file, callback)
            
            # 验证返回空字典
            self.assertEqual(result, {})
            
        finally:
            # 恢复权限以便清理
            os.chmod(no_perm_file, 0o644)
    
    def test_safe_basename_normal(self):
        """测试正常文件名处理"""
        from src.processors.index_builder import IndexBuilder
        
        builder = IndexBuilder()
        
        # 正常文件名
        result = builder._safe_basename("/path/to/file.txt")
        self.assertEqual(result, "file.txt")
    
    def test_safe_basename_path_traversal(self):
        """测试路径遍历攻击防护"""
        from src.processors.index_builder import IndexBuilder
        
        builder = IndexBuilder()
        
        # 路径遍历攻击
        result = builder._safe_basename("/path/to/../../../etc/passwd")
        self.assertIsNone(result)
        
        # 点文件
        result = builder._safe_basename("/path/to/.")
        self.assertIsNone(result)
        
        # 空文件名
        result = builder._safe_basename("")
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
