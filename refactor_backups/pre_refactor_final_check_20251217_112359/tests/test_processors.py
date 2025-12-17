"""
文档处理器模块测试
Stage 4.1
"""

import os
import sys
import tempfile
import shutil
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.processors import UploadHandler, UploadResult, IndexBuilder, BuildResult


def test_upload_handler():
    """测试上传处理器"""
    print("测试上传处理器...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        handler = UploadHandler(tmpdir)
        
        # 测试文件夹统计
        test_dir = os.path.join(tmpdir, "test")
        os.makedirs(test_dir)
        
        # 创建测试文件
        with open(os.path.join(test_dir, "test.txt"), "w") as f:
            f.write("test")
        
        count, types, size = UploadHandler.get_folder_stats(test_dir)
        assert count == 1, "文件数量错误"
        assert '.TXT' in types, "文件类型统计错误"
        assert size > 0, "文件大小统计错误"
    
    print("✅ 上传处理器测试通过")


def test_index_builder_init():
    """测试索引构建器初始化"""
    print("测试索引构建器初始化...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = IndexBuilder(
            kb_name="test_kb",
            persist_dir=tmpdir,
            embed_model=None
        )
        
        assert builder.kb_name == "test_kb", "知识库名称错误"
        assert builder.persist_dir == tmpdir, "持久化目录错误"
    
    print("✅ 索引构建器初始化测试通过")


def test_build_result():
    """测试构建结果数据类"""
    print("测试构建结果...")
    
    result = BuildResult(
        success=True,
        index=None,
        file_count=10,
        doc_count=50,
        duration=1.5
    )
    
    assert result.success == True, "成功标志错误"
    assert result.file_count == 10, "文件数量错误"
    assert result.doc_count == 50, "文档数量错误"
    assert result.duration == 1.5, "耗时错误"
    
    print("✅ 构建结果测试通过")


def test_save_kb_info():
    """测试知识库信息保存"""
    print("测试知识库信息保存...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        builder = IndexBuilder(
            kb_name="test_kb",
            persist_dir=tmpdir,
            embed_model=None
        )
        
        # 调用保存方法
        builder._save_kb_info()
        
        # 检查文件是否创建
        kb_info_file = os.path.join(tmpdir, ".kb_info.json")
        assert os.path.exists(kb_info_file), "kb_info.json 未创建"
        
        # 检查内容
        with open(kb_info_file, 'r') as f:
            kb_info = json.load(f)
        
        assert 'embedding_model' in kb_info, "缺少 embedding_model"
        assert 'embedding_dim' in kb_info, "缺少 embedding_dim"
        assert 'created_at' in kb_info, "缺少 created_at"
    
    print("✅ 知识库信息保存测试通过")


if __name__ == "__main__":
    print("=" * 60)
    print("文档处理器模块测试")
    print("=" * 60)
    
    try:
        test_upload_handler()
        test_index_builder_init()
        test_build_result()
        test_save_kb_info()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        sys.exit(1)
