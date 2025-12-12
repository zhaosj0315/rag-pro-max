#!/usr/bin/env python3
"""
完整的LLM连接测试
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.llm_manager import get_llm_manager
from src.utils.model_manager import set_global_llm_model
from src.query.query_rewriter import QueryRewriter
from llama_index.core import Settings

def test_complete_llm():
    """测试完整的LLM功能"""
    print("🔍 测试完整LLM功能...")
    
    # 1. 测试LLM管理器
    print("\n1️⃣ 测试LLM管理器...")
    llm_manager = get_llm_manager()
    llm = llm_manager.get_llm(
        provider="Ollama",
        model="gpt-oss:20b", 
        key="",
        url="http://localhost:11434"
    )
    
    if llm is None:
        print("❌ LLM管理器创建失败")
        return False
    
    try:
        response = llm.complete("Hello")
        print(f"✅ LLM管理器调用成功: {response.text[:30]}...")
    except Exception as e:
        print(f"❌ LLM管理器调用失败: {str(e)}")
        return False
    
    # 2. 测试全局LLM设置
    print("\n2️⃣ 测试全局LLM设置...")
    success = set_global_llm_model(
        provider="Ollama",
        model_name="gpt-oss:20b",
        api_url="http://localhost:11434"
    )
    
    if not success:
        print("❌ 全局LLM设置失败")
        return False
    
    try:
        if Settings.llm:
            response = Settings.llm.complete("Hello")
            print(f"✅ 全局LLM调用成功: {response.text[:30]}...")
        else:
            print("❌ Settings.llm为空")
            return False
    except Exception as e:
        print(f"❌ 全局LLM调用失败: {str(e)}")
        return False
    
    # 3. 测试查询改写器
    print("\n3️⃣ 测试查询改写器...")
    try:
        query_rewriter = QueryRewriter(Settings.llm)
        should_rewrite, reason = query_rewriter.should_rewrite("这个怎么样？")
        print(f"✅ 查询改写器初始化成功，检测结果: {should_rewrite} ({reason})")
        
        if should_rewrite:
            rewritten = query_rewriter.suggest_rewrite("这个怎么样？")
            if rewritten:
                print(f"✅ 查询改写成功: 这个怎么样？ → {rewritten}")
            else:
                print("⚠️ 查询改写返回空结果")
        
        return True
    except Exception as e:
        print(f"❌ 查询改写器测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_complete_llm()
    print(f"\n{'='*50}")
    print(f"测试结果: {'✅ 全部通过' if success else '❌ 存在问题'}")
    sys.exit(0 if success else 1)
