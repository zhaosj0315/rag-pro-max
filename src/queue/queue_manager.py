"""
队列管理器模块
负责问题队列管理和批处理
"""

import streamlit as st
from src.app_logging import LogManager

logger = LogManager()


class QueueManager:
    """队列管理器"""
    
    def __init__(self):
        if not hasattr(st.session_state, 'question_queue'):
            st.session_state.question_queue = []
        if not hasattr(st.session_state, 'is_processing'):
            st.session_state.is_processing = False
    
    def add_question(self, question):
        """添加问题到队列"""
        if question not in st.session_state.question_queue:
            st.session_state.question_queue.append(question)
            logger.info(f"📝 问题已加入队列: {question[:50]}...")
        else:
            st.toast("⚠️ 该问题已在队列中")
    
    def get_next_question(self):
        """获取下一个问题"""
        if st.session_state.question_queue and not st.session_state.is_processing:
            return st.session_state.question_queue.pop(0)
        return None
    
    def has_questions(self):
        """检查是否有待处理问题"""
        return len(st.session_state.question_queue) > 0
    
    def get_queue_size(self):
        """获取队列大小"""
        return len(st.session_state.question_queue)
    
    def is_processing(self):
        """检查是否正在处理"""
        return st.session_state.get('is_processing', False)
    
    def set_processing(self, processing):
        """设置处理状态"""
        st.session_state.is_processing = processing
        if processing:
            logger.info("🔄 开始处理问题")
        else:
            logger.info("✅ 问题处理完成")
    
    def render_queue_status(self):
        """渲染队列状态"""
        queue_len = self.get_queue_size()
        
        if self.is_processing():
            if queue_len > 0:
                with st.expander(f"⏳ 正在处理问题，队列中还有 {queue_len} 个问题等待...", expanded=False):
                    for i, q in enumerate(st.session_state.question_queue, 1):
                        display_q = q[:50] + "..." if len(q) > 50 else q
                        st.caption(f"{i}. {display_q}")
            else:
                st.info("⏳ 正在处理问题...")
        elif queue_len > 0:
            with st.expander(f"📝 队列中有 {queue_len} 个问题待处理", expanded=True):
                for i, q in enumerate(st.session_state.question_queue, 1):
                    display_q = q[:50] + "..." if len(q) > 50 else q
                    st.caption(f"{i}. {display_q}")
    
    def should_auto_process(self):
        """检查是否应该自动处理下一个问题"""
        return not self.is_processing() and self.has_questions()
    
    def render_process_controls(self):
        """渲染处理控制按钮"""
        queue_len = self.get_queue_size()
        
        if queue_len > 0 and not self.is_processing():
            if st.button("▶️ 处理下一个问题", key="process_next", type="primary"):
                return True
        
        return False
    
    def clear_queue(self):
        """清空队列"""
        cleared_count = len(st.session_state.question_queue)
        st.session_state.question_queue = []
        logger.info(f"🗑️ 已清空队列，移除 {cleared_count} 个问题")
        return cleared_count
    
    def remove_question(self, index):
        """移除指定位置的问题"""
        if 0 <= index < len(st.session_state.question_queue):
            removed = st.session_state.question_queue.pop(index)
            logger.info(f"🗑️ 已移除问题: {removed[:50]}...")
            return removed
        return None
    
    def get_queue_preview(self, max_items=3):
        """获取队列预览"""
        queue = st.session_state.question_queue[:max_items]
        preview = []
        for i, q in enumerate(queue, 1):
            display_q = q[:30] + "..." if len(q) > 30 else q
            preview.append(f"{i}. {display_q}")
        return preview
    
    def handle_user_input(self, user_input, chat_engine):
        """处理用户输入"""
        if user_input:
            if not chat_engine:
                st.error("请先点击左侧【🚀 执行处理】启动系统")
                return False
            else:
                self.add_question(user_input)
                return True
        return False
    
    def handle_prompt_trigger(self, chat_engine):
        """处理追问按钮触发"""
        if st.session_state.get('prompt_trigger'):
            if chat_engine:
                self.add_question(st.session_state.prompt_trigger)
            st.session_state.prompt_trigger = None
            return True
        return False
    
    def check_duplicate_recent(self, question, messages, max_recent=6):
        """检查最近是否有重复问题"""
        recent_queries = [m['content'] for m in messages[-max_recent:] if m['role'] == 'user']
        return question in recent_queries
