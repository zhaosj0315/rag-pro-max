#!/usr/bin/env python3
"""
RAG Pro Max v1.8 - 真正的精简版 (40行)
集成紧凑侧边栏和所有优化功能
"""

# 环境初始化
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from src.core.environment import initialize_environment
from src.ui.compact_sidebar import render_compact_sidebar
from src.core.main_controller import MainController
from src.ui.page_style import PageStyle

# 初始化环境
initialize_environment()

# 页面配置
PageStyle.setup_page()
st.title("🚀 RAG Pro Max v1.8")

# 渲染紧凑侧边栏
render_compact_sidebar()

# 主控制器处理所有业务逻辑
controller = MainController()

# 主界面内容
if st.session_state.get('active_kb_name'):
    # 有知识库时显示问答界面
    controller.render_chat_interface()
else:
    # 无知识库时显示欢迎页面
    controller.render_welcome_page()

# 处理文件上传
if st.session_state.get('process_files'):
    controller.process_uploaded_files()

# 处理用户查询
if st.session_state.get('user_query'):
    controller.handle_user_query()

# 底部状态栏
controller.render_status_bar()
