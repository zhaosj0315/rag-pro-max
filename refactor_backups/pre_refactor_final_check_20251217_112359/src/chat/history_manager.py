"""聊天历史管理器"""

import os
import json
from typing import List, Dict
from datetime import datetime


class HistoryManager:
    """聊天历史管理器"""
    
    HISTORY_DIR = "chat_histories"
    
    @classmethod
    def load(cls, kb_id: str) -> List[Dict]:
        """加载对话历史"""
        path = cls._get_path(kb_id)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []
    
    @classmethod
    def save(cls, kb_id: str, messages: List[Dict]) -> bool:
        """保存对话历史"""
        try:
            os.makedirs(cls.HISTORY_DIR, exist_ok=True)
            path = cls._get_path(kb_id)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    @classmethod
    def clear(cls, kb_id: str) -> bool:
        """清空对话历史"""
        try:
            path = cls._get_path(kb_id)
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception:
            return False
    
    @classmethod
    def exists(cls, kb_id: str) -> bool:
        """检查历史是否存在"""
        return os.path.exists(cls._get_path(kb_id))
    
    @classmethod
    def _get_path(cls, kb_id: str) -> str:
        """获取历史文件路径"""
        return os.path.join(cls.HISTORY_DIR, f"{kb_id}.json")
