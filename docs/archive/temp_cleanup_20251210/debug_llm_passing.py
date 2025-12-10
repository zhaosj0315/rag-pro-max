#!/usr/bin/env python3
"""
调试LLM传递问题
检查推荐问题生成时LLM是否正确传递
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.chat_utils_improved import generate_follow_up_questions_safe

def debug_llm_passing():
    """调试LLM传递"""
    print("🔍 调试LLM传递问题...")
    
    # 模拟上下文
    context = "樊登读书会通过友好的用户界面设计，确保用户一打开界面就能毫无障碍地使用。"
    
    print(f"📝 上下文: {context}")
    print()
    
    # 测试1: 不传递LLM (应该使用fallback)
    print("🧪 测试1: 不传递LLM参数")
    suggestions1 = generate_follow_up_questions_safe(
        context_text=context,
        num_questions=3,
        existing_questions=[],
        llm_model=None
    )
    print(f"结果: {suggestions1}")
    
    # 检查是否是fallback
    fallback_questions = [
        "这本书的核心观点是什么？",
        "作者的写作背景如何？", 
        "有哪些实用的阅读技巧？"
    ]
    
    is_fallback1 = any(q in fallback_questions for q in suggestions1)
    print(f"是否使用fallback: {is_fallback1}")
    print()
    
    # 测试2: 传递模拟LLM
    print("🧪 测试2: 传递模拟LLM")
    
    # 创建模拟LLM
    class MockLLM:
        def complete(self, prompt):
            class MockResponse:
                text = "樊登读书会的界面有什么特色功能？\n用户体验设计的核心原则是什么？\n如何评估界面设计的效果？"
            return MockResponse()
    
    mock_llm = MockLLM()
    
    suggestions2 = generate_follow_up_questions_safe(
        context_text=context,
        num_questions=3,
        existing_questions=[],
        llm_model=mock_llm
    )
    print(f"结果: {suggestions2}")
    
    is_fallback2 = any(q in fallback_questions for q in suggestions2)
    print(f"是否使用fallback: {is_fallback2}")
    
    return not is_fallback2

if __name__ == "__main__":
    print("=" * 60)
    print("  LLM传递调试")
    print("=" * 60)
    
    success = debug_llm_passing()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ LLM传递正常，推荐问题使用真正的LLM生成")
    else:
        print("❌ LLM传递有问题，仍在使用fallback")
        print("💡 需要检查应用中的LLM传递逻辑")
    print("=" * 60)
