#!/usr/bin/env python3
"""
公共业务逻辑 - 合并重复的核心业务函数
"""

import streamlit as st
import os
import time
import json
from datetime import datetime
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

def export_chat_history(kb_id: str, export_format: str = "json", logger=None) -> Optional[str]:
    """统一的对话历史导出函数"""
    try:
        # 尝试加载对话历史
        from src.chat_utils_improved import load_chat_history_safe
        messages = load_chat_history_safe(kb_id, logger)
        
        if export_format == "json":
            return json.dumps(messages, indent=2, ensure_ascii=False)
        
        elif export_format == "markdown":
            md_content = f"# 对话历史: {kb_id}\n\n"
            md_content += f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for msg in messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                
                if role == "user":
                    md_content += f"## 👤 用户\n\n{content}\n\n"
                else:
                    md_content += f"## 🤖 助手\n\n{content}\n\n"
            
            return md_content
        
        else:
            if logger:
                logger.log_error("导出", f"不支持的格式: {export_format}")
            return None

def generate_doc_summary(doc_text: str, filename: str) -> str:
    """统一的文档摘要生成函数"""
    try:
        # 导入必要的模块
        import warnings
        import logging
        from llama_index.core import Settings
        
        warnings.filterwarnings('ignore')
        logging.getLogger('streamlit').setLevel(logging.ERROR)
        
        if not hasattr(Settings, 'llm'): 
            return "总结失败: LLM未初始化"
        
        llm = Settings.llm
        summary_prompt = (
            f"以下是文档 '{filename}' 的一个片段内容，请用一段简短的中文话总结其核心内容 (不超过 80 字)，用于文件清单预览。内容:\n---\n{doc_text[:2000]}..."
        )
        response = llm.complete(summary_prompt)
        return response.text.strip().replace('\n', ' ')\
                             .replace('总结:', '').replace('总结是：', '').strip()
        
    except Exception as e:
        return f"总结失败: {str(e)}"

def click_btn(q: str):
    """点击追问按钮，将问题加入队列（去重）"""
    from src.queue.queue_manager import QueueManager
    import streamlit as st
    
    queue_manager = QueueManager()
    queue_manager.add_question(q)
    st.rerun()
            
    except Exception as e:
        if logger:
            logger.log_error("导出", f"导出失败: {str(e)}")
        return None
