#!/usr/bin/env python3
"""
RAG Pro Max - 超级精简主文件
终极模块化架构，主文件仅 30 行
"""

from src.core.environment import initialize_environment
initialize_environment()

import streamlit as st
from src.core.app_config import load_config
from src.ui.page_style import PageStyle
from src.ui.complete_sidebar import CompleteSidebar
from src.core.main_controller import MainController
from src.utils.app_utils import initialize_session_state, show_first_time_guide, handle_kb_switching

# 应用初始化
PageStyle.setup_page()
st.title("🛡️ RAG Pro Max")
initialize_session_state()

# 核心组件
defaults = load_config()
output_base = "vector_db_storage"
controller = MainController(output_base)
sidebar = CompleteSidebar(defaults, output_base)

# 首次引导
import os
existing_kbs = [d for d in os.listdir(output_base) if os.path.isdir(os.path.join(output_base, d))] if os.path.exists(output_base) else []
show_first_time_guide(existing_kbs)

# 主流程
config_data = sidebar.render()
if 'config' in config_data:
    config = CompleteSidebar.extract_config_values(config_data['config'])
    kb_name = config_data.get('kb', {}).get('current_nav', '创建新知识库')
    active_kb = kb_name[2:] if kb_name.startswith('📂 ') else None
    
    if handle_kb_switching(active_kb, st.session_state.current_kb_id):
        if controller.handle_kb_loading(active_kb, config['embed_provider'], config['embed_model'], config['embed_key'], config['embed_url']):
            controller.handle_auto_summary(active_kb)
            controller.handle_message_rendering(active_kb)
            controller.handle_user_input(st.chat_input("输入问题..."))
            controller.handle_queue_processing(active_kb, config['embed_provider'], config['embed_model'], config['embed_key'], config['embed_url'], config['llm_model'])

if config_data.get('kb', {}).get('current_nav') == "创建新知识库":
    PageStyle.render_welcome_message()
