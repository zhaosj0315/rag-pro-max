#!/usr/bin/env python3
"""
资源保护集成测试
验证 apppro.py 中的资源保护功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """测试导入"""
    print("测试1: 导入资源保护模块...")
    try:
        from src.utils.adaptive_throttling import get_resource_guard
        import psutil
        print("  ✅ 导入成功")
        return True
    except Exception as e:
        print(f"  ❌ 导入失败: {e}")
        return False

def test_resource_guard():
    """测试资源保护"""
    print("\n测试2: 资源保护功能...")
    try:
        from src.utils.adaptive_throttling import get_resource_guard
        import psutil
        
        resource_guard = get_resource_guard()
        cpu = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory().percent
        
        result = resource_guard.check_resources(cpu, mem, 0)
        throttle_info = result.get('throttle', {})
        
        print(f"  CPU: {cpu}%")
        print(f"  内存: {mem}%")
        print(f"  限流级别: {throttle_info.get('level', 0)}")
        print(f"  动作: {throttle_info.get('action', 'allow')}")
        print("  ✅ 资源检查成功")
        return True
    except Exception as e:
        print(f"  ❌ 资源检查失败: {e}")
        return False

def test_memory_cleanup():
    """测试内存清理"""
    print("\n测试3: 内存清理功能...")
    try:
        from src.utils.adaptive_throttling import get_resource_guard
        
        resource_guard = get_resource_guard()
        resource_guard.throttler.cleanup_memory()
        
        print("  ✅ 内存清理成功")
        return True
    except Exception as e:
        print(f"  ❌ 内存清理失败: {e}")
        return False

def test_apppro_integration():
    """测试 apppro.py 集成"""
    print("\n测试4: apppro.py 集成检查...")
    try:
        with open('src/apppro.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('from src.utils.adaptive_throttling import get_resource_guard', '导入资源保护'),
            ('import psutil as psutil_main', '导入psutil'),
            ('resource_guard = get_resource_guard()', '初始化资源保护'),
            ('resource_guard.check_resources', '资源检查调用'),
            ('resource_guard.throttler.cleanup_memory()', '内存清理调用')
        ]
        
        all_passed = True
        for check_str, desc in checks:
            if check_str in content:
                print(f"  ✅ {desc}")
            else:
                print(f"  ❌ {desc} - 未找到")
                all_passed = False
        
        return all_passed
    except Exception as e:
        print(f"  ❌ 集成检查失败: {e}")
        return False

def main():
    print("=" * 60)
    print("  资源保护集成测试")
    print("=" * 60)
    
    results = []
    results.append(("导入测试", test_imports()))
    results.append(("资源保护", test_resource_guard()))
    results.append(("内存清理", test_memory_cleanup()))
    results.append(("集成检查", test_apppro_integration()))
    
    print("\n" + "=" * 60)
    print("  测试结果")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！资源保护已成功集成。")
        return 0
    else:
        print(f"\n❌ {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())
