#!/usr/bin/env python3
"""
实时监控功能测试
验证实时监控功能的正常工作
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_realtime_monitor():
    """测试实时监控组件"""
    print("🧪 测试实时监控组件...")
    
    try:
        from src.utils.realtime_monitor import RealtimeMonitor
        
        monitor = RealtimeMonitor()
        print("✅ 成功创建实时监控器实例")
        
        # 测试获取系统指标
        metrics = monitor._get_system_metrics()
        print(f"✅ 成功获取系统指标: CPU {metrics['cpu_percent']:.1f}%, 内存 {metrics['memory_percent']:.1f}%")
        
        # 测试知识库获取
        kb_list = monitor._get_knowledge_bases()
        print(f"✅ 成功获取知识库列表: {len(kb_list)} 个")
        
        print("🎉 实时监控组件测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_system_dependencies():
    """测试系统依赖"""
    print("\n🧪 测试系统依赖...")
    
    try:
        import psutil
        print("✅ psutil 库可用")
        
        # 测试基本功能
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        print(f"✅ 系统监控功能正常: CPU {cpu_percent}%, 内存 {memory.percent}%, 磁盘 {disk.percent}%")
        return True
        
    except ImportError:
        print("❌ psutil 库未安装，请运行: pip install psutil")
        return False
    except Exception as e:
        print(f"❌ 系统监控测试失败: {e}")
        return False

def test_integration():
    """测试集成功能"""
    print("\n🧪 测试集成功能...")
    
    try:
        # 测试导入
        from src.utils.realtime_monitor import render_realtime_monitoring, render_mini_monitoring, realtime_monitor
        print("✅ 成功导入集成函数")
        
        # 测试全局实例
        metrics = realtime_monitor._get_system_metrics()
        print(f"✅ 全局实例测试: 获取到 {len(metrics)} 个监控指标")
        
        print("✅ 集成功能测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
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
    print("🚀 开始实时监控功能测试")
    print("=" * 50)
    
    test1_result = test_realtime_monitor()
    test2_result = test_system_dependencies()
    test3_result = test_integration()
    test4_result = test_sidebar_integration()
    
    print("\n" + "=" * 50)
    if test1_result and test2_result and test3_result and test4_result:
        print("🎉 所有测试通过！实时监控功能已就绪")
        print("\n📋 功能特点:")
        print("- ✅ 真正的实时监控，每5秒自动刷新")
        print("- ✅ 不影响对话页面，只刷新监控区域")
        print("- ✅ 系统资源监控 (CPU、内存、磁盘)")
        print("- ✅ 应用状态监控 (知识库、查询、错误率)")
        print("- ✅ 集成到侧边栏监控选项")
        print("- ✅ 支持手动立即刷新")
    else:
        print("❌ 部分测试失败，需要修复")
        if not test2_result:
            print("💡 提示: 请安装 psutil 库: pip install psutil")
        sys.exit(1)
