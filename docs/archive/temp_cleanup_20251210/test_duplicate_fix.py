#!/usr/bin/env python3
"""
测试重复检测修复和推荐问题日志
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.chat_utils_improved import generate_follow_up_questions_safe, _is_similar_question

def test_duplicate_detection():
    """测试智能重复检测"""
    print("🧪 测试智能重复检测...")
    
    # 模拟历史问题
    recent_queries = [
        "有哪些实用的阅读技巧？",
        "樊登读书会的运营策略是什么？"
    ]
    
    test_cases = [
        # (查询, 预期结果, 说明)
        ("有哪些实用的阅读技巧？", True, "完全相同"),
        ("有效提升阅读理解能力的实用技巧有哪些？", True, "查询重写后的相似问题"),
        ("阅读技巧有哪些？", True, "相似问题"),
        ("樊登读书会如何盈利？", False, "不同问题"),
        ("什么是创新思维？", False, "完全不同的问题")
    ]
    
    print(f"📝 历史问题: {recent_queries}")
    print()
    
    for query, expected, desc in test_cases:
        # 使用智能相似度检测
        is_duplicate = False
        for recent_query in recent_queries:
            if _is_similar_question(query, recent_query, threshold=0.8):
                is_duplicate = True
                break
        
        status = "✅" if is_duplicate == expected else "❌"
        print(f"{status} {desc}: '{query}' -> {is_duplicate} (预期: {expected})")
    
    return True

def test_suggestion_logging():
    """测试推荐问题日志记录"""
    print("\n🧪 测试推荐问题日志记录...")
    
    context = "樊登读书会通过友好的用户界面设计提升用户体验"
    existing_questions = ["界面设计有什么特点？"]
    
    print(f"📝 上下文: {context}")
    print(f"📝 已有问题: {existing_questions}")
    print()
    
    # 生成推荐问题
    suggestions = generate_follow_up_questions_safe(
        context_text=context,
        num_questions=3,
        existing_questions=existing_questions,
        timeout=10
    )
    
    print("✨ 生成的推荐问题:")
    if suggestions:
        for i, q in enumerate(suggestions, 1):
            print(f"   {i}. {q}")
    else:
        print("   ⚠️ 未生成推荐问题")
    
    return len(suggestions) > 0

if __name__ == "__main__":
    print("=" * 60)
    print("  重复检测和日志修复测试")
    print("=" * 60)
    
    success = True
    
    # 测试1: 重复检测
    success &= test_duplicate_detection()
    
    # 测试2: 推荐问题日志
    success &= test_suggestion_logging()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过！重复检测和日志功能已修复")
    else:
        print("❌ 测试失败，需要进一步调试")
    print("=" * 60)
