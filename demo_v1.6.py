#!/usr/bin/env python3
"""
RAG Pro Max v1.6 功能演示
演示查询改写和文档预览功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.query.query_rewriter import QueryRewriter
from src.kb.document_viewer import DocumentViewer
from llama_index.llms.openai import OpenAI


def demo_query_rewriter():
    """演示查询改写功能"""
    print("\n" + "="*60)
    print("🎯 查询改写功能演示")
    print("="*60)
    
    # 创建查询改写器（使用测试 LLM）
    llm = OpenAI(model="gpt-3.5-turbo", api_key="test")
    rewriter = QueryRewriter(llm)
    
    # 测试用例
    test_queries = [
        ("RAG是啥", "短查询 + 口语化"),
        ("这个咋用啊", "口语化表达"),
        ("文档处理", "查询过短"),
        ("什么是检索增强生成技术？", "正常查询"),
    ]
    
    for query, desc in test_queries:
        print(f"\n📝 测试查询: {query}")
        print(f"   类型: {desc}")
        
        should, reason = rewriter.should_rewrite(query)
        print(f"   需要改写: {'✅ 是' if should else '❌ 否'}")
        if should:
            print(f"   原因: {reason}")
        print()


def demo_document_viewer():
    """演示文档预览功能"""
    print("\n" + "="*60)
    print("📄 文档预览功能演示")
    print("="*60)
    
    viewer = DocumentViewer()
    
    # 创建测试文件
    import tempfile
    test_content = """
# RAG Pro Max 测试文档

这是一个测试文档，用于演示文档预览功能。

## 功能特性

1. 查询改写 - 自动优化用户查询
2. 文档预览 - 上传前/后预览文档
3. 精细化管理 - 查看、编辑、删除文档

## 技术实现

使用 LlamaIndex 和 Streamlit 构建。
""" * 5  # 重复5次，制造长文本
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        print(f"\n📁 测试文件: {os.path.basename(temp_path)}")
        print(f"   大小: {len(test_content)} 字符")
        
        # 预览文件
        preview = viewer.preview_file(temp_path, max_chars=200)
        print(f"\n📖 预览内容 (前200字符):")
        print("-" * 60)
        print(preview)
        print("-" * 60)
        
        # 测试知识库文档列表
        print(f"\n📚 知识库文档列表:")
        kb_name = "test_kb"
        docs = viewer.get_kb_documents(kb_name)
        if docs:
            for doc in docs:
                print(f"   📄 {doc.name} ({doc.size_mb:.2f} MB)")
        else:
            print(f"   ℹ️ 知识库 '{kb_name}' 中暂无文档")
        
    finally:
        os.unlink(temp_path)


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 RAG Pro Max v1.6 功能演示")
    print("="*60)
    print("\n新增功能:")
    print("  1. 🎯 查询改写 (Query Rewriting)")
    print("  2. 📄 文档预览 (Document Preview)")
    print()
    
    try:
        # 演示查询改写
        demo_query_rewriter()
        
        # 演示文档预览
        demo_document_viewer()
        
        print("\n" + "="*60)
        print("✅ 演示完成！")
        print("="*60)
        print("\n💡 提示:")
        print("  - 启动应用: streamlit run src/apppro.py")
        print("  - 查看文档: docs/V1.6_FEATURES.md")
        print("  - 运行测试: python tests/test_query_rewriter.py")
        print()
        
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
