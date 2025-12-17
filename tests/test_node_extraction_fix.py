"""
测试节点文本提取修复
验证 "Node must be a TextNode to get text" 错误已解决
"""

import sys
sys.path.insert(0, '/Users/zhaosj/Documents/rag-pro-max')

from src.query.query_processor import QueryProcessor
from src.chat.chat_engine import ChatEngine
from llama_index.core.schema import TextNode, NodeWithScore, IndexNode
from unittest.mock import Mock


def test_extract_node_text_with_textnode():
    """测试提取 TextNode 文本"""
    qp = QueryProcessor()
    text_node = TextNode(text='Test content')
    result = qp._extract_node_text(text_node)
    assert result == 'Test content', f"Expected 'Test content', got {result}"
    print("✅ TextNode extraction passed")


def test_extract_node_text_with_wrapped_node():
    """测试提取被包装的节点"""
    qp = QueryProcessor()
    text_node = TextNode(text='Wrapped content')
    wrapped_node = NodeWithScore(node=text_node, score=0.9)
    result = qp._extract_node_text(wrapped_node)
    assert result == 'Wrapped content', f"Expected 'Wrapped content', got {result}"
    print("✅ Wrapped node extraction passed")


def test_extract_node_text_with_index_node():
    """测试提取 IndexNode（非 TextNode）"""
    qp = QueryProcessor()
    # IndexNode 不是 TextNode，应该返回字符串表示
    index_node = IndexNode(index_id='test_id')
    result = qp._extract_node_text(index_node)
    assert isinstance(result, str), f"Expected string, got {type(result)}"
    # IndexNode 可能返回空字符串，这是可以接受的
    print(f"✅ IndexNode extraction passed: {repr(result)}")


def test_extract_node_text_with_mock_node():
    """测试提取自定义节点对象"""
    qp = QueryProcessor()
    
    # 创建一个简单的对象，只有 text 属性
    class SimpleNode:
        def __init__(self):
            self.text = 'Mock content'
    
    node = SimpleNode()
    result = qp._extract_node_text(node)
    assert result == 'Mock content', f"Expected 'Mock content', got {result}"
    print("✅ Mock node extraction passed")


def test_extract_node_text_with_error_handling():
    """测试错误处理"""
    qp = QueryProcessor()
    
    # 创建一个会抛出异常的对象
    class ErrorNode:
        @property
        def text(self):
            raise Exception("Test error")
        
        def get_content(self):
            raise Exception("Test error")
        
        def get_text(self):
            raise Exception("Test error")
    
    node = ErrorNode()
    result = qp._extract_node_text(node)
    assert isinstance(result, str), f"Expected string, got {type(result)}"
    print(f"✅ Error handling passed: {result}")


def test_no_textnode_get_text_error():
    """验证不会抛出 'Node must be a TextNode to get text' 错误"""
    qp = QueryProcessor()
    
    # 创建一个 IndexNode（不是 TextNode）
    index_node = IndexNode(index_id='test_id')
    
    try:
        result = qp._extract_node_text(index_node)
        print(f"✅ No 'Node must be a TextNode' error: {result[:50]}")
    except Exception as e:
        if "Node must be a TextNode" in str(e):
            raise AssertionError(f"❌ Still getting 'Node must be a TextNode' error: {e}")
        else:
            raise


if __name__ == '__main__':
    print("=" * 60)
    print("  节点文本提取修复测试")
    print("=" * 60)
    
    test_extract_node_text_with_textnode()
    test_extract_node_text_with_wrapped_node()
    test_extract_node_text_with_index_node()
    test_extract_node_text_with_mock_node()
    test_extract_node_text_with_error_handling()
    test_no_textnode_get_text_error()
    
    print("=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)
