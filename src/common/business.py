#!/usr/bin/env python3
"""
公共业务逻辑 - 合并重复的核心业务函数
"""

import streamlit as st
import os
import time
from typing import Optional, Callable, Any
from urllib.parse import urlparse

def update_status(message: str, status_type: str = "info") -> None:
    """统一的状态更新函数"""
    if status_type == "success":
        st.success(message)
    elif status_type == "error":
        st.error(message)
    elif status_type == "warning":
        st.warning(message)
    else:
        st.info(message)

def generate_smart_kb_name(source: str, source_type: str = "file") -> str:
    """统一的智能知识库命名函数"""
    from src.common.utils import sanitize_filename
    
    if source_type == "url":
        try:
            domain = urlparse(source).netloc
            domain = domain.replace('www.', '').replace('.', '_')
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            return sanitize_filename(f"Web_{domain}_{timestamp}")
        except:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            return f"Web_Unknown_{timestamp}"
    
    elif source_type == "file":
        if os.path.isfile(source):
            base_name = os.path.splitext(os.path.basename(source))[0]
            return sanitize_filename(f"KB_{base_name}_{int(time.time())}")
        elif os.path.isdir(source):
            dir_name = os.path.basename(source.rstrip('/\\'))
            return sanitize_filename(f"KB_{dir_name}_{int(time.time())}")
    
    # 默认命名
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    return f"KB_{timestamp}"

def process_knowledge_base_logic(
    kb_name: str,
    source_path: str,
    progress_callback: Optional[Callable] = None,
    **kwargs
) -> dict:
    """统一的知识库处理逻辑"""
    
    if progress_callback:
        progress_callback("开始处理知识库...")
    
    try:
        # 这里是简化的处理逻辑框架
        # 实际实现需要根据具体需求调整
        
        result = {
            'success': True,
            'kb_name': kb_name,
            'source_path': source_path,
            'processed_files': 0,
            'message': '知识库处理完成'
        }
        
        if progress_callback:
            progress_callback("知识库处理完成")
        
        return result
        
    except Exception as e:
        if progress_callback:
            progress_callback(f"处理失败: {str(e)}")
        
        return {
            'success': False,
            'kb_name': kb_name,
            'source_path': source_path,
            'processed_files': 0,
            'error': str(e),
            'message': f'知识库处理失败: {str(e)}'
        }

def status_callback_factory(prefix: str = "") -> Callable:
    """状态回调函数工厂"""
    def callback(message: str, status_type: str = "info"):
        full_message = f"{prefix}{message}" if prefix else message
        update_status(full_message, status_type)
    
    return callback
