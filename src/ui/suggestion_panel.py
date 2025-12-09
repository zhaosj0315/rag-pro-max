"""
推荐问题管理面板
v1.5.1 新增功能
"""

import streamlit as st
from typing import Optional
from src.chat.suggestion_engine import SuggestionEngine


class SuggestionPanel:
    """推荐问题管理面板"""
    
    def __init__(self, engine: Optional[SuggestionEngine] = None):
        self.engine = engine
    
    def render_panel(self):
        """渲染推荐问题管理面板"""
        if not self.engine:
            st.info("💡 请先选择知识库")
            return
        
        with st.expander("💡 推荐问题管理", expanded=False):
            tabs = st.tabs(["📝 自定义推荐", "📊 统计信息", "📜 历史记录"])
            
            # Tab 1: 自定义推荐
            with tabs[0]:
                self._render_custom_tab()
            
            # Tab 2: 统计信息
            with tabs[1]:
                self._render_stats_tab()
            
            # Tab 3: 历史记录
            with tabs[2]:
                self._render_history_tab()
    
    def _render_custom_tab(self):
        """渲染自定义推荐标签"""
        st.markdown("**添加自定义推荐问题**")
        st.caption("这些问题会优先显示在推荐列表中")
        
        # 添加新问题
        new_question = st.text_input(
            "输入问题",
            key="new_custom_suggestion",
            placeholder="例如：这个知识库主要讲什么？"
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("➕ 添加", use_container_width=True, key="add_custom"):
                if new_question:
                    if self.engine.add_custom_suggestion(new_question):
                        st.success("✅ 已添加")
                        st.rerun()
                    else:
                        st.warning("⚠️ 问题已存在")
        
        # 显示现有自定义推荐
        st.markdown("---")
        st.markdown("**当前自定义推荐**")
        
        custom_list = self.engine.get_custom_suggestions()
        if not custom_list:
            st.caption("暂无自定义推荐")
        else:
            for i, q in enumerate(custom_list, 1):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.caption(f"{i}. {q}")
                with col2:
                    if st.button("🗑️", key=f"del_custom_{i}", help="删除"):
                        self.engine.remove_custom_suggestion(q)
                        st.rerun()
    
    def _render_stats_tab(self):
        """渲染统计信息标签"""
        stats = self.engine.get_stats()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("自定义推荐", stats['custom_count'])
        
        with col2:
            st.metric("历史记录", stats['history_count'])
        
        with col3:
            st.metric("队列中", stats['queue_count'])
        
        st.markdown("---")
        
        # 清空操作
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ 清空历史", use_container_width=True, key="clear_history"):
                self.engine.clear_history()
                st.success("✅ 已清空历史")
                st.rerun()
        
        with col2:
            if st.button("🗑️ 清空队列", use_container_width=True, key="clear_queue"):
                self.engine.clear_queue()
                st.success("✅ 已清空队列")
                st.rerun()
    
    def _render_history_tab(self):
        """渲染历史记录标签"""
        st.markdown("**最近生成的推荐问题**")
        
        history = self.engine.get_history(limit=20)
        
        if not history:
            st.caption("暂无历史记录")
        else:
            for i, q in enumerate(reversed(history), 1):
                st.caption(f"{i}. {q}")


def get_suggestion_panel(engine: Optional[SuggestionEngine] = None) -> SuggestionPanel:
    """获取推荐问题管理面板"""
    if 'suggestion_panel' not in st.session_state:
        st.session_state.suggestion_panel = SuggestionPanel(engine)
    else:
        # 更新 engine
        st.session_state.suggestion_panel.engine = engine
    return st.session_state.suggestion_panel
