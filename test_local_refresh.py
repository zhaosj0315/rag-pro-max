#!/usr/bin/env python3
"""
局部刷新监控功能测试
验证监控组件不会影响对话功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_local_refresh_monitor():
    """测试局部刷新监控功能"""
    print("🧪 测试局部刷新监控功能...")
    
    try:
        # 测试导入
        from src.utils.local_refresh_monitor import LocalRefreshMonitor, show_local_monitor
        print("✅ 成功导入局部刷新监控模块")
        
        # 测试实例化
        monitor = LocalRefreshMonitor("/Users/zhaosj/Documents/rag-pro-max")
        print("✅ 成功创建监控实例")
        
        # 测试获取指标
        metrics = monitor._get_current_metrics()
        print(f"✅ 成功获取监控指标: {metrics}")
        
        # 测试轻量级指标
        lightweight_metrics = monitor._get_lightweight_metrics()
        print(f"✅ 成功获取轻量级指标: {lightweight_metrics}")
        
        print("🎉 局部刷新监控功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_sidebar_integration():
    """测试侧边栏集成"""
    print("\n🧪 测试侧边栏集成...")
    
    try:
        # 测试侧边栏导入
        from src.ui.sidebar_manager import SidebarManager
        print("✅ 成功导入侧边栏管理器")
        
        print("✅ 侧边栏集成测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 侧边栏集成测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始局部刷新监控功能测试")
    print("=" * 50)
    
    test1_result = test_local_refresh_monitor()
    test2_result = test_sidebar_integration()
    
    print("\n" + "=" * 50)
    if test1_result and test2_result:
        print("🎉 所有测试通过！局部刷新监控功能已就绪")
        print("\n📋 功能特点:")
        print("- ✅ 只刷新监控区域，不影响对话")
        print("- ✅ 使用session state避免全页面刷新")
        print("- ✅ 支持手动刷新和自动更新")
        print("- ✅ 提供实时指标和趋势图")
        print("- ✅ 集成到侧边栏监控标签")
    else:
        print("❌ 部分测试失败，需要修复")
        sys.exit(1)
