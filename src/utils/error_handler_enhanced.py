"""
增强的错误处理机制
"""

import traceback
import logging  # 允许使用 - 错误处理专用
import streamlit as st
from typing import Any, Callable
from functools import wraps

class ErrorHandler:
    """全局错误处理器"""
    
    @staticmethod
    def safe_execute(func: Callable, *args, **kwargs) -> tuple[bool, Any]:
        """安全执行函数"""
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            logging.error(f"函数 {func.__name__} 执行失败: {e}")
            return False, str(e)
    
    @staticmethod
    def with_error_handling(error_message: str = "操作失败"):
        """装饰器：为函数添加错误处理"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    st.error(f"{error_message}: {str(e)}")
                    logging.error(f"{func.__name__}: {traceback.format_exc()}")
                    return None
            return wrapper
        return decorator
    
    @staticmethod
    def display_error(error: Exception, context: str = ""):
        """统一错误显示"""
        error_msg = f"{context}: {str(error)}" if context else str(error)
        st.error(f"❌ {error_msg}")
        
        with st.expander("🔍 错误详情"):
            st.code(traceback.format_exc())

# 全局错误处理器实例
error_handler = ErrorHandler()
