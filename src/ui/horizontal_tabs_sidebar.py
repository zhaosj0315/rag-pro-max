#!/usr/bin/env python3
"""
横向标签页侧边栏组件 - 只修改样式，保持原有功能
"""

import streamlit as st

def create_horizontal_tabs_sidebar():
    """创建横向标签页侧边栏"""
    
    with st.sidebar:
        # 横向标签页选择
        tabs = st.tabs(["🏠", "⚙️", "📊", "🔧", "ℹ️"])
        
        with tabs[0]:  # 🏠 主页
            render_main_content()
        
        with tabs[1]:  # ⚙️ 配置  
            render_config_content()
        
        with tabs[2]:  # 📊 监控
            render_monitor_content()
        
        with tabs[3]:  # 🔧 工具
            render_tools_content()
        
        with tabs[4]:  # ℹ️ 帮助
            render_help_content()

def render_main_content():
    """主页内容 - 核心功能"""
    # 这里放置原有的主要侧边栏内容
    # 知识库管理、文档上传等
    pass

def render_config_content():
    """配置内容"""
    # 这里放置原有的配置相关内容
    pass

def render_monitor_content():
    """监控内容"""
    # 这里放置原有的监控相关内容
    pass

def render_tools_content():
    """工具内容"""
    # 这里放置原有的工具相关内容
    pass

def render_help_content():
    """帮助内容"""
    # 这里放置原有的帮助相关内容
    pass
