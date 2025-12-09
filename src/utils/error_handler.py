"""统一错误处理模块 - v1.5.1 增强版"""

import streamlit as st
import time
from typing import Optional, Callable, Any, Tuple
from functools import wraps


class ErrorHandler:
    """错误处理器"""
    
    @staticmethod
    def handle_error(error: Exception, context: str = "") -> str:
        """处理错误并返回友好消息"""
        error_type = type(error).__name__
        error_msg = str(error)
        
        # 常见错误的友好提示
        friendly_messages = {
            "FileNotFoundError": "文件未找到，请检查文件路径是否正确",
            "PermissionError": "权限不足，请检查文件访问权限",
            "ValueError": "数据格式错误，请检查输入内容",
            "KeyError": "配置项缺失，请检查配置文件",
            "ConnectionError": "网络连接失败，请检查网络设置",
            "TimeoutError": "操作超时，请稍后重试",
            "MemoryError": "内存不足，请关闭其他程序或减少数据量",
            "AttributeError": "对象属性错误，可能是版本不兼容",
            "ImportError": "模块导入失败，请检查依赖是否安装",
        }
        
        friendly_msg = friendly_messages.get(error_type, "发生未知错误")
        
        if context:
            return f"❌ {context}: {friendly_msg}\n\n详细信息: {error_msg}"
        else:
            return f"❌ {friendly_msg}\n\n详细信息: {error_msg}"
    
    @staticmethod
    def show_error(error: Exception, context: str = "", show_recovery: bool = True):
        """在 Streamlit 中显示错误"""
        if show_recovery:
            msg = ErrorHandler.with_recovery(error, context)
        else:
            msg = ErrorHandler.handle_error(error, context)
        st.error(msg)
    
    @staticmethod
    def with_recovery(error: Exception, context: str = "") -> str:
        """提供恢复建议"""
        error_type = type(error).__name__
        
        recovery_tips = {
            "FileNotFoundError": "💡 建议: 检查文件是否存在，或重新上传文件",
            "PermissionError": "💡 建议: 使用管理员权限运行，或修改文件权限",
            "ValueError": "💡 建议: 检查输入格式，确保数据类型正确",
            "KeyError": "💡 建议: 检查配置文件是否完整，或重置配置",
            "ConnectionError": "💡 建议: 检查网络连接，或更换 API 地址",
            "TimeoutError": "💡 建议: 增加超时时间，或减少数据量",
            "MemoryError": "💡 建议: 关闭其他程序，或分批处理数据",
            "AttributeError": "💡 建议: 检查依赖版本，或重新安装依赖",
            "ImportError": "💡 建议: 运行 pip install -r requirements.txt",
        }
        
        tip = recovery_tips.get(error_type, "💡 建议: 查看日志获取更多信息，或联系技术支持")
        
        msg = ErrorHandler.handle_error(error, context)
        return f"{msg}\n\n{tip}"
    
    @staticmethod
    def safe_execute(func: Callable, *args, **kwargs) -> Tuple[bool, Any]:
        """安全执行函数"""
        try:
            result = func(*args, **kwargs)
            return True, result
        except Exception as e:
            return False, e
    
    @staticmethod
    def retry_execute(
        func: Callable,
        max_retries: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0,
        *args,
        **kwargs
    ) -> Tuple[bool, Any]:
        """带重试的执行函数
        
        Args:
            func: 要执行的函数
            max_retries: 最大重试次数
            delay: 初始延迟时间（秒）
            backoff: 延迟倍增因子
            *args, **kwargs: 函数参数
        
        Returns:
            (成功标志, 结果或异常)
        """
        last_error = None
        current_delay = delay
        
        for attempt in range(max_retries):
            try:
                result = func(*args, **kwargs)
                return True, result
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(current_delay)
                    current_delay *= backoff
        
        return False, last_error


def handle_errors(context: str = "", show_recovery: bool = True):
    """错误处理装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                ErrorHandler.show_error(e, context, show_recovery)
                return None
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            success, result = ErrorHandler.retry_execute(
                func, max_retries, delay, backoff, *args, **kwargs
            )
            if success:
                return result
            else:
                raise result  # 抛出最后一次的异常
        return wrapper
    return decorator
