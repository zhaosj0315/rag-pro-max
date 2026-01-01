"""
状态栏组件
显示当前处理状态，支持取消操作
"""

import streamlit as st
from typing import Optional

class StatusBar:
    """状态栏管理器"""
    
    @staticmethod
    def show_processing_status(question: str, allow_cancel: bool = True):
        """显示处理中状态"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.info(f"🔄 正在回复: {question[:50]}...")
        
        with col2:
            if allow_cancel and st.button("❌ 取消", key="cancel_current"):
                StatusBar.cancel_current_processing()
                return True
        
        return False
    
    @staticmethod
    def show_waiting_status(queue_size: int):
        """显示等待状态"""
        if queue_size > 0:
            st.warning(f"⏳ 队列中有 {queue_size} 个问题等待处理")
    
    @staticmethod
    def show_idle_status():
        """显示空闲状态"""
        st.success("✅ 就绪 - 可以提问")
    
    @staticmethod
    def cancel_current_processing():
        """取消当前处理"""
        # 清除当前问题
        if 'current_question' in st.session_state:
            del st.session_state.current_question
        
        # 重置处理状态
        st.session_state.is_processing = False
        st.session_state.cancel_requested = True
        
        st.success("✅ 已取消当前问题")
        st.rerun()
    
    @staticmethod
    def is_cancelled():
        """检查是否被取消"""
        return st.session_state.get('cancel_requested', False)
    
    @staticmethod
    def clear_cancel_flag():
        """清除取消标志"""
        st.session_state.cancel_requested = False
