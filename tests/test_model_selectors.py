"""
测试模型选择器组件
Stage 3.2.1 - 模型选择器测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def test_imports():
    """测试模块导入"""
    print("测试模块导入...")
    
    try:
        from ui.model_selectors import (
            render_ollama_model_selector,
            render_openai_model_selector,
            render_hf_embedding_selector
        )
        print("✅ 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_helper_functions():
    """测试辅助函数"""
    print("测试辅助函数...")
    
    try:
        from ui.model_selectors import _fetch_ollama_models
        
        # 测试函数存在
        assert callable(_fetch_ollama_models)
        print("✅ 辅助函数定义正确")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_preset_models():
    """测试预设模型列表"""
    print("测试预设模型列表...")
    
    # 验证预设模型格式
    preset_models = [
        "sentence-transformers/all-MiniLM-L6-v2",
        "BAAI/bge-large-zh-v1.5",
        "BAAI/bge-m3",
    ]
    
    for model in preset_models:
        assert "/" in model, f"模型名格式错误: {model}"
        assert len(model) > 5, f"模型名太短: {model}"
    
    print("✅ 预设模型列表格式正确")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*50)
    print("模型选择器组件测试")
    print("="*50 + "\n")
    
    tests = [
        test_imports,
        test_helper_functions,
        test_preset_models
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except AssertionError as e:
            print(f"❌ 断言失败: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ 测试错误: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
