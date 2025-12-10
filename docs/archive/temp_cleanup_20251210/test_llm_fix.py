#!/usr/bin/env python3
"""
测试LLM设置修复
验证推荐问题生成是否使用真正的LLM而不是fallback
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from llama_index.core import Settings
from src.chat_utils_improved import generate_follow_up_questions_safe

def test_llm_availability():
    """测试LLM可用性"""
    print("🧪 测试LLM可用性...")
    
    print(f"Settings.llm: {getattr(Settings, 'llm', None)}")
    
    # 模拟推荐问题生成
    context = "樊登读书会通过友好的用户界面设计，确保用户一打开界面就能毫无障碍地使用。"
    
    print(f"📝 上下文: {context}")
    
    # 生成推荐问题
    suggestions = generate_follow_up_questions_safe(
        context_text=context,
        num_questions=3,
        existing_questions=[],
        timeout=15
    )
    
    print(f"✨ 生成的推荐问题: {suggestions}")
    
    # 检查是否是fallback问题
    fallback_questions = [
        "这本书的核心观点是什么？",
        "作者的写作背景如何？", 
        "有哪些实用的阅读技巧？"
    ]
    
    is_fallback = any(q in fallback_questions for q in suggestions)
    
    if is_fallback:
        print("❌ 使用了fallback问题，LLM未正确设置")
        return False
    else:
        print("✅ 生成了真正的推荐问题，LLM工作正常")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("  LLM设置修复测试")
    print("=" * 60)
    
    success = test_llm_availability()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ LLM设置正常，推荐问题生成使用真正的LLM")
    else:
        print("❌ LLM设置有问题，需要进一步调试")
        print("💡 建议：确保在推荐问题生成前正确设置LLM模型")
    print("=" * 60)
