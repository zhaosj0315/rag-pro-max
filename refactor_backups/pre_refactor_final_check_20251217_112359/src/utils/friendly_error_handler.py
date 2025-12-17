"""
友好错误处理器
将技术性错误转换为用户友好的提示
"""

import streamlit as st
import traceback
from functools import wraps

class FriendlyErrorHandler:
    def __init__(self):
        self.error_solutions = {
            # 文件相关错误
            "FileNotFoundError": {
                "message": "📁 找不到指定的文件",
                "solution": "请检查文件路径是否正确，或重新选择文件"
            },
            "PermissionError": {
                "message": "🔒 没有文件访问权限", 
                "solution": "请检查文件权限，或选择其他文件"
            },
            "UnicodeDecodeError": {
                "message": "📝 文件编码格式不支持",
                "solution": "请使用UTF-8编码保存文件，或转换文件格式"
            },
            
            # 网络相关错误
            "ConnectionError": {
                "message": "🌐 网络连接失败",
                "solution": "请检查网络连接，或稍后重试"
            },
            "TimeoutError": {
                "message": "⏰ 请求超时",
                "solution": "网络较慢，请稍后重试或检查网络连接"
            },
            "requests.exceptions.RequestException": {
                "message": "🌐 网络请求失败",
                "solution": "请检查网络连接和URL是否正确"
            },
            
            # 模型相关错误
            "OutOfMemoryError": {
                "message": "💾 内存不足",
                "solution": "请关闭其他程序释放内存，或减少处理的文件数量"
            },
            "CUDA out of memory": {
                "message": "🎮 GPU内存不足", 
                "solution": "请减少批处理大小，或重启应用释放GPU内存"
            },
            "Model not found": {
                "message": "🤖 AI模型未找到",
                "solution": "请检查模型配置，或重新下载模型文件"
            },
            
            # API相关错误
            "Invalid API key": {
                "message": "🔑 API密钥无效",
                "solution": "请检查API密钥是否正确，或重新获取密钥"
            },
            "Rate limit exceeded": {
                "message": "🚦 API调用频率超限",
                "solution": "请稍后重试，或升级API套餐"
            },
            
            # 数据处理错误
            "JSONDecodeError": {
                "message": "📄 数据格式错误",
                "solution": "请检查文件格式是否正确，或重新保存文件"
            },
            "KeyError": {
                "message": "📋 数据字段缺失",
                "solution": "文件可能损坏或格式不完整，请检查文件内容"
            }
        }
    
    def handle_error(self, error, context="操作"):
        """处理错误并显示友好提示"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # 查找匹配的错误类型
        friendly_info = None
        for error_pattern, info in self.error_solutions.items():
            if error_pattern in error_type or error_pattern in error_message:
                friendly_info = info
                break
        
        if friendly_info:
            # 显示友好错误信息
            st.error(f"❌ {friendly_info['message']}")
            st.info(f"💡 **解决方案**: {friendly_info['solution']}")
        else:
            # 通用错误处理
            st.error(f"❌ {context}失败")
            st.info(f"💡 **错误详情**: {error_message}")
        
        # 显示详细错误信息（可展开）
        with st.expander("🔍 技术详情（开发者用）", expanded=False):
            st.code(f"错误类型: {error_type}")
            st.code(f"错误信息: {error_message}")
            if hasattr(error, '__traceback__'):
                st.code(traceback.format_exc())
    
    def safe_execute(self, func, context="操作", show_spinner=True):
        """安全执行函数，自动处理错误"""
        try:
            if show_spinner:
                with st.spinner(f"⏳ 正在{context}..."):
                    return func()
            else:
                return func()
        except Exception as e:
            self.handle_error(e, context)
            return None
    
    def error_boundary(self, context="操作"):
        """错误边界装饰器"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    self.handle_error(e, context)
                    return None
            return wrapper
        return decorator
    
    def show_recovery_options(self, error_type):
        """显示恢复选项"""
        st.markdown("### 🔧 恢复选项")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 重试", use_container_width=True):
                st.rerun()
        
        with col2:
            if st.button("🧹 清理缓存", use_container_width=True):
                # 清理缓存
                if hasattr(st, 'cache_data'):
                    st.cache_data.clear()
                st.success("✅ 缓存已清理")
                st.rerun()
        
        with col3:
            if st.button("🏠 返回首页", use_container_width=True):
                # 重置会话状态
                for key in list(st.session_state.keys()):
                    if key not in ['current_user', 'login_time']:
                        del st.session_state[key]
                st.rerun()

# 全局友好错误处理器
error_handler = FriendlyErrorHandler()
