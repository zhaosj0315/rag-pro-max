#!/usr/bin/env python3
"""
改进的错误处理器
"""
import streamlit as st
from typing import Optional

class UserFriendlyErrorHandler:
    @staticmethod
    def show_error(error_type: str, message: str, suggestion: Optional[str] = None):
        """显示用户友好的错误信息"""
        error_messages = {
            "file_upload": "文件上传失败",
            "processing": "文档处理出错", 
            "query": "查询执行失败",
            "config": "配置加载错误"
        }
        
        title = error_messages.get(error_type, "系统错误")
        
        with st.error(title):
            st.write(f"错误详情: {message}")
            if suggestion:
                st.write(f"建议: {suggestion}")
            st.write("如果问题持续存在，请联系技术支持。")
    
    @staticmethod
    def show_success(message: str):
        """显示成功信息"""
        st.success(f"✅ {message}")
    
    @staticmethod
    def show_warning(message: str):
        """显示警告信息"""
        st.warning(f"⚠️ {message}")
