#!/usr/bin/env python3
"""快速测试推荐问题生成"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.chat_utils_improved import generate_follow_up_questions_safe
from src.logging.log_manager import LogManager

# 创建模拟LLM
class MockLLM:
    def complete(self, prompt):
        class MockResponse:
            text = "樊登读书会的界面有什么特色功能？\n用户体验设计的核心原则是什么？\n如何评估界面设计的效果？"
        return MockResponse()

def test_with_llm():
    logger = LogManager()
    mock_llm = MockLLM()
    
    context = "樊登读书会通过友好的用户界面设计，确保用户一打开界面就能毫无障碍地使用。"
    
    print("🧪 测试推荐问题生成...")
    print(f"📝 上下文: {context}")
    
    suggestions = generate_follow_up_questions_safe(
        context_text=context,
        num_questions=3,
        existing_questions=[],
        logger=logger,
        llm_model=mock_llm
    )
    
    print(f"✨ 生成结果: {suggestions}")
    
    # 检查是否是fallback
    fallback_questions = [
        "这本书的核心观点是什么？",
        "作者的写作背景如何？", 
        "有哪些实用的阅读技巧？"
    ]
    
    is_fallback = any(q in fallback_questions for q in suggestions)
    
    if is_fallback:
        print("❌ 仍在使用fallback问题")
        return False
    else:
        print("✅ 使用了真正的LLM生成")
        return True

if __name__ == "__main__":
    success = test_with_llm()
    print(f"\n结果: {'成功' if success else '失败'}")
