"""
查询改写模块测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.query.query_rewriter import QueryRewriter
from llama_index.llms.openai import OpenAI


def test_should_rewrite():
    """测试是否需要改写判断"""
    print("\n=== 测试查询改写判断 ===")
    
    # 创建一个简单的 LLM（不实际调用）
    llm = OpenAI(model="gpt-3.5-turbo", api_key="test")
    rewriter = QueryRewriter(llm)
    
    # 测试短查询
    should, reason = rewriter.should_rewrite("RAG是啥")
    print(f"短查询 'RAG是啥': {should} ({reason})")
    assert should == True, "短查询应该需要改写"
    
    # 测试口语化查询
    should, reason = rewriter.should_rewrite("这个咋用啊")
    print(f"口语化查询 '这个咋用啊': {should} ({reason})")
    assert should == True, "口语化查询应该需要改写"
    
    # 测试正常查询
    should, reason = rewriter.should_rewrite("什么是检索增强生成技术？")
    print(f"正常查询: {should} ({reason})")
    assert should == False, "正常查询不需要改写"
    
    # 测试低相似度
    should, reason = rewriter.should_rewrite("正常查询", top_score=0.3)
    print(f"低相似度查询: {should} ({reason})")
    assert should == True, "低相似度应该需要改写"
    
    print("✅ 查询改写判断测试通过")


def test_document_viewer():
    """测试文档查看器"""
    print("\n=== 测试文档查看器 ===")
    
    from src.kb.document_viewer import DocumentViewer
    
    viewer = DocumentViewer()
    
    # 测试获取知识库文档（如果存在）
    kb_name = "test_kb"
    docs = viewer.get_kb_documents(kb_name)
    print(f"知识库 '{kb_name}' 文档数: {len(docs)}")
    
    # 测试预览文件（创建临时文件）
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("这是测试内容\n" * 100)
        temp_path = f.name
    
    try:
        preview = viewer.preview_file(temp_path, max_chars=100)
        print(f"文件预览: {preview[:50]}...")
        assert len(preview) <= 150, "预览内容应该被截断"
        print("✅ 文档查看器测试通过")
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    try:
        test_should_rewrite()
        test_document_viewer()
        print("\n" + "="*50)
        print("✅ 所有测试通过！")
        print("="*50)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
