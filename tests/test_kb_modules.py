"""知识库模块测试"""

import os
import sys
import tempfile
import shutil
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kb import KBManager, KBOperations


class TestKBOperations:
    """测试 KBOperations 类"""
    
    def __init__(self):
        self.temp_dir = None
        self.ops = KBOperations()
    
    def setup(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        return True
    
    def teardown(self):
        """测试后清理"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        return True
    
    def test_create_kb(self):
        """测试创建知识库"""
        kb_name = "test_kb"
        success = self.ops.create_kb(kb_name, self.temp_dir)
        
        assert success, "创建知识库失败"
        assert os.path.exists(os.path.join(self.temp_dir, kb_name)), "知识库目录不存在"
        
        # 重复创建应该返回 False
        success = self.ops.create_kb(kb_name, self.temp_dir)
        assert not success, "重复创建应该返回 False"
        
        return True
    
    def test_delete_kb(self):
        """测试删除知识库"""
        kb_name = "test_kb_delete"
        self.ops.create_kb(kb_name, self.temp_dir)
        
        # 创建历史文件
        history_dir = os.path.join(self.temp_dir, "histories")
        os.makedirs(history_dir, exist_ok=True)
        hist_file = os.path.join(history_dir, f"{kb_name}.json")
        with open(hist_file, 'w') as f:
            json.dump([], f)
        
        success = self.ops.delete_kb(kb_name, self.temp_dir, history_dir)
        
        assert success, "删除知识库失败"
        assert not os.path.exists(os.path.join(self.temp_dir, kb_name)), "知识库目录仍存在"
        assert not os.path.exists(hist_file), "历史文件仍存在"
        
        return True
    
    def test_rename_kb(self):
        """测试重命名知识库"""
        old_name = "old_kb"
        new_name = "new_kb"
        
        self.ops.create_kb(old_name, self.temp_dir)
        
        success = self.ops.rename_kb(old_name, new_name, self.temp_dir, self.temp_dir)
        
        assert success, "重命名失败"
        assert not os.path.exists(os.path.join(self.temp_dir, old_name)), "旧目录仍存在"
        assert os.path.exists(os.path.join(self.temp_dir, new_name)), "新目录不存在"
        
        return True
    
    def test_list_kbs(self):
        """测试列出知识库"""
        kb_names = ["kb1", "kb2", "kb3"]
        
        for name in kb_names:
            self.ops.create_kb(name, self.temp_dir)
            time.sleep(0.01)  # 确保时间戳不同
        
        # 按时间排序
        kbs = self.ops.list_kbs(self.temp_dir, sort_by_time=True)
        assert len(kbs) == 3, f"知识库数量错误: {len(kbs)}"
        assert kbs[0] == "kb3", "时间排序错误"
        
        # 按名称排序
        kbs = self.ops.list_kbs(self.temp_dir, sort_by_time=False)
        assert kbs == sorted(kb_names), "名称排序错误"
        
        return True
    
    def test_kb_exists(self):
        """测试检查知识库存在"""
        kb_name = "test_exists"
        
        assert not self.ops.kb_exists(kb_name, self.temp_dir), "不存在的知识库返回 True"
        
        self.ops.create_kb(kb_name, self.temp_dir)
        assert self.ops.kb_exists(kb_name, self.temp_dir), "存在的知识库返回 False"
        
        return True
    
    def test_save_load_kb_info(self):
        """测试保存和加载知识库信息"""
        kb_name = "test_info"
        self.ops.create_kb(kb_name, self.temp_dir)
        
        kb_path = os.path.join(self.temp_dir, kb_name)
        embed_model = "test-model"
        embed_dim = 768
        
        # 保存信息
        success = self.ops.save_kb_info(kb_path, embed_model, embed_dim)
        assert success, "保存信息失败"
        
        # 加载信息
        info = self.ops.load_kb_info(kb_path)
        assert info is not None, "加载信息失败"
        assert info['embedding_model'] == embed_model, "模型名称不匹配"
        assert info['embedding_dim'] == embed_dim, "维度不匹配"
        assert 'created_at' in info, "缺少创建时间"
        
        return True


class TestKBManager:
    """测试 KBManager 类"""
    
    def __init__(self):
        self.temp_dir = None
        self.manager = None
    
    def setup(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = KBManager(base_path=self.temp_dir, history_dir=self.temp_dir)
        return True
    
    def teardown(self):
        """测试后清理"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        return True
    
    def test_create(self):
        """测试创建知识库"""
        success, msg = self.manager.create("test_kb")
        assert success, f"创建失败: {msg}"
        assert "成功" in msg, "消息不正确"
        
        # 重复创建
        success, msg = self.manager.create("test_kb")
        assert not success, "重复创建应该失败"
        assert "已存在" in msg, "错误消息不正确"
        
        # 空名称
        success, msg = self.manager.create("")
        assert not success, "空名称应该失败"
        
        return True
    
    def test_delete(self):
        """测试删除知识库"""
        self.manager.create("test_delete")
        
        success, msg = self.manager.delete("test_delete")
        assert success, f"删除失败: {msg}"
        assert "已删除" in msg, "消息不正确"
        
        # 删除不存在的
        success, msg = self.manager.delete("not_exist")
        assert not success, "删除不存在的应该失败"
        
        return True
    
    def test_rename(self):
        """测试重命名知识库"""
        self.manager.create("old_name")
        
        success, msg = self.manager.rename("old_name", "new_name")
        assert success, f"重命名失败: {msg}"
        assert "已重命名" in msg, "消息不正确"
        assert not self.manager.exists("old_name"), "旧名称仍存在"
        assert self.manager.exists("new_name"), "新名称不存在"
        
        return True
    
    def test_list_all(self):
        """测试列出所有知识库"""
        names = ["kb_a", "kb_b", "kb_c"]
        for name in names:
            self.manager.create(name)
            time.sleep(0.01)
        
        kbs = self.manager.list_all()
        assert len(kbs) == 3, f"数量错误: {len(kbs)}"
        
        return True
    
    def test_exists(self):
        """测试检查存在"""
        assert not self.manager.exists("not_exist"), "不存在的返回 True"
        
        self.manager.create("exist_kb")
        assert self.manager.exists("exist_kb"), "存在的返回 False"
        
        return True
    
    def test_get_info(self):
        """测试获取信息"""
        kb_name = "info_kb"
        self.manager.create(kb_name)
        self.manager.save_info(kb_name, "test-model", 768)
        
        info = self.manager.get_info(kb_name)
        assert info is not None, "获取信息失败"
        assert info['name'] == kb_name, "名称不匹配"
        assert info['embedding_model'] == "test-model", "模型不匹配"
        assert 'created_time' in info, "缺少创建时间"
        
        return True
    
    def test_get_stats(self):
        """测试获取统计信息"""
        kb_name = "stats_kb"
        self.manager.create(kb_name)
        
        stats = self.manager.get_stats(kb_name)
        assert stats is not None, "获取统计失败"
        assert 'size' in stats, "缺少大小"
        assert 'file_count' in stats, "缺少文件数"
        assert 'modified_time' in stats, "缺少修改时间"
        
        return True
    
    def test_search(self):
        """测试搜索知识库"""
        names = ["python_docs", "java_docs", "python_tutorial"]
        for name in names:
            self.manager.create(name)
        
        results = self.manager.search("python")
        assert len(results) == 2, f"搜索结果数量错误: {len(results)}"
        assert all("python" in r.lower() for r in results), "搜索结果不正确"
        
        return True
    
    def test_format_size(self):
        """测试格式化大小"""
        assert "1.00 KB" in KBManager.format_size(1024), "KB 格式化错误"
        assert "1.00 MB" in KBManager.format_size(1024 * 1024), "MB 格式化错误"
        assert "B" in KBManager.format_size(100), "B 格式化错误"
        
        return True


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  知识库模块测试")
    print("="*60 + "\n")
    
    test_classes = [
        ("KBOperations", TestKBOperations),
        ("KBManager", TestKBManager)
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for class_name, test_class in test_classes:
        print(f"\n📦 测试 {class_name}")
        print("-" * 60)
        
        tester = test_class()
        test_methods = [m for m in dir(tester) if m.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            test_name = method_name.replace('test_', '').replace('_', ' ').title()
            
            try:
                tester.setup()
                method = getattr(tester, method_name)
                result = method()
                tester.teardown()
                
                if result:
                    print(f"  ✅ {test_name}")
                    passed_tests += 1
                else:
                    print(f"  ❌ {test_name} - 返回 False")
                    failed_tests.append(f"{class_name}.{method_name}")
            except Exception as e:
                print(f"  ❌ {test_name} - {str(e)}")
                failed_tests.append(f"{class_name}.{method_name}")
                try:
                    tester.teardown()
                except:
                    pass
    
    # 打印总结
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    print(f"✅ 通过: {passed_tests}/{total_tests}")
    print(f"❌ 失败: {len(failed_tests)}/{total_tests}")
    
    if failed_tests:
        print(f"\n失败的测试:")
        for test in failed_tests:
            print(f"  - {test}")
        print("\n❌ 部分测试失败")
        return False
    else:
        print("\n✅ 所有测试通过！")
        return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
