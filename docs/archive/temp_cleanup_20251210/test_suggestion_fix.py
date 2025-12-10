#!/usr/bin/env python3
"""
测试推荐问题重复修复
验证修复后的推荐系统不会生成重复问题
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.chat_utils_improved import generate_follow_up_questions_safe

def test_suggestion_deduplication():
    """测试推荐问题去重功能"""
    print("🧪 测试推荐问题去重功能...")
    
    # 模拟上下文
    context = "这本书讲述了如何培养创新思维，作者通过大量案例说明了创新的重要性。"
    
    # 模拟已存在的问题
    existing_questions = [
        "这本书的核心观点是什么？",
        "作者的写作背景如何？",
        "有哪些实用的阅读技巧？"
    ]
    
    print(f"📝 已存在问题: {existing_questions}")
    
    # 生成新推荐
    new_suggestions = generate_follow_up_questions_safe(
        context_text=context,
        num_questions=3,
        existing_questions=existing_questions,
        timeout=15
    )
    
    print(f"✨ 新生成推荐: {new_suggestions}")
    
    # 检查是否有重复
    duplicates = []
    for new_q in new_suggestions:
        for existing_q in existing_questions:
            if new_q.strip() == existing_q.strip():
                duplicates.append(new_q)
    
    if duplicates:
        print(f"❌ 发现重复问题: {duplicates}")
        return False
    else:
        print("✅ 没有重复问题，去重功能正常")
        return True

def test_multiple_generations():
    """测试多次生成的累积效果"""
    print("\n🧪 测试多次生成累积效果...")
    
    context = "这本书讲述了如何培养创新思维。"
    all_generated = []
    
    # 模拟3次生成
    for i in range(3):
        print(f"\n第 {i+1} 次生成:")
        suggestions = generate_follow_up_questions_safe(
            context_text=context,
            num_questions=3,
            existing_questions=all_generated,
            timeout=10
        )
        
        print(f"  生成: {suggestions}")
        
        # 检查是否与之前生成的重复
        duplicates = set(suggestions) & set(all_generated)
        if duplicates:
            print(f"  ❌ 发现重复: {duplicates}")
            return False
        
        all_generated.extend(suggestions)
        print(f"  ✅ 累积问题数: {len(all_generated)}")
    
    print(f"\n📊 总共生成 {len(all_generated)} 个不重复问题")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("  推荐问题重复修复测试")
    print("=" * 60)
    
    success = True
    
    # 测试1: 基本去重
    success &= test_suggestion_deduplication()
    
    # 测试2: 多次生成累积
    success &= test_multiple_generations()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 所有测试通过！推荐问题重复问题已修复")
    else:
        print("❌ 测试失败，需要进一步调试")
    print("=" * 60)
