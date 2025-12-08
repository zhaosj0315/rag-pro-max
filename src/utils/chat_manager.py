"""
聊天管理模块 - 管理对话历史的加载和保存
"""
import os
import json


# 对话历史目录
HISTORY_DIR = "chat_histories"


def load_chat_history(kb_id: str) -> list:
    """
    加载知识库的对话历史
    
    Args:
        kb_id: 知识库ID
    
    Returns:
        list: 消息列表，如果不存在则返回空列表
    """
    path = os.path.join(HISTORY_DIR, f"{kb_id}.json")
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 对话历史加载失败: {e}")
    return []


def save_chat_history(kb_id: str, messages: list) -> bool:
    """
    保存知识库的对话历史
    
    Args:
        kb_id: 知识库ID
        messages: 消息列表
    
    Returns:
        bool: 是否保存成功
    """
    try:
        # 确保目录存在
        if not os.path.exists(HISTORY_DIR):
            os.makedirs(HISTORY_DIR)
        
        path = os.path.join(HISTORY_DIR, f"{kb_id}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(messages, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ 对话历史保存失败: {e}")
        return False


def clear_chat_history(kb_id: str) -> bool:
    """
    清空知识库的对话历史
    
    Args:
        kb_id: 知识库ID
    
    Returns:
        bool: 是否清空成功
    """
    try:
        path = os.path.join(HISTORY_DIR, f"{kb_id}.json")
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception as e:
        print(f"❌ 对话历史清空失败: {e}")
        return False


def get_chat_history_path(kb_id: str) -> str:
    """
    获取对话历史文件路径
    
    Args:
        kb_id: 知识库ID
    
    Returns:
        str: 文件路径
    """
    return os.path.join(HISTORY_DIR, f"{kb_id}.json")


def chat_history_exists(kb_id: str) -> bool:
    """
    检查对话历史是否存在
    
    Args:
        kb_id: 知识库ID
    
    Returns:
        bool: 是否存在
    """
    path = get_chat_history_path(kb_id)
    return os.path.exists(path)
