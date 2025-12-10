"""
核心业务逻辑模块
负责知识库创建和文档处理的核心逻辑
"""

import os
import time
import streamlit as st
from src.logging import LogManager
from src.config import ConfigLoader
from src.utils.document_processor import sanitize_filename
from src.chat import HistoryManager

logger = LogManager()

def process_knowledge_base_logic():
    """处理知识库创建的核心逻辑"""
    # 这里包含原来的知识库处理逻辑
    # 由于代码量很大，这里只是一个框架
    logger.info("开始处理知识库创建")
    
    # 实际的处理逻辑会在后续步骤中从主文件移动过来
    pass

def handle_button_actions(btn_start, final_kb_name, target_path, output_base, action_mode):
    """处理按钮操作"""
    if btn_start:
        config_to_save = {
            "target_path": target_path,
            "output_path": output_base,
            # ... 其他配置项
        }
        ConfigLoader.save(config_to_save)

        if not final_kb_name:
            st.error("请输入知识库名称")
            return False
        
        try:
            clean_kb_name = sanitize_filename(final_kb_name)
            if not clean_kb_name:
                raise ValueError("知识库名称包含非法字符或为空")
            
            process_knowledge_base_logic()
            st.session_state.current_nav = f"📂 {final_kb_name}"
            st.session_state.current_kb_id = None
            
            if action_mode == "NEW" or action_mode == "APPEND":
                st.session_state.messages = []
                st.session_state.suggestions_history = []
                hist_path = os.path.join("chat_histories", f"{final_kb_name}.json")
                if os.path.exists(hist_path):
                    os.remove(hist_path)
            
            time.sleep(1)
            st.rerun()
            return True
            
        except Exception as e:
            st.error(f"执行失败: {e}")
            return False
    
    return False
