#!/usr/bin/env python3
"""
RAG Pro Max - 最终精简版 (50行)
完全模块化，所有功能通过模块调用
"""

# 环境初始化
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 核心初始化
from src.core.environment import initialize_environment
initialize_environment()

# 导入主要组件
import streamlit as st
from src.ui.page_style import PageStyle
from src.ui.compact_sidebar import render_compact_sidebar
from src.core.main_controller import MainController
from src.ui.main_interface import MainInterface

# 初始化
PageStyle.setup_page()
controller = MainController()
interface = MainInterface()

# 页面标题
st.title("🛡️ RAG Pro Max")

# 渲染侧边栏
render_compact_sidebar()

# 主界面
if st.session_state.get('active_kb_name'):
    interface.render_chat_interface()
else:
    interface.render_welcome_interface()

# 处理业务逻辑
controller.handle_file_processing()
controller.handle_user_queries()

# 底部状态
controller.render_status_bar()

# 清理资源
controller.cleanup_resources()
