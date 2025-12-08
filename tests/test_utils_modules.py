"""
工具模块测试
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import tempfile


def test_resource_monitor():
    """测试资源监控模块"""
    from utils.resource_monitor import (
        check_resource_usage,
        get_system_stats,
        should_throttle,
        format_bytes
    )
    
    # 测试资源检查
    cpu, mem, gpu, throttle = check_resource_usage(threshold=80.0)
    assert isinstance(cpu, (int, float))
    assert isinstance(mem, (int, float))
    assert isinstance(gpu, (int, float))
    assert isinstance(throttle, bool)
    print(f"✅ 资源监控: CPU {cpu:.1f}% | 内存 {mem:.1f}% | GPU {gpu:.1f}%")
    
    # 测试系统统计
    stats = get_system_stats()
    assert 'cpu_percent' in stats
    assert 'memory_percent' in stats
    print(f"✅ 系统统计: {len(stats)} 个指标")
    
    # 测试限流判断
    result = should_throttle(90, 85, 95, threshold=80)
    assert result == True
    result = should_throttle(50, 60, 70, threshold=80)
    assert result == False
    print("✅ 限流判断测试通过")
    
    # 测试字节格式化
    assert "1.00 KB" in format_bytes(1024)
    assert "1.00 MB" in format_bytes(1024*1024)
    print("✅ 字节格式化测试通过")


def test_model_utils():
    """测试模型工具模块"""
    from utils.model_utils import (
        check_hf_model_exists,
        auto_switch_model,
        get_model_dimension
    )
    
    # 测试 HF 模型检查
    exists = check_hf_model_exists("BAAI/bge-small-zh-v1.5")
    assert isinstance(exists, bool)
    print(f"✅ HF 模型检查: {'存在' if exists else '不存在'}")
    
    # 测试自动切换模型
    model = auto_switch_model(512, "current_model")
    assert model == "BAAI/bge-small-zh-v1.5"
    model = auto_switch_model(1024, "current_model")
    assert model == "BAAI/bge-large-zh-v1.5"
    print("✅ 自动切换模型测试通过")
    
    # 测试获取模型维度
    dim = get_model_dimension("BAAI/bge-small-zh-v1.5")
    assert dim == 512
    dim = get_model_dimension("BAAI/bge-large-zh-v1.5")
    assert dim == 1024
    print("✅ 模型维度获取测试通过")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  工具模块测试")
    print("="*60 + "\n")
    
    print("--- 资源监控模块 ---")
    test_resource_monitor()
    
    print("\n--- 模型工具模块 ---")
    test_model_utils()
    
    print("\n" + "="*60)
    print("  ✅ 所有工具模块测试通过")
    print("="*60 + "\n")
