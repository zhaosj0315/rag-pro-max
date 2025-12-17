#!/usr/bin/env python3
"""
ManifestManager 单元测试
"""

import sys
import os
import tempfile
import shutil
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_manifest_manager():
    """测试ManifestManager功能"""
    print("🧪 测试ManifestManager...")
    
    try:
        from src.config.manifest_manager import ManifestManager
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 测试保存和加载
            test_files = [
                {
                    'name': 'test1.pdf',
                    'path': '/path/to/test1.pdf',
                    'size': 1024,
                    'type': '.pdf'
                },
                {
                    'name': 'test2.txt',
                    'path': '/path/to/test2.txt', 
                    'size': 512,
                    'type': '.txt'
                }
            ]
            
            # 测试保存
            result = ManifestManager.save(temp_dir, test_files, 'test-model')
            assert result == True, "保存应该成功"
            
            # 测试加载
            manifest = ManifestManager.load(temp_dir)
            assert 'files' in manifest, "清单应该包含files字段"
            assert manifest['file_count'] == 2, f"文件数量应该是2，实际是{manifest['file_count']}"
            assert manifest['embed_model'] == 'test-model', "嵌入模型应该正确"
            
            # 测试统计
            stats = ManifestManager.get_stats(temp_dir)
            assert stats['file_count'] == 2, "统计文件数量应该正确"
            assert stats['total_size'] == 1536, f"总大小应该是1536，实际是{stats['total_size']}"
            
            # 测试格式化大小
            assert ManifestManager.format_size(1024) == "1.0KB", "大小格式化应该正确"
            assert ManifestManager.format_size(1048576) == "1.0MB", "大小格式化应该正确"
            
            print("  ✅ ManifestManager所有功能测试通过")
            return True
            
    except Exception as e:
        print(f"  ❌ ManifestManager测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_crawler_anti_bot():
    """测试网页爬虫反爬功能"""
    print("🧪 测试网页爬虫反爬功能...")
    
    try:
        from src.processors.web_crawler import WebCrawler
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            crawler = WebCrawler(temp_dir)
            
            # 测试配置
            assert hasattr(crawler, 'anti_bot_config'), "应该有反爬配置"
            assert crawler.anti_bot_config['min_delay'] > 0, "最小延迟应该大于0"
            assert crawler.anti_bot_config['max_retries'] > 0, "最大重试次数应该大于0"
            
            # 测试失败URL跟踪
            assert hasattr(crawler, 'failed_urls'), "应该有失败URL集合"
            assert hasattr(crawler, 'retry_counts'), "应该有重试计数"
            
            # 测试智能请求方法
            assert hasattr(crawler, '_smart_request'), "应该有智能请求方法"
            
            print("  ✅ 网页爬虫反爬功能测试通过")
            return True
            
    except Exception as e:
        print(f"  ❌ 网页爬虫反爬功能测试失败: {e}")
        return False

def test_kb_interface_stats():
    """测试知识库界面统计功能"""
    print("🧪 测试知识库界面统计功能...")
    
    try:
        from src.kb.kb_interface import KBInterface
        
        # 创建知识库界面实例
        kb_interface = KBInterface()
        
        # 测试方法存在
        assert hasattr(kb_interface, 'render_kb_manager'), "应该有知识库管理渲染方法"
        assert hasattr(kb_interface, 'render_kb_creator'), "应该有知识库创建渲染方法"
        
        print("  ✅ 知识库界面统计功能测试通过")
        return True
        
    except Exception as e:
        print(f"  ❌ 知识库界面统计功能测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("  ManifestManager 和相关功能单元测试")
    print("=" * 60)
    
    tests = [
        ("ManifestManager功能", test_manifest_manager),
        ("网页爬虫反爬功能", test_web_crawler_anti_bot),
        ("知识库界面统计", test_kb_interface_stats)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有单元测试通过！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
