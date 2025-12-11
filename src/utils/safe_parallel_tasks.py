"""
多进程安全的工作函数
不依赖Streamlit或其他UI组件
"""

import os
import json
from typing import Dict, Any, Tuple

def safe_process_node_worker(task_data: Tuple[Dict[str, Any], str]) -> str:
    """
    多进程安全的节点处理函数
    
    Args:
        task_data: (node_data, kb_name) 元组
        
    Returns:
        str: 处理结果的HTML字符串
    """
    try:
        node_data, kb_name = task_data
        
        # 提取基本信息
        metadata = node_data.get('metadata', {})
        score = node_data.get('score', 0.0)
        text = node_data.get('text', '')
        
        # 安全地获取文件名
        file_name = metadata.get('file_name', '未知文件')
        if isinstance(file_name, str) and len(file_name) > 50:
            file_name = file_name[:47] + "..."
        
        # 安全地获取页码
        page_label = metadata.get('page_label', '')
        if page_label:
            page_info = f" (第{page_label}页)"
        else:
            page_info = ""
        
        # 生成简洁的文本格式（避免HTML截断）
        content_preview = text[:200] + "..." if len(text) > 200 else text
        
        result_text = f"""📌 相关度: {score:.3f} | 📄 {file_name}{page_info}
        
{content_preview}

---"""
        
        return result_text.strip()
        
    except Exception as e:
        # 返回错误信息而不是抛出异常
        return f'<div style="color: red;">处理节点时出错: {str(e)}</div>'

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
