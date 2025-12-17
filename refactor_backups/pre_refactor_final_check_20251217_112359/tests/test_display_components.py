"""
测试 UI 展示组件
Stage 3.1 - 纯展示组件测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ui.display_components import (
    get_relevance_label,
    format_time_duration,
    format_token_count
)


def test_relevance_label():
    """测试相关性标签"""
    print("测试相关性标签...")
    
    # 高度相关
    assert "高度相关" in get_relevance_label(0.9)
    assert "高度相关" in get_relevance_label(0.8)
    
    # 相关
    assert "相关" in get_relevance_label(0.7)
    assert "相关" in get_relevance_label(0.6)
    
    # 一般相关
    assert "一般相关" in get_relevance_label(0.5)
    assert "一般相关" in get_relevance_label(0.3)
    
    print("✅ 相关性标签测试通过")


def test_time_formatting():
    """测试时间格式化"""
    print("测试时间格式化...")
    
    # 毫秒
    assert "ms" in format_time_duration(0.5)
    assert "500ms" == format_time_duration(0.5)
    
    # 秒
    assert "秒" in format_time_duration(5.5)
    assert "5.5秒" == format_time_duration(5.5)
    
    # 分钟
    assert "分" in format_time_duration(65)
    assert "1分5秒" == format_time_duration(65)
    
    print("✅ 时间格式化测试通过")


def test_token_formatting():
    """测试 token 格式化"""
    print("测试 token 格式化...")
    
    # 小于 1000
    assert "500 字符" == format_token_count(500)
    
    # 1K-10K
    assert "K 字符" in format_token_count(5000)
    assert "5.0K 字符" == format_token_count(5000)
    
    # 大于 10K
    assert "万 字符" in format_token_count(50000)
    assert "5.0万 字符" == format_token_count(50000)
    
    print("✅ Token 格式化测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*50)
    print("UI 展示组件测试")
    print("="*50 + "\n")
    
    try:
        test_relevance_label()
        test_time_formatting()
        test_token_formatting()
        
        print("\n" + "="*50)
        print("✅ 所有测试通过！")
        print("="*50)
        return True
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
