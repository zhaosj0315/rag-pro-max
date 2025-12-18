"""
并行任务函数
Stage 6 - 多进程安全的任务函数
"""

from src.metadata_manager import MetadataManager


def extract_metadata_task(task):
    """
    单个文件的元数据提取任务（多进程安全）
    
    Args:
        task: (file_path, file_name, doc_ids, text_sample, persist_dir)
        
    Returns:
        (file_name, metadata_dict)
    """
    fp, fname, doc_ids, text_sample, persist_dir = task
    temp_mgr = MetadataManager(persist_dir)
    return fname, temp_mgr.add_file_metadata(fp, doc_ids, text_sample)


def process_node_worker(args):
    """
    多进程处理单个节点（问答场景）
    
    Args:
        args: (node_data, kb_name)
        
    Returns:
        dict: 处理后的节点信息，包含 file, score, text
    """
    node_data, kb_name = args
    try:
        metadata = node_data.get('metadata', {})
        file_name = metadata.get('file_name', 'Unknown')
        score = node_data.get('score', 0.0)
        text = node_data.get('text', '')
        node_id = node_data.get('node_id', 'unknown')
        
        return {
            "file_name": file_name, 
            "score": score, 
            "text": text[:150].replace("\n", " ") + "...",
            "node_id": node_id
        }
    except:
        return None
