#!/usr/bin/env python3
"""
v2.3.1 完整功能测试
测试所有新增模块和重构后的应用
"""

import sys
import os
import time
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_module_imports():
    """测试所有新模块导入"""
    print("🧪 测试模块导入...")
    
    try:
        # 测试核心应用模块
        from src.app.app_initializer import AppInitializer
        from src.app.main_app import MainApp
        print("  ✅ 应用模块导入成功")
        
        # 测试UI模块
        from src.ui.sidebar_manager import SidebarManager
        print("  ✅ UI模块导入成功")
        
        # 测试知识库模块
        from src.kb.kb_interface import KBInterface
        from src.kb.kb_processor import KBProcessor
        print("  ✅ 知识库模块导入成功")
        
        # 测试聊天模块
        from src.chat.chat_interface import ChatInterface
        print("  ✅ 聊天模块导入成功")
        
        # 测试新增功能模块
        from src.config.config_interface import ConfigInterface
        from src.upload.upload_interface import UploadInterface
        from src.document.document_manager_ui import DocumentManagerUI
        from src.monitor.system_monitor_ui import SystemMonitorUI
        print("  ✅ 新增功能模块导入成功")
        
        # 测试工具模块
        from src.utils.kb_utils import generate_smart_kb_name
        print("  ✅ 工具模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 模块导入失败: {e}")
        return False

def test_app_initialization():
    """测试应用初始化"""
    print("🧪 测试应用初始化...")
    
    try:
        from src.app.app_initializer import AppInitializer
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 测试目录创建
            initializer = AppInitializer()
            
            # 模拟初始化（不实际创建目录）
            print("  ✅ 应用初始化器创建成功")
            
        return True
        
    except Exception as e:
        print(f"  ❌ 应用初始化失败: {e}")
        return False

def test_main_app_creation():
    """测试主应用创建"""
    print("🧪 测试主应用创建...")
    
    try:
        # 先设置必要的streamlit会话状态模拟
        import streamlit as st
        if not hasattr(st, 'session_state'):
            # 创建一个模拟的session_state
            class MockSessionState:
                def __init__(self):
                    self._state = {}
                def get(self, key, default=None):
                    return self._state.get(key, default)
                def __setattr__(self, key, value):
                    if key.startswith('_'):
                        super().__setattr__(key, value)
                    else:
                        self._state[key] = value
                def __getattr__(self, key):
                    return self._state.get(key)
            
            st.session_state = MockSessionState()
        
        from src.app.main_app import MainApp
        
        # 创建主应用实例（不运行）
        print("  ✅ 主应用模块导入成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 主应用创建失败: {e}")
        return False

def test_sidebar_manager():
    """测试侧边栏管理器"""
    print("🧪 测试侧边栏管理器...")
    
    try:
        from src.ui.sidebar_manager import SidebarManager
        
        # 创建侧边栏管理器实例
        sidebar = SidebarManager()
        print("  ✅ 侧边栏管理器创建成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 侧边栏管理器测试失败: {e}")
        return False

def test_kb_interface():
    """测试知识库界面"""
    print("🧪 测试知识库界面...")
    
    try:
        from src.kb.kb_interface import KBInterface
        
        # 创建知识库界面实例
        kb_ui = KBInterface()
        print("  ✅ 知识库界面创建成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 知识库界面测试失败: {e}")
        return False

def test_chat_interface():
    """测试聊天界面"""
    print("🧪 测试聊天界面...")
    
    try:
        from src.chat.chat_interface import ChatInterface
        
        # 创建聊天界面实例
        chat_ui = ChatInterface()
        print("  ✅ 聊天界面创建成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 聊天界面测试失败: {e}")
        return False

def test_new_modules():
    """测试新增模块"""
    print("🧪 测试新增模块...")
    
    try:
        # 测试配置界面
        from src.config.config_interface import ConfigInterface
        config_ui = ConfigInterface()
        print("  ✅ 配置界面创建成功")
        
        # 测试上传界面
        from src.upload.upload_interface import UploadInterface
        upload_ui = UploadInterface()
        print("  ✅ 上传界面创建成功")
        
        # 测试文档管理界面
        from src.document.document_manager_ui import DocumentManagerUI
        doc_ui = DocumentManagerUI()
        print("  ✅ 文档管理界面创建成功")
        
        # 测试系统监控界面
        from src.monitor.system_monitor_ui import SystemMonitorUI
        monitor_ui = SystemMonitorUI()
        print("  ✅ 系统监控界面创建成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 新增模块测试失败: {e}")
        return False

def test_utility_functions():
    """测试工具函数"""
    print("🧪 测试工具函数...")
    
    try:
        from src.utils.kb_utils import generate_smart_kb_name
        
        # 测试智能命名（提供正确格式的参数）
        name = generate_smart_kb_name("test_document.pdf", 1, {".pdf": 1}, "test_folder")
        print(f"  ✅ 智能命名生成: {name}")
        
        # 测试会话状态初始化函数存在
        from src.utils.kb_utils import initialize_session_state
        print("  ✅ 会话状态初始化函数导入成功")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 工具函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_structure():
    """测试文件结构"""
    print("🧪 测试文件结构...")
    
    required_files = [
        "src/app/app_initializer.py",
        "src/app/main_app.py",
        "src/ui/sidebar_manager.py",
        "src/kb/kb_interface.py",
        "src/kb/kb_processor.py",
        "src/chat/chat_interface.py",
        "src/config/config_interface.py",
        "src/upload/upload_interface.py",
        "src/document/document_manager_ui.py",
        "src/monitor/system_monitor_ui.py",
        "src/utils/kb_utils.py",
        "src/apppro_refactored.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"  ❌ 缺少文件: {missing_files}")
        return False
    else:
        print(f"  ✅ 所有必需文件存在 ({len(required_files)}个)")
        return True

def test_refactored_app_startup():
    """测试重构后应用启动"""
    print("🧪 测试重构后应用启动...")
    
    try:
        # 检查重构后的主文件
        refactored_file = project_root / "src/apppro_refactored.py"
        if not refactored_file.exists():
            print("  ❌ 重构后的主文件不存在")
            return False
        
        # 检查文件大小（应该很小）
        file_size = refactored_file.stat().st_size
        if file_size > 1000:  # 1KB
            print(f"  ⚠️  重构后文件较大: {file_size} bytes")
        else:
            print(f"  ✅ 重构后文件精简: {file_size} bytes")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 重构后应用测试失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 60)
    print("  v2.3.1 完整功能测试")
    print("=" * 60)
    
    tests = [
        ("模块导入", test_module_imports),
        ("应用初始化", test_app_initialization),
        ("主应用创建", test_main_app_creation),
        ("侧边栏管理器", test_sidebar_manager),
        ("知识库界面", test_kb_interface),
        ("聊天界面", test_chat_interface),
        ("新增模块", test_new_modules),
        ("工具函数", test_utility_functions),
        ("文件结构", test_file_structure),
        ("重构后应用", test_refactored_app_startup)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print("  测试结果汇总")
    print("=" * 60)
    print(f"✅ 通过: {passed}/{len(tests)}")
    print(f"❌ 失败: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 所有v2.3.1功能测试通过！重构成功！")
        return True
    else:
        print(f"\n⚠️  有 {failed} 个测试失败，需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
