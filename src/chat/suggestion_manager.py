"""
追问建议管理器 - 统一推荐引擎适配器
Stage 7.2 - 追问推荐逻辑 (已迁移到统一推荐引擎)
"""

from typing import List, Optional, Any
import streamlit as st
from src.chat.unified_suggestion_engine import get_unified_suggestion_engine


class SuggestionManager:
    """追问建议管理器 - 统一推荐引擎的适配器"""
    
    @staticmethod
    def get_suggestions_history() -> List[str]:
        """获取追问历史"""
        if 'suggestions_history' not in st.session_state:
            st.session_state.suggestions_history = []
        return st.session_state.suggestions_history
    
    @staticmethod
    def add_suggestions(suggestions: List[str]):
        """添加追问建议（去重）"""
        history = SuggestionManager.get_suggestions_history()
        for sug in suggestions:
            if sug not in history:
                history.append(sug)
    
    @staticmethod
    def clear_suggestions():
        """清空追问历史"""
        st.session_state.suggestions_history = []
    
    @staticmethod
    def generate_initial_suggestions(
        context_text: str,
        messages: List[dict],
        question_queue: List[str],
        query_engine: Optional[Any] = None,
        num_questions: int = 3,
        kb_name: str = None
    ) -> List[str]:
        """
        生成初始追问建议 - 使用统一推荐引擎
        
        Args:
            context_text: 上下文文本（回答内容）
            messages: 历史消息列表
            question_queue: 问题队列
            query_engine: 查询引擎（可选）
            num_questions: 生成问题数量
            kb_name: 知识库名称
        
        Returns:
            追问建议列表
        """
        # 使用统一推荐引擎
        engine = get_unified_suggestion_engine(kb_name)
        suggestions = engine.generate_suggestions(
            context=context_text,
            source_type='chat',
            query_engine=query_engine,
            num_questions=num_questions
        )
        
        return suggestions
    
    @staticmethod
    def generate_more_suggestions(
        context_text: str,
        messages: List[dict],
        question_queue: List[str],
        query_engine: Optional[Any] = None,
        num_questions: int = 3,
        kb_name: str = None
    ) -> List[str]:
        """
        生成更多追问建议 - 使用统一推荐引擎
        
        Args:
            context_text: 上下文文本
            messages: 历史消息列表
            question_queue: 问题队列
            query_engine: 查询引擎（可选）
            num_questions: 生成问题数量
            kb_name: 知识库名称
        
        Returns:
            新的追问建议列表
        """
        # 使用统一推荐引擎
        engine = get_unified_suggestion_engine(kb_name)
        suggestions = engine.generate_suggestions(
            context=context_text,
            source_type='chat',
            query_engine=query_engine,
            num_questions=num_questions
        )
        
        return suggestions
