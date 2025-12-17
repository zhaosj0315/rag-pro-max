#!/usr/bin/env python3
"""
RAG Pro Max - 极简主文件
完全模块化架构，主文件仅负责应用启动
"""

# 环境初始化
from src.core.environment import initialize_environment
initialize_environment()

import streamlit as st
from src.core.app_config import load_config
from src.ui.page_style import PageStyle
from src.ui.complete_sidebar import CompleteSidebar
from src.core.main_controller import MainController
from src.utils.app_utils import initialize_session_state, show_first_time_guide, handle_kb_switching

# 页面设置
PageStyle.setup_page()
st.title("🛡️ RAG Pro Max")

# 状态初始化
initialize_session_state()

# 配置和控制器
defaults = load_config()
output_base = "vector_db_storage"
main_controller = MainController(output_base)

# 首次使用引导
existing_kbs = [d for d in __import__('os').listdir(output_base) 
                if __import__('os').path.isdir(__import__('os').path.join(output_base, d))] if __import__('os').path.exists(output_base) else []
show_first_time_guide(existing_kbs)

# 侧边栏渲染
sidebar = CompleteSidebar(defaults, output_base)
sidebar_config = sidebar.render()

# 获取配置
if 'config' in sidebar_config:
    config = CompleteSidebar.extract_config_values(sidebar_config['config'])
    
    # 获取当前知识库
    current_kb_name = sidebar_config.get('kb', {}).get('current_nav', '创建新知识库')
    if current_kb_name.startswith('📂 '):
        current_kb_name = current_kb_name[2:]
    
    active_kb_name = current_kb_name if current_kb_name != "创建新知识库" else None
    
    # 处理知识库切换和加载
    if handle_kb_switching(active_kb_name, st.session_state.current_kb_id):
        if main_controller.handle_kb_loading(active_kb_name, config['embed_provider'], 
                                           config['embed_model'], config['embed_key'], config['embed_url']):
            # 自动摘要
            main_controller.handle_auto_summary(active_kb_name)
            
            # 消息渲染
            main_controller.handle_message_rendering(active_kb_name)
            
            # 用户输入处理
            user_input = st.chat_input("输入问题...")
            main_controller.handle_user_input(user_input)
            
            # 队列处理
            main_controller.handle_queue_processing(active_kb_name, config['embed_provider'], 
                                                  config['embed_model'], config['embed_key'], 
                                                  config['embed_url'], config['llm_model'])

# 创建新知识库的情况
if sidebar_config.get('kb', {}).get('current_nav') == "创建新知识库":
    PageStyle.render_welcome_message()
