#!/usr/bin/env python3
"""
测试LLM连接
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.llm_manager import get_llm_manager

def test_llm_connection():
    """测试LLM连接"""
    print("🔍 测试LLM连接...")
    
    # 获取LLM管理器
    llm_manager = get_llm_manager()
    
    # 创建Ollama LLM
    llm = llm_manager.get_llm(
        provider="Ollama",
        model="gpt-oss:20b", 
        key="",
        url="http://localhost:11434"
    )
    
    if llm is None:
        print("❌ LLM创建失败")
        return False
    
    print("✅ LLM创建成功")
    
    # 测试简单调用
    try:
        print("🔄 测试LLM调用...")
        response = llm.complete("Hello")
        print(f"✅ LLM调用成功: {response.text[:50]}...")
        return True
    except Exception as e:
        print(f"❌ LLM调用失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_llm_connection()
    sys.exit(0 if success else 1)
