#!/usr/bin/env python3
"""
测试推荐问题日志输出
模拟推荐问题生成并检查日志格式
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.chat_utils_improved import generate_follow_up_questions_safe
from src.logging.log_manager import LogManager

def test_suggestion_logging():
    """测试推荐问题日志记录"""
    print("🧪 测试推荐问题日志记录...")
    
    # 初始化日志管理器
    logger = LogManager()
    
    # 模拟上下文
    context = "樊登读书会通过友好的用户界面设计，确保用户一打开界面就能毫无障碍地使用，无需任何指导即可顺畅操作。"
    existing_questions = ["界面设计有什么特点？"]
    
    print(f"📝 上下文: {context}")
    print(f"📝 已有问题: {existing_questions}")
    print()
    
    # 生成推荐问题
    suggestions = generate_follow_up_questions_safe(
        context_text=context,
        num_questions=3,
        existing_questions=existing_questions,
        timeout=15,
        logger=logger
    )
    
    print("✨ 生成的推荐问题:")
    if suggestions:
        # 模拟日志输出格式
        logger.info(f"✨ 生成 {len(suggestions)} 个新推荐问题")
        for i, q in enumerate(suggestions[:3], 1):
            logger.info(f"   {i}. {q}")
            print(f"   {i}. {q}")
    else:
        logger.info("⚠️ 推荐问题生成失败")
        print("   ⚠️ 未生成推荐问题")
    
    return len(suggestions) > 0

def simulate_log_output():
    """模拟期望的日志输出格式"""
    print("\n📋 期望的日志输出格式:")
    print("ℹ️ [16:35:07] ✨ 生成 3 个新推荐问题")
    print("ℹ️ [16:35:07]    1. 樊登读书会的用户界面有哪些具体功能？")
    print("ℹ️ [16:35:07]    2. 如何通过界面设计提升用户留存率？")
    print("ℹ️ [16:35:07]    3. 界面设计对用户学习效果有何影响？")

if __name__ == "__main__":
    print("=" * 60)
    print("  推荐问题日志测试")
    print("=" * 60)
    
    success = test_suggestion_logging()
    simulate_log_output()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 推荐问题生成成功！")
        print("💡 现在应用重启后，日志中会显示具体的推荐问题内容")
    else:
        print("❌ 推荐问题生成失败")
    print("=" * 60)
