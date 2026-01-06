#!/usr/bin/env python3
"""
用户认证系统
提供登录、注册、会话管理功能
"""

import streamlit as st
import json
import hashlib
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

class UserAuth:
    """用户认证管理器"""
    
    def __init__(self):
        self.users_file = "config/users.json"
        self.ensure_users_file()
    
    def ensure_users_file(self):
        """确保用户文件存在"""
        if not os.path.exists(self.users_file):
            os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
            # 创建默认管理员（需要通过脚本设置密码）
            default_users = {
                "admin": {
                    "password_hash": "",  # 空密码，需要通过脚本重置
                    "role": "admin",
                    "created_at": datetime.now().isoformat(),
                    "last_login": None,
                    "password_reset_required": True
                }
            }
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(default_users, f, indent=2, ensure_ascii=False)
    
    def hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def load_users(self) -> Dict:
        """加载用户数据"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_users(self, users: Dict):
        """保存用户数据"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[Dict]]:
        """用户认证"""
        users = self.load_users()
        
        if username not in users:
            return False, None
        
        user = users[username]
        
        # 检查是否需要重置密码
        if user.get('password_reset_required', False) or not user.get('password_hash'):
            return False, {"error": "password_reset_required", "message": "管理员密码需要重置，请运行: python scripts/reset_admin_password.py"}
        
        if user['password_hash'] == self.hash_password(password):
            # 更新最后登录时间
            user['last_login'] = datetime.now().isoformat()
            users[username] = user
            self.save_users(users)
            
            return True, {
                'username': username,
                'role': user['role'],
                'created_at': user['created_at'],
                'last_login': user['last_login']
            }
        
        return False, None
    
    def register_user(self, username: str, password: str, role: str = "user") -> bool:
        """注册新用户"""
        users = self.load_users()
        
        if username in users:
            return False
        
        users[username] = {
            "password_hash": self.hash_password(password),
            "role": role,
            "created_at": datetime.now().isoformat(),
            "last_login": None
        }
        
        self.save_users(users)
        return True
    
    def create_guest_session(self) -> Dict:
        """创建游客会话"""
        import uuid
        from datetime import datetime
        
        guest_id = f"guest_{uuid.uuid4().hex[:8]}"
        
        guest_info = {
            'username': guest_id,
            'role': 'guest',
            'created_at': datetime.now().isoformat(),
            'last_login': datetime.now().isoformat(),
            'is_temporary': True
        }
        
        return guest_info
    
    def cleanup_guest_data(self, guest_id: str):
        """清理游客数据"""
        import shutil
        
        # 清理游客知识库
        guest_kb_path = f"vector_db_storage/{guest_id}"
        if os.path.exists(guest_kb_path):
            shutil.rmtree(guest_kb_path)
        
        # 清理游客对话历史
        guest_chat_path = f"chat_histories/{guest_id}"
        if os.path.exists(guest_chat_path):
            shutil.rmtree(guest_chat_path)
        
        # 清理游客临时文件
        guest_temp_path = f"temp_uploads/{guest_id}"
        if os.path.exists(guest_temp_path):
            shutil.rmtree(guest_temp_path)
    
    def get_all_users(self) -> Dict:
        """获取所有用户（管理员专用）"""
        return self.load_users()
    
    def delete_user(self, username: str) -> bool:
        """删除用户"""
        if username == "admin":  # 保护管理员账户
            return False
            
        users = self.load_users()
        if username in users:
            del users[username]
            self.save_users(users)
            return True
        return False

# 全局认证实例
user_auth = UserAuth()
