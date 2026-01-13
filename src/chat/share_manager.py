"""
分享管理器 - 负责会话的快照生成与持久化分享
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional

class ShareManager:
    SHARE_FILE = "config/shared_sessions.json"
    
    @classmethod
    def _load_shares(cls) -> Dict:
        if not os.path.exists(cls.SHARE_FILE):
            return {}
        try:
            with open(cls.SHARE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    @classmethod
    def _save_shares(cls, shares: Dict):
        os.makedirs(os.path.dirname(cls.SHARE_FILE), exist_ok=True)
        with open(cls.SHARE_FILE, 'w', encoding='utf-8') as f:
            json.dump(shares, f, ensure_ascii=False, indent=4)

    @classmethod
    def create_share(cls, kb_name: str, messages: List[Dict], creator: str) -> str:
        """为当前会话创建快照并返回分享ID"""
        shares = cls._load_shares()
        share_id = str(uuid.uuid4())[:12]
        
        shares[share_id] = {
            "kb_name": kb_name,
            "messages": messages,
            "creator": creator,
            "created_at": datetime.now().isoformat(),
            "view_count": 0
        }
        
        cls._save_shares(shares)
        return share_id

    @classmethod
    def get_share(cls, share_id: str) -> Optional[Dict]:
        """获取分享内容并增加阅读计数"""
        shares = cls._load_shares()
        if share_id in shares:
            shares[share_id]["view_count"] += 1
            cls._save_shares(shares)
            return shares[share_id]
        return None
