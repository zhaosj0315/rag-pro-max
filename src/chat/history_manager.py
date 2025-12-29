"""聊天历史管理器"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime


class HistoryManager:
    """聊天历史管理器"""
    
    HISTORY_DIR = "chat_histories"
    
    @classmethod
    def load(cls, kb_id: str) -> List[Dict]:
        """加载对话历史 (默认会话)"""
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
        """保存对话历史 (默认会话)"""
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
        """清空对话历史 (默认会话)"""
        try:
            path = cls._get_path(kb_id)
            if os.path.exists(path):
                os.remove(path)
            return True
        except Exception:
            return False
            
    @classmethod
    def list_sessions(cls, kb_id: str) -> List[Dict]:
        """获取知识库的所有会话列表"""
        sessions = []
        if not os.path.exists(cls.HISTORY_DIR):
            return []
            
        # 1. 添加默认会话 (如果有且不为空)
        default_path = cls._get_path(kb_id)
        if os.path.exists(default_path):
            try:
                stats = os.stat(default_path)
                # 检查内容是否为空
                with open(default_path, 'r') as f:
                    data = json.load(f)
                    if data: # 只有非空才显示
                        title = "默认会话"
                        if len(data) > 0:
                            first_msg = next((m['content'] for m in data if m['role'] == 'user'), None)
                            if first_msg:
                                title = first_msg[:20].strip() + ("..." if len(first_msg)>20 else "")
                        
                        sessions.append({
                            "id": None, # None means default
                            "title": title,
                            "updated_at": datetime.fromtimestamp(stats.st_mtime),
                            "is_default": True
                        })
            except: pass
            
        # 2. 扫描命名会话
        prefix = f"{kb_id}@"
        for f in os.listdir(cls.HISTORY_DIR):
            if f.startswith(prefix) and f.endswith(".json"):
                session_id = f[len(prefix):-5]
                path = os.path.join(cls.HISTORY_DIR, f)
                try:
                    stats = os.stat(path)
                    # 尝试读取第一条消息作为标题
                    title = f"会话 {session_id[:6]}"
                    try:
                        with open(path, 'r') as jf:
                            data = json.load(jf)
                            if data:
                                first_msg = next((m['content'] for m in data if m['role'] == 'user'), None)
                                if first_msg:
                                    title = first_msg[:20].strip() + ("..." if len(first_msg)>20 else "")
                    except: pass
                    
                    sessions.append({
                        "id": session_id,
                        "title": title,
                        "updated_at": datetime.fromtimestamp(stats.st_mtime),
                        "is_default": False
                    })
                except: pass
                
        # 按时间倒序排序
        sessions.sort(key=lambda x: x['updated_at'], reverse=True)
        return sessions

    @classmethod
    def load_session(cls, kb_id: str, session_id: Optional[str] = None) -> List[Dict]:
        """加载特定会话"""
        if not session_id:
            return cls.load(kb_id)
        
        path = os.path.join(cls.HISTORY_DIR, f"{kb_id}@{session_id}.json")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return []

    @classmethod
    def save_session(cls, kb_id: str, messages: List[Dict], session_id: Optional[str] = None) -> bool:
        """保存特定会话"""
        if not session_id:
            return cls.save(kb_id, messages)
            
        try:
            os.makedirs(cls.HISTORY_DIR, exist_ok=True)
            path = os.path.join(cls.HISTORY_DIR, f"{kb_id}@{session_id}.json")
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
            
    @classmethod
    def delete_session(cls, kb_id: str, session_id: Optional[str] = None) -> bool:
        """删除特定会话"""
        if not session_id:
            return cls.clear(kb_id)
            
        try:
            path = os.path.join(cls.HISTORY_DIR, f"{kb_id}@{session_id}.json")
            if os.path.exists(path):
                os.remove(path)
            return True
        except:
            return False
    
    @classmethod
    def exists(cls, kb_id: str) -> bool:
        """检查历史是否存在"""
        return os.path.exists(cls._get_path(kb_id))
    
    @classmethod
    def _get_path(cls, kb_id: str) -> str:
        """获取历史文件路径"""
        return os.path.join(cls.HISTORY_DIR, f"{kb_id}.json")