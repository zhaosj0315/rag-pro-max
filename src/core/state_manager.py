"""
状态管理器
Stage 3.3 - 高风险重构
集中管理 Streamlit session_state
"""

import streamlit as st
from typing import Any, Optional, List, Dict


class StateManager:
    """集中管理应用状态"""
    
    # 聊天相关
    @staticmethod
    def get_messages() -> List[Dict]:
        """获取聊天消息列表"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        return st.session_state.messages
    
    @staticmethod
    def add_message(role: str, content: str, **kwargs):
        """添加消息"""
        messages = StateManager.get_messages()
        msg = {'role': role, 'content': content, **kwargs}
        messages.append(msg)
    
    @staticmethod
    def clear_messages():
        """清空消息"""
        st.session_state.messages = []
    
    # 聊天引擎
    @staticmethod
    def get_chat_engine() -> Optional[Any]:
        """获取聊天引擎"""
        return st.session_state.get('chat_engine')
    
    @staticmethod
    def set_chat_engine(engine: Any):
        """设置聊天引擎"""
        st.session_state.chat_engine = engine
    
    # 模型列表
    @staticmethod
    def get_model_list() -> List[str]:
        """获取模型列表"""
        if 'model_list' not in st.session_state:
            st.session_state.model_list = []
        return st.session_state.model_list
    
    @staticmethod
    def set_model_list(models: List[str]):
        """设置模型列表"""
        st.session_state.model_list = models
    
    @staticmethod
    def get_ollama_models() -> List[str]:
        """获取 Ollama 模型列表"""
        if 'ollama_models' not in st.session_state:
            st.session_state.ollama_models = []
        return st.session_state.ollama_models
    
    @staticmethod
    def set_ollama_models(models: List[str]):
        """设置 Ollama 模型列表"""
        st.session_state.ollama_models = models
    
    # 知识库维度
    @staticmethod
    def get_kb_dimensions() -> Dict:
        """获取知识库维度信息"""
        if 'kb_dimensions' not in st.session_state:
            st.session_state.kb_dimensions = {}
        return st.session_state.kb_dimensions
    
    @staticmethod
    def set_kb_dimension(kb_name: str, dimension: int):
        """设置知识库维度"""
        dims = StateManager.get_kb_dimensions()
        dims[kb_name] = dimension
    
    # 建议历史
    @staticmethod
    def get_suggestions_history() -> List:
        """获取建议历史"""
        if 'suggestions_history' not in st.session_state:
            st.session_state.suggestions_history = []
        return st.session_state.suggestions_history
    
    @staticmethod
    def add_suggestion(suggestion: str):
        """添加建议"""
        history = StateManager.get_suggestions_history()
        if suggestion not in history:
            history.append(suggestion)
    
    # 通用 get/set
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """获取状态值"""
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any):
        """设置状态值"""
        st.session_state[key] = value
    
    @staticmethod
    def has(key: str) -> bool:
        """检查状态是否存在"""
        return key in st.session_state
    
    @staticmethod
    def delete(key: str):
        """删除状态"""
        if key in st.session_state:
            del st.session_state[key]
    
    @staticmethod
    def clear_all():
        """清空所有状态（谨慎使用）"""
        st.session_state.clear()


# 便捷访问
state = StateManager()
