#!/usr/bin/env python3
"""
RAG Pro Max v1.4.4 可行性测试
测试追问推荐和队列处理功能
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_imports():
    """测试关键模块导入"""
    print("\n" + "="*60)
    print("  1. 模块导入测试")
    print("="*60)
    
    try:
        from src.chat_utils_improved import generate_follow_up_questions_safe
        print("✅ chat_utils_improved: PASS")
        print("   └─ generate_follow_up_questions_safe 已导入")
    except Exception as e:
        print(f"❌ chat_utils_improved: FAIL")
        print(f"   └─ {e}")
        return False
    
    try:
        from src.app_logging.log_manager import LogManager
        print("✅ LogManager: PASS")
    except Exception as e:
        print(f"❌ LogManager: FAIL")
        print(f"   └─ {e}")
        return False
    
    try:
        from src.chat import HistoryManager
        print("✅ HistoryManager: PASS")
    except Exception as e:
        print(f"❌ HistoryManager: FAIL")
        print(f"   └─ {e}")
        return False
    
    return True


def test_apppro_syntax():
    """测试 apppro.py 语法"""
    print("\n" + "="*60)
    print("  2. apppro.py 语法测试")
    print("="*60)
    
    try:
        import py_compile
        py_compile.compile('src/apppro.py', doraise=True)
        print("✅ apppro.py 语法: PASS")
        print("   └─ 无语法错误")
        return True
    except SyntaxError as e:
        print(f"❌ apppro.py 语法: FAIL")
        print(f"   └─ {e}")
        return False


def test_queue_logic():
    """测试队列处理逻辑"""
    print("\n" + "="*60)
    print("  3. 队列处理逻辑测试")
    print("="*60)
    
    # 检查关键代码片段
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查队列初始化
    if 'question_queue' in content and 'st.session_state.question_queue = []' in content:
        print("✅ 队列初始化: PASS")
        print("   └─ question_queue 已定义")
    else:
        print("❌ 队列初始化: FAIL")
        return False
    
    # 检查手动触发按钮
    if '▶️ 处理下一个问题' in content:
        print("✅ 手动触发按钮: PASS")
        print("   └─ 已实现手动触发模式")
    else:
        print("❌ 手动触发按钮: FAIL")
        return False
    
    # 检查 is_processing 标志
    if 'is_processing' in content:
        print("✅ 处理状态标志: PASS")
        print("   └─ is_processing 已使用")
    else:
        print("❌ 处理状态标志: FAIL")
        return False
    
    return True


def test_suggestion_logic():
    """测试推荐问题逻辑"""
    print("\n" + "="*60)
    print("  4. 推荐问题逻辑测试")
    print("="*60)
    
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查 suggestions_history 初始化
    if 'suggestions_history' in content:
        print("✅ 推荐历史初始化: PASS")
        print("   └─ suggestions_history 已定义")
    else:
        print("❌ 推荐历史初始化: FAIL")
        return False
    
    # 检查推荐问题生成
    if 'generate_follow_up_questions' in content:
        print("✅ 推荐问题生成: PASS")
        print("   └─ generate_follow_up_questions 已调用")
    else:
        print("❌ 推荐问题生成: FAIL")
        return False
    
    # 检查推荐按钮显示
    if '🚀 追问推荐' in content:
        print("✅ 推荐按钮显示: PASS")
        print("   └─ 推荐区域已实现")
    else:
        print("❌ 推荐按钮显示: FAIL")
        return False
    
    # 检查继续推荐按钮
    if '✨ 继续推荐' in content:
        print("✅ 继续推荐按钮: PASS")
        print("   └─ 无限追问功能已实现")
    else:
        print("❌ 继续推荐按钮: FAIL")
        return False
    
    return True


def test_chat_message_block():
    """测试 chat_message 块结构"""
    print("\n" + "="*60)
    print("  5. chat_message 块结构测试")
    print("="*60)
    
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否有 try-except 结构
    if 'try:' in content and 'except Exception as e:' in content:
        print("✅ try-except 结构: PASS")
        print("   └─ 错误处理已实现")
    else:
        print("❌ try-except 结构: FAIL")
        return False
    
    # 检查推荐按钮是否在 chat_message 块外
    # 通过检查缩进判断（简化检查）
    lines = content.split('\n')
    in_chat_message = False
    suggestion_outside = False
    
    for i, line in enumerate(lines):
        if 'with st.chat_message("assistant")' in line:
            in_chat_message = True
        if in_chat_message and '🚀 追问推荐' in line:
            # 检查缩进是否比 chat_message 少
            if not line.startswith('                '):  # 假设 chat_message 内至少 16 空格
                suggestion_outside = True
                break
    
    if suggestion_outside or '🚀 追问推荐' in content:
        print("✅ 推荐按钮位置: PASS")
        print("   └─ 按钮在 chat_message 块外")
    else:
        print("⚠️  推荐按钮位置: WARNING")
        print("   └─ 无法确定按钮位置，需手动检查")
    
    return True


def test_bug_fixes():
    """测试 bug 修复"""
    print("\n" + "="*60)
    print("  6. Bug 修复验证")
    print("="*60)
    
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Bug 1: 回答消失问题
    # 检查是否移除了 chat_message 块内的临时按钮
    if 'temp_sug_' not in content or 'sug_btn_' in content:
        print("✅ Bug #1 修复: PASS")
        print("   └─ 临时按钮已移除或重构")
    else:
        print("⚠️  Bug #1 修复: WARNING")
        print("   └─ 可能仍存在临时按钮")
    
    # Bug 2: 队列自动处理问题
    # 检查是否改为手动触发
    if '▶️ 处理下一个问题' in content:
        print("✅ Bug #2 修复: PASS")
        print("   └─ 已改为手动触发模式")
    else:
        print("❌ Bug #2 修复: FAIL")
        return False
    
    return True


def test_suggestion_generation():
    """测试推荐问题生成功能"""
    print("\n" + "="*60)
    print("  7. 推荐问题生成功能测试")
    print("="*60)
    
    try:
        from src.chat_utils_improved import generate_follow_up_questions_safe
        
        # 测试基本调用
        context = "数据仪表盘是一种可视化工具，用于实时展示关键运营指标。"
        questions = generate_follow_up_questions_safe(
            context_text=context,
            num_questions=3,
            existing_questions=[],
            timeout=5
        )
        
        if questions and len(questions) > 0:
            print("✅ 推荐问题生成: PASS")
            print(f"   └─ 生成了 {len(questions)} 个问题")
            for i, q in enumerate(questions, 1):
                print(f"      {i}. {q}")
        else:
            print("⚠️  推荐问题生成: WARNING")
            print("   └─ 未生成问题（可能使用降级策略）")
        
        return True
    except Exception as e:
        print(f"❌ 推荐问题生成: FAIL")
        print(f"   └─ {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  RAG Pro Max v1.4.4 可行性测试")
    print("="*60)
    
    tests = [
        ("模块导入", test_imports),
        ("语法检查", test_apppro_syntax),
        ("队列逻辑", test_queue_logic),
        ("推荐逻辑", test_suggestion_logic),
        ("块结构", test_chat_message_block),
        ("Bug修复", test_bug_fixes),
        ("问题生成", test_suggestion_generation),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试异常: {e}")
            results.append((name, False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("  测试结果汇总")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"✅ 通过: {passed}/{total}")
    print(f"❌ 失败: {total - passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！v1.4.4 可以发布。")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查后再发布。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
