"""
状态管理器 - 多进程安全版本
"""

import os
import sys
from typing import Dict, Any, Optional, List

class StateManager:
    """多进程安全的状态管理器"""
    
    def __init__(self):
        self._state = {}
        self._streamlit_available = False
        
        # 检查是否在Streamlit环境中
        try:
            if 'streamlit' in sys.modules:
                import streamlit as st
                self._st = st
                self._streamlit_available = True
            else:
                self._st = None
        except ImportError:
            self._st = None
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取状态值"""
        if self._streamlit_available and self._st and hasattr(self._st, 'session_state'):
            return getattr(self._st.session_state, key, default)
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置状态值"""
        if self._streamlit_available and self._st and hasattr(self._st, 'session_state'):
            setattr(self._st.session_state, key, value)
        else:
            self._state[key] = value
    
    def has(self, key: str) -> bool:
        """检查是否存在键"""
        if self._streamlit_available and self._st and hasattr(self._st, 'session_state'):
            return hasattr(self._st.session_state, key)
        return key in self._state
    
    def clear(self) -> None:
        """清空状态"""
        if self._streamlit_available and self._st and hasattr(self._st, 'session_state'):
            for key in list(self._st.session_state.keys()):
                del self._st.session_state[key]
        else:
            self._state.clear()
    
    def get_messages(self) -> List[Dict[str, str]]:
        """获取消息列表"""
        if self._streamlit_available and self._st and hasattr(self._st, 'session_state'):
            return getattr(self._st.session_state, 'messages', [])
        return self._state.get('messages', [])
    
    def add_message(self, role: str, content: str) -> None:
        """添加消息"""
        messages = self.get_messages()
        messages.append({"role": role, "content": content})
        self.set('messages', messages)
    
    def clear_messages(self) -> None:
        """清空消息"""
        self.set('messages', [])

# 全局状态管理器实例
state = StateManager()
