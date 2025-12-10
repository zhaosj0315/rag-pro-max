#!/usr/bin/env python3
"""RAG Pro Max - 终极精简版 (仅 25 行)"""

from src.core.environment import initialize_environment
initialize_environment()

import streamlit as st
import os
from src.core.app_config import load_config
from src.ui.page_style import PageStyle
from src.ui.complete_sidebar import CompleteSidebar
from src.core.main_controller import MainController
from src.ui.status_bar import StatusBar

# 初始化
PageStyle.setup_page()
st.title("🛡️ RAG Pro Max")
initialize_session_state()

# 组件
controller = MainController("vector_db_storage")
sidebar = CompleteSidebar(load_config(), "vector_db_storage")

# 引导
show_first_time_guide([d for d in os.listdir("vector_db_storage") if os.path.isdir(os.path.join("vector_db_storage", d))] if os.path.exists("vector_db_storage") else [])

# 主逻辑
config_data = sidebar.render()
if 'config' in config_data:
    config = CompleteSidebar.extract_config_values(config_data['config'])
    kb_name = config_data.get('kb', {}).get('current_nav', '创建新知识库')
    active_kb = kb_name[2:] if kb_name.startswith('📂 ') else None
    
    if handle_kb_switching(active_kb, st.session_state.current_kb_id) and controller.handle_kb_loading(active_kb, config['embed_provider'], config['embed_model'], config['embed_key'], config['embed_url']):
        controller.handle_auto_summary(active_kb)
        controller.handle_message_rendering(active_kb)
    # 处理用户输入
    user_input = st.chat_input("输入问题...")
    if user_input and controller.handle_user_input(user_input):
        st.rerun()
    
    # 处理当前问题（直接处理，不使用复杂队列）
    if hasattr(st.session_state, 'current_question') and st.session_state.current_question:
        current_q = st.session_state.current_question
        st.session_state.current_question = None  # 清除问题
        
        # 直接处理
        if hasattr(st.session_state, 'chat_engine') and st.session_state.chat_engine:
            with st.chat_message("user"):
                st.write(current_q)
            
            with st.chat_message("assistant"):
                try:
                    response = st.session_state.chat_engine.stream_chat(current_q)
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    for token in response.response_gen:
                        full_response += token
                        response_placeholder.markdown(full_response + "▌")
                    
                    response_placeholder.markdown(full_response)
                    
                except Exception as e:
                    st.error(f"查询失败: {e}")
    
    # 队列处理（手动模式）
    controller.handle_queue_processing(active_kb, config['embed_provider'], config['embed_model'], config['embed_key'], config['embed_url'], config['llm_model'])
    elif config_data.get('kb', {}).get('current_nav') == "创建新知识库":
        PageStyle.render_welcome_message()
