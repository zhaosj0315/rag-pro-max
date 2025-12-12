#!/usr/bin/env python3
"""
测试全局LLM设置
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.model_manager import set_global_llm_model
from llama_index.core import Settings

def test_global_llm():
    """测试全局LLM设置"""
    print("🔍 测试全局LLM设置...")
    
    # 设置全局LLM
    success = set_global_llm_model(
        provider="Ollama",
        model_name="gpt-oss:20b",
        api_url="http://localhost:11434"
    )
    
    if not success:
        print("❌ 全局LLM设置失败")
        return False
    
    print("✅ 全局LLM设置成功")
    
    # 测试LLM调用
    try:
        print("🔄 测试全局LLM调用...")
        if Settings.llm:
            response = Settings.llm.complete("Hello")
            print(f"✅ 全局LLM调用成功: {response.text[:50]}...")
            return True
        else:
            print("❌ Settings.llm为空")
            return False
    except Exception as e:
        print(f"❌ 全局LLM调用失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_global_llm()
    sys.exit(0 if success else 1)
