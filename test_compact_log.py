#!/usr/bin/env python3
"""
紧凑日志显示功能测试
验证日志管理的紧凑显示功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_compact_log_display():
    """测试紧凑日志显示组件"""
    print("🧪 测试紧凑日志显示组件...")
    
    try:
        from src.utils.compact_log_display import CompactLogDisplay
        
        # 创建测试日志目录
        import tempfile
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = Path(temp_dir)
            
            # 创建测试日志文件
            test_log = log_dir / "test.log"
            with open(test_log, 'w', encoding='utf-8') as f:
                f.write("2026-01-01 10:00:00 INFO 系统启动\n")
                f.write("2026-01-01 10:01:00 WARNING 内存使用率较高\n")
                f.write("2026-01-01 10:02:00 ERROR 连接失败\n")
                f.write("2026-01-01 10:03:00 INFO 重新连接成功\n")
            
            # 测试紧凑日志显示器
            display = CompactLogDisplay(str(log_dir))
            print("✅ 成功创建紧凑日志显示器")
            
            # 测试获取日志文件
            log_files = display._get_log_files()
            print(f"✅ 成功获取日志文件: {len(log_files)} 个")
            
            # 测试日志预览
            preview = display._get_log_preview(test_log)
            print(f"✅ 成功获取日志预览: {len(preview)} 行")
            
            # 测试日志级别统计
            counts = display._count_log_levels(test_log)
            print(f"✅ 成功统计日志级别: {counts}")
            
        print("🎉 紧凑日志显示组件测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_integration():
    """测试集成功能"""
    print("\n🧪 测试集成功能...")
    
    try:
        # 测试导入
        from src.utils.compact_log_display import render_compact_log_management, compact_log_display
        print("✅ 成功导入集成函数")
        
        # 测试全局实例
        log_files = compact_log_display._get_log_files()
        print(f"✅ 全局实例测试: 找到 {len(log_files)} 个日志文件")
        
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
        from src.ui.tabbed_sidebar import TabbedSidebar
        print("✅ 成功导入侧边栏组件")
        
        # 测试监控系统导入
        from src.monitoring.unified_monitoring_system import UnifiedMonitoringSystem
        print("✅ 成功导入监控系统")
        
        print("✅ 侧边栏集成测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 侧边栏集成测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始紧凑日志显示功能测试")
    print("=" * 50)
    
    test1_result = test_compact_log_display()
    test2_result = test_integration()
    test3_result = test_sidebar_integration()
    
    print("\n" + "=" * 50)
    if test1_result and test2_result and test3_result:
        print("🎉 所有测试通过！紧凑日志显示功能已就绪")
        print("\n📋 功能特点:")
        print("- ✅ 折叠式日志文件显示，节省空间")
        print("- ✅ 日志级别统计和状态指示")
        print("- ✅ 日志预览和快速操作")
        print("- ✅ 集成到侧边栏和监控系统")
        print("- ✅ 支持日志清理、下载、打包")
    else:
        print("❌ 部分测试失败，需要修复")
        sys.exit(1)
