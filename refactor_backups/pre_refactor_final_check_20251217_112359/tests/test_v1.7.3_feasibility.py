#!/usr/bin/env python3
"""
RAG Pro Max v1.7.3 可行性测试
测试模块导入修复和系统稳定性
"""

import sys
import os
import unittest
import importlib.util

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestV173Feasibility(unittest.TestCase):
    """v1.7.3 可行性测试"""
    
    def setUp(self):
        """测试前准备"""
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def test_01_src_package_structure(self):
        """测试src包结构"""
        init_file = os.path.join(self.project_root, 'src', '__init__.py')
        self.assertTrue(os.path.exists(init_file), "src/__init__.py 文件应该存在")
        
    def test_02_core_environment_import(self):
        """测试核心环境模块导入"""
        try:
            from src.core.environment import initialize_environment
            self.assertTrue(callable(initialize_environment), "initialize_environment 应该是可调用的")
        except ImportError as e:
            self.fail(f"核心环境模块导入失败: {e}")
            
    def test_03_main_app_import(self):
        """测试主应用文件导入"""
        app_file = os.path.join(self.project_root, 'src', 'apppro.py')
        self.assertTrue(os.path.exists(app_file), "src/apppro.py 应该存在")
        
        # 检查导入修复
        with open(app_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('sys.path.insert', content, "应该包含路径修复代码")
            
    def test_04_module_imports(self):
        """测试关键模块导入"""
        modules_to_test = [
            'src.utils.model_manager',
            'src.config.config_loader', 
            'src.chat.history_manager',
            'src.kb.kb_manager',
            'src.logging.log_manager'
        ]
        
        for module_name in modules_to_test:
            try:
                spec = importlib.util.find_spec(module_name)
                self.assertIsNotNone(spec, f"模块 {module_name} 应该可以找到")
            except Exception as e:
                self.fail(f"模块 {module_name} 导入测试失败: {e}")
                
    def test_05_factory_test_compatibility(self):
        """测试出厂测试兼容性"""
        factory_test = os.path.join(self.project_root, 'tests', 'factory_test.py')
        self.assertTrue(os.path.exists(factory_test), "出厂测试文件应该存在")
        
    def test_06_documentation_consistency(self):
        """测试文档一致性"""
        # 检查版本号一致性
        files_to_check = [
            'README.md',
            'CHANGELOG.md', 
            'RELEASE_v1.7.3.md',
            'TESTING.md'
        ]
        
        for filename in files_to_check:
            filepath = os.path.join(self.project_root, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.assertIn('1.7.3', content, f"{filename} 应该包含版本号 1.7.3")
                    
    def test_07_verification_script(self):
        """测试验证脚本"""
        verify_script = os.path.join(self.project_root, 'verify_v1.7.3.sh')
        self.assertTrue(os.path.exists(verify_script), "验证脚本应该存在")
        self.assertTrue(os.access(verify_script, os.X_OK), "验证脚本应该可执行")
        
    def test_08_cleanup_completion(self):
        """测试清理完成状态"""
        # 检查临时文件是否已清理
        temp_patterns = ['DEBUG_', 'FIX_', 'TEMP_', 'QUICK_', 'SIMPLE_']
        root_files = os.listdir(self.project_root)
        
        for pattern in temp_patterns:
            temp_files = [f for f in root_files if f.startswith(pattern)]
            self.assertEqual(len(temp_files), 0, f"不应该有 {pattern} 开头的临时文件")
            
    def test_09_backup_integrity(self):
        """测试备份完整性"""
        backup_dir = os.path.join(self.project_root, 'docs', 'archive', 'temp_cleanup_20251210')
        if os.path.exists(backup_dir):
            backup_files = os.listdir(backup_dir)
            self.assertGreater(len(backup_files), 0, "备份目录应该包含文件")

if __name__ == '__main__':
    print("=" * 60)
    print("  RAG Pro Max v1.7.3 可行性测试")
    print("=" * 60)
    
    # 运行测试
    unittest.main(verbosity=2)
