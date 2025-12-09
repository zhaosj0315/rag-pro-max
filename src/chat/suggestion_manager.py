"""
追问建议管理器
Stage 7.2 - 追问推荐逻辑
"""

from typing import List, Optional, Any
import streamlit as st

from src.chat_utils_improved import generate_follow_up_questions_safe as generate_follow_up_questions


class SuggestionManager:
    """追问建议管理器"""
    
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
        num_questions: int = 3
    ) -> List[str]:
        """
        生成初始追问建议
        
        Args:
            context_text: 上下文文本（回答内容）
            messages: 历史消息列表
            question_queue: 问题队列
            query_engine: 查询引擎（可选）
            num_questions: 生成问题数量
        
        Returns:
            追问建议列表
        """
        # 排除已有的问题
        existing_questions = [m['content'] for m in messages if m['role'] == 'user']
        existing_questions.extend(question_queue)
        existing_questions.extend(SuggestionManager.get_suggestions_history())
        
        # 生成新问题
        new_sugs = generate_follow_up_questions(
            context_text,
            num_questions=num_questions,
            existing_questions=existing_questions,
            query_engine=query_engine
        )
        
        # 去重检查
        if new_sugs:
            # 再次检查是否与现有问题重复
            unique_sugs = [s for s in new_sugs if s not in existing_questions]
            return unique_sugs
        
        return []
    
    @staticmethod
    def generate_more_suggestions(
        context_text: str,
        messages: List[dict],
        question_queue: List[str],
        query_engine: Optional[Any] = None,
        num_questions: int = 3
    ) -> List[str]:
        """
        生成更多追问建议（用于"继续推荐"按钮）
        
        Args:
            context_text: 上下文文本
            messages: 历史消息列表
            question_queue: 问题队列
            query_engine: 查询引擎（可选）
            num_questions: 生成问题数量
        
        Returns:
            新的追问建议列表
        """
        # 排除所有已有问题（包括历史、队列、已生成的追问）
        all_history_questions = [m['content'] for m in messages if m['role'] == 'user']
        all_history_questions.extend(SuggestionManager.get_suggestions_history())
        all_history_questions.extend(question_queue)
        
        # 生成新问题
        new_sugs = generate_follow_up_questions(
            context_text=context_text,
            num_questions=num_questions,
            existing_questions=all_history_questions,
            query_engine=query_engine
        )
        
        return new_sugs if new_sugs else []
