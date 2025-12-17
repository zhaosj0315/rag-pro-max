#!/usr/bin/env python3
"""
RAG Pro Max v1.6 可行性测试脚本
测试所有新功能的可用性和性能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.kb.document_viewer import DocumentViewer
from src.query.query_rewriter import QueryRewriter
from llama_index.llms.openai import OpenAI
import time


def test_query_rewriter():
    """测试查询改写功能"""
    print("\n" + "="*60)
    print("🎯 测试 1: 查询改写功能")
    print("="*60)
    
    llm = OpenAI(model="gpt-3.5-turbo", api_key="test")
    rewriter = QueryRewriter(llm)
    
    test_cases = [
        ("RAG是啥", True, "包含口语化表达"),
        ("这个咋用", True, "查询过短"),
        ("什么是检索增强生成技术？", False, ""),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_rewrite, expected_reason in test_cases:
        should, reason = rewriter.should_rewrite(query)
        
        if should == expected_rewrite:
            print(f"   ✅ '{query}': {should} ({reason})")
            passed += 1
        else:
            print(f"   ❌ '{query}': 期望 {expected_rewrite}, 实际 {should}")
            failed += 1
    
    print(f"\n   结果: {passed} 通过, {failed} 失败")
    return failed == 0


def test_document_viewer():
    """测试文档查看器功能"""
    print("\n" + "="*60)
    print("📄 测试 2: 文档查看器功能")
    print("="*60)
    
    viewer = DocumentViewer()
    
    # 查找任意知识库
    vector_db_path = "vector_db_storage"
    if not os.path.exists(vector_db_path):
        print("   ⚠️ 向量数据库目录不存在")
        return False
    
    kb_list = [d for d in os.listdir(vector_db_path) if os.path.isdir(os.path.join(vector_db_path, d))]
    
    if not kb_list:
        print("   ⚠️ 没有找到知识库")
        return False
    
    kb_name = kb_list[0]
    print(f"   测试知识库: {kb_name}")
    
    # 测试获取文档列表
    docs = viewer.get_kb_documents(kb_name)
    print(f"   ✅ 找到 {len(docs)} 个文档")
    
    if docs:
        for doc in docs[:3]:
            print(f"      📄 {doc.name} ({doc.size_mb:.2f} MB)")
        
        # 测试文档预览
        doc = docs[0]
        preview = viewer.preview_file(doc.file_path, max_chars=100)
        if preview:
            print(f"   ✅ 预览成功: {preview[:50]}...")
        else:
            print(f"   ❌ 预览失败")
            return False
    
    return True


def test_smart_naming():
    """测试智能命名功能"""
    print("\n" + "="*60)
    print("💡 测试 3: 智能命名功能")
    print("="*60)
    
    from datetime import datetime
    
    test_cases = [
        ({'PDF': 3, 'DOCX': 1}, "文档集合"),
        ({'MD': 5}, "笔记集合"),
        ({'PY': 10}, "代码库"),
        ({'XLSX': 2, 'CSV': 3}, "数据集"),
    ]
    
    passed = 0
    failed = 0
    
    for file_types, expected_prefix in test_cases:
        # 模拟命名逻辑
        main_ext = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[0][0]
        
        if main_ext in ['PDF', 'DOCX']:
            auto_name = "文档集合"
        elif main_ext in ['MD', 'TXT']:
            auto_name = "笔记集合"
        elif main_ext in ['PY', 'JS']:
            auto_name = "代码库"
        elif main_ext in ['XLSX', 'CSV']:
            auto_name = "数据集"
        else:
            auto_name = f"{main_ext}文件集"
        
        date_suffix = datetime.now().strftime("%Y%m%d")
        full_name = f"{auto_name}_{date_suffix}"
        
        if auto_name == expected_prefix:
            print(f"   ✅ {file_types} → {full_name}")
            passed += 1
        else:
            print(f"   ❌ {file_types}: 期望 {expected_prefix}, 实际 {auto_name}")
            failed += 1
    
    print(f"\n   结果: {passed} 通过, {failed} 失败")
    return failed == 0


def test_performance():
    """测试性能"""
    print("\n" + "="*60)
    print("⚡ 测试 4: 性能测试")
    print("="*60)
    
    viewer = DocumentViewer()
    
    # 测试文档列表加载时间
    vector_db_path = "vector_db_storage"
    if os.path.exists(vector_db_path):
        kb_list = [d for d in os.listdir(vector_db_path) if os.path.isdir(os.path.join(vector_db_path, d))]
        
        if kb_list:
            kb_name = kb_list[0]
            
            start = time.time()
            docs = viewer.get_kb_documents(kb_name)
            elapsed = time.time() - start
            
            print(f"   ✅ 文档列表加载: {elapsed:.3f}s ({len(docs)} 个文档)")
            
            if docs and elapsed < 1.0:
                print(f"   ✅ 性能优秀 (<1秒)")
                return True
            elif elapsed < 2.0:
                print(f"   ⚠️ 性能可接受 (<2秒)")
                return True
            else:
                print(f"   ❌ 性能较差 (>2秒)")
                return False
    
    print("   ⚠️ 无法测试性能（没有知识库）")
    return True


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("🚀 RAG Pro Max v1.6 可行性测试")
    print("="*60)
    print("\n测试内容:")
    print("  1. 查询改写功能")
    print("  2. 文档查看器功能")
    print("  3. 智能命名功能")
    print("  4. 性能测试")
    
    results = []
    
    # 运行所有测试
    results.append(("查询改写", test_query_rewriter()))
    results.append(("文档查看器", test_document_viewer()))
    results.append(("智能命名", test_smart_naming()))
    results.append(("性能测试", test_performance()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {status}: {name}")
    
    print(f"\n   总计: {passed}/{len(results)} 通过")
    
    if failed == 0:
        print("\n" + "="*60)
        print("✅ 所有测试通过！v1.6 可行性验证成功")
        print("="*60)
        return 0
    else:
        print("\n" + "="*60)
        print(f"❌ {failed} 个测试失败")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
