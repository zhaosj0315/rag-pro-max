"""清单管理器单元测试"""

import unittest
import os
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import ManifestManager


class TestManifestManager(unittest.TestCase):
    """清单管理器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_get_path(self):
        """测试获取路径"""
        path = ManifestManager.get_path(self.test_dir)
        self.assertTrue(path.endswith("manifest.json"))
        self.assertIn(self.test_dir, path)
    
    def test_load_empty(self):
        """测试加载空清单"""
        manifest = ManifestManager.load(self.test_dir)
        self.assertEqual(manifest["files"], [])
        self.assertEqual(manifest["embed_model"], "Unknown")
    
    def test_save_and_load(self):
        """测试保存和加载"""
        files = [
            {"name": "test1.pdf", "size": 1024},
            {"name": "test2.txt", "size": 512}
        ]
        
        success = ManifestManager.save(self.test_dir, files, "test-model")
        self.assertTrue(success)
        
        manifest = ManifestManager.load(self.test_dir)
        self.assertEqual(len(manifest["files"]), 2)
        self.assertEqual(manifest["embed_model"], "test-model")
        self.assertIn("updated_at", manifest)
    
    def test_update_new(self):
        """测试新建更新"""
        files = [{"name": "test.pdf"}]
        
        success = ManifestManager.update(self.test_dir, files, is_append=False, embed_model="model1")
        self.assertTrue(success)
        
        manifest = ManifestManager.load(self.test_dir)
        self.assertEqual(len(manifest["files"]), 1)
    
    def test_update_append(self):
        """测试追加更新"""
        # 先保存初始数据
        files1 = [{"name": "test1.pdf"}]
        ManifestManager.save(self.test_dir, files1, "model1")
        
        # 追加新文件
        files2 = [{"name": "test2.pdf"}]
        success = ManifestManager.update(self.test_dir, files2, is_append=True, embed_model="model1")
        self.assertTrue(success)
        
        # 验证
        manifest = ManifestManager.load(self.test_dir)
        self.assertEqual(len(manifest["files"]), 2)
        self.assertEqual(manifest["files"][0]["name"], "test1.pdf")
        self.assertEqual(manifest["files"][1]["name"], "test2.pdf")
    
    def test_update_replace(self):
        """测试替换更新"""
        # 先保存初始数据
        files1 = [{"name": "test1.pdf"}, {"name": "test2.pdf"}]
        ManifestManager.save(self.test_dir, files1, "model1")
        
        # 替换
        files2 = [{"name": "test3.pdf"}]
        success = ManifestManager.update(self.test_dir, files2, is_append=False, embed_model="model2")
        self.assertTrue(success)
        
        # 验证
        manifest = ManifestManager.load(self.test_dir)
        self.assertEqual(len(manifest["files"]), 1)
        self.assertEqual(manifest["files"][0]["name"], "test3.pdf")
        self.assertEqual(manifest["embed_model"], "model2")


def run_tests():
    """运行测试"""
    suite = unittest.TestLoader().loadTestsFromTestCase(TestManifestManager)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
