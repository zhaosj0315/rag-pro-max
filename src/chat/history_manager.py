"""聊天历史管理器"""

import os
import json
from typing import List, Dict, Optional
from datetime import datetime


class HistoryManager:
    """聊天历史管理器"""
    
    HISTORY_DIR = "chat_histories"
    
    @classmethod
    def exists(cls, kb_id: str) -> bool:
        """检查历史是否存在"""
        return os.path.exists(cls._get_path(kb_id))
    
    @classmethod
    def _get_path(cls, kb_id: str) -> str:
        """获取历史文件路径"""
        return os.path.join(cls.HISTORY_DIR, f"{kb_id}.json")

    @classmethod
    def _get_full_path(cls, kb_id: str, session_id: Optional[str] = None) -> str:
        """获取完整路径"""
        if not session_id:
            return cls._get_path(kb_id)
        return os.path.join(cls.HISTORY_DIR, f"{kb_id}@{session_id}.json")

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
                with open(default_path, 'r') as f:
                    data = json.load(f)
                    # 兼容新旧格式
                    msgs = data.get("messages", []) if isinstance(data, dict) else data
                    meta = data.get("meta", {}) if isinstance(data, dict) else {}
                    
                    if msgs: 
                        title = meta.get("title", "默认会话")
                        if title == "默认会话" and len(msgs) > 0:
                            first_msg = next((m['content'] for m in msgs if m['role'] == 'user'), None)
                            if first_msg:
                                title = first_msg[:20].strip() + ("..." if len(first_msg)>20 else "")
                        
                        sessions.append({
                            "id": None, # None means default
                            "title": title,
                            "updated_at": datetime.fromtimestamp(stats.st_mtime),
                            "is_default": True,
                            "pinned": meta.get("pinned", False)
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
                    title = f"会话 {session_id[:6]}"
                    pinned = False
                    
                    try:
                        with open(path, 'r') as jf:
                            data = json.load(jf)
                            # 兼容新旧格式
                            msgs = data.get("messages", []) if isinstance(data, dict) else data
                            meta = data.get("meta", {}) if isinstance(data, dict) else {}
                            
                            if msgs:
                                title = meta.get("title", title)
                                pinned = meta.get("pinned", False)
                                
                                # 自动标题回退
                                if title.startswith("会话 ") and len(msgs) > 0:
                                    first_msg = next((m['content'] for m in msgs if m['role'] == 'user'), None)
                                    if first_msg:
                                        title = first_msg[:20].strip() + ("..." if len(first_msg)>20 else "")
                    except: pass
                    
                    sessions.append({
                        "id": session_id,
                        "title": title,
                        "updated_at": datetime.fromtimestamp(stats.st_mtime),
                        "is_default": False,
                        "pinned": pinned
                    })
                except: pass
                
        # 排序：置顶优先(True>False)，然后按时间倒序
        sessions.sort(key=lambda x: (x.get('pinned', False), x['updated_at']), reverse=True)
        return sessions

    @classmethod
    def get_latest_session_id(cls, kb_id: str) -> Optional[str]:
        """获取最近活跃的会话ID"""
        sessions = cls.list_sessions(kb_id)
        if not sessions:
            return None
        # 注意：list_sessions 现在是按置顶排序的，我们需要按时间排序找"最近"
        # 重新按时间排序
        time_sorted = sorted(sessions, key=lambda x: x['updated_at'], reverse=True)
        return time_sorted[0]['id']

    @classmethod
    def load_session(cls, kb_id: str, session_id: Optional[str] = None) -> List[Dict]:
        """加载特定会话"""
        path = cls._get_full_path(kb_id, session_id)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    return data.get("messages", [])
            except: pass
        return []

    @classmethod
    def save_session(cls, kb_id: str, messages: List[Dict], session_id: Optional[str] = None) -> bool:
        """保存特定会话"""
        try:
            os.makedirs(cls.HISTORY_DIR, exist_ok=True)
            path = cls._get_full_path(kb_id, session_id)
            
            # 读取现有数据以保留元数据
            existing_data = {}
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                except: pass
            
            if isinstance(existing_data, list):
                # 升级旧格式
                data = {
                    "meta": {"created_at": datetime.now().isoformat()},
                    "messages": messages
                }
            else:
                # 保留现有元数据
                data = existing_data
                data["messages"] = messages
                if "meta" not in data: data["meta"] = {}
                data["meta"]["updated_at"] = datetime.now().isoformat()
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except:
            return False
            
    @classmethod
    def delete_session(cls, kb_id: str, session_id: Optional[str] = None) -> bool:
        """删除特定会话"""
        try:
            path = cls._get_full_path(kb_id, session_id)
            if os.path.exists(path):
                os.remove(path)
            return True
        except:
            return False

    @classmethod
    def rename_session(cls, kb_id: str, session_id: Optional[str], new_title: str) -> bool:
        """重命名会话"""
        try:
            path = cls._get_full_path(kb_id, session_id)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    data = {"meta": {}, "messages": data}
                
                if "meta" not in data: data["meta"] = {}
                data["meta"]["title"] = new_title
                
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return True
        except: pass
        return False

    @classmethod
    def toggle_pin_session(cls, kb_id: str, session_id: Optional[str]) -> bool:
        """置顶/取消置顶会话"""
        try:
            path = cls._get_full_path(kb_id, session_id)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if isinstance(data, list):
                    data = {"meta": {}, "messages": data}
                
                if "meta" not in data: data["meta"] = {}
                current = data["meta"].get("pinned", False)
                data["meta"]["pinned"] = not current
                
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                return True
        except: pass
        return False