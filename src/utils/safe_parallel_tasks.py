"""
多进程安全的工作函数
不依赖Streamlit或其他UI组件
"""

import os
import json
from typing import Dict, Any, Tuple

def safe_process_node_worker(task_data: Tuple[Dict[str, Any], str]) -> Dict[str, Any]:
    """
    多进程安全的节点处理函数
    
    Args:
        task_data: (node_data, kb_name) 元组
        
    Returns:
        Dict: 包含节点信息的字典（用于前端渲染）
    """
    try:
        node_data, kb_name = task_data
        
        # 提取基本信息
        metadata = node_data.get('metadata', {})
        score = node_data.get('score', 0.0)
        text = node_data.get('text', '')
        node_id = node_data.get('node_id', 'unknown')
        
        # 安全地获取文件名
        file_name = metadata.get('file_name', '未知文件')
        
        # 🔍 提取页码信息
        page_info = ""
        if 'page_number' in metadata:
            page_num = metadata['page_number']
            if isinstance(page_num, (int, str)) and str(page_num).isdigit():
                page_info = f"[第{page_num}页]"
        elif 'page_label' in metadata:
            page_label = metadata['page_label']
            if page_label:
                page_info = f"[{page_label}]"
        
        # 构建显示名称
        display_name = file_name
        if page_info:
            display_name = f"{file_name} {page_info}"
        
        # 返回结构化数据
        return {
            'file_name': file_name,
            'display_name': display_name,
            'page_info': page_info,
            'score': score,
            'text': text,
            'node_id': node_id,
            'metadata': metadata
        }
        
    except Exception as e:
        # 返回错误信息的字典结构
        return {
            'error': str(e),
            'file_name': 'Error',
            'display_name': 'Error',
            'text': f"处理节点时出错: {str(e)}"
        }

def extract_metadata_task(file_path: str) -> Dict[str, Any]:
    """
    多进程安全的元数据提取函数
    
    Args:
        file_path: 文件路径
        
    Returns:
        Dict: 元数据字典
    """
    try:
        # 基本文件信息
        file_stat = os.stat(file_path)
        file_name = os.path.basename(file_path)
        
        metadata = {
            'file_name': file_name,
            'file_size': file_stat.st_size,
            'file_path': file_path,
            'extension': os.path.splitext(file_name)[1].lower(),
            'modified_time': file_stat.st_mtime
        }
        
        return metadata
        
    except Exception as e:
        return {
            'file_name': os.path.basename(file_path) if file_path else '未知',
            'error': str(e)
        }

# 兼容性别名
safe_extract_metadata_task = extract_metadata_task
