"""
用户认证服务
提供基础的用户登录、注册、会话管理功能
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import streamlit as st

class AuthService:
    def __init__(self):
        self.users_file = "data/users.json"
        self.sessions_file = "data/sessions.json"
        self._ensure_data_dir()
        self._load_users()
        self._create_default_admin()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        os.makedirs("data", exist_ok=True)
    
    def _load_users(self):
        """加载用户数据"""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.users = json.load(f)
        else:
            self.users = {}
            self._save_users()
    
    def _save_users(self):
        """保存用户数据"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(self.users, f, ensure_ascii=False, indent=2)
    
    def _create_default_admin(self):
        """创建默认管理员账户"""
        admin_username = "admin"
        admin_password = "admin123"
        
        if admin_username not in self.users:
            self.users[admin_username] = {
                "password": self._hash_password(admin_password),
                "email": "admin@ragpromax.com",
                "created_at": datetime.now().isoformat(),
                "last_login": None,
                "is_active": True,
                "role": "admin"
            }
            self._save_users()
            print(f"✅ 已创建管理员账户: {admin_username} / {admin_password}")
    
    def _hash_password(self, password: str) -> str:
        """密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, username: str, password: str, email: str = "") -> bool:
        """注册用户"""
        if username in self.users:
            return False
        
        self.users[username] = {
            "password": self._hash_password(password),
            "email": email,
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True
        }
        self._save_users()
        return True
    
    def authenticate(self, username: str, password: str) -> bool:
        """验证用户"""
        if username not in self.users:
            return False
        
        user = self.users[username]
        if not user.get("is_active", True):
            return False
        
        if user["password"] == self._hash_password(password):
            # 更新最后登录时间
            self.users[username]["last_login"] = datetime.now().isoformat()
            self._save_users()
            return True
        
        return False
    
    def get_user_info(self, username: str) -> Optional[Dict]:
        """获取用户信息"""
        if username in self.users:
            user_info = self.users[username].copy()
            del user_info["password"]  # 不返回密码
            return user_info
        return None
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return st.session_state.get("authenticated", False)
    
    def get_current_user(self) -> Optional[str]:
        """获取当前登录用户"""
        if self.is_logged_in():
            return st.session_state.get("username")
        return None
    
    def login(self, username: str) -> None:
        """设置登录状态"""
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.login_time = datetime.now().isoformat()
    
    def logout(self) -> None:
        """登出"""
        for key in ["authenticated", "username", "login_time"]:
            if key in st.session_state:
                del st.session_state[key]
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """修改密码"""
        if not self.authenticate(username, old_password):
            return False
        
        self.users[username]["password"] = self._hash_password(new_password)
        self._save_users()
        return True
    
    def is_admin(self, username: str = None) -> bool:
        """检查是否为管理员"""
        if username is None:
            username = self.get_current_user()
        
        if username and username in self.users:
            return self.users[username].get("role") == "admin"
        return False
    
    def get_all_users(self) -> List[Dict]:
        """获取所有用户信息（管理员功能）"""
        users_list = []
        for username, user_data in self.users.items():
            user_info = user_data.copy()
            del user_info["password"]
            user_info["username"] = username
            users_list.append(user_info)
        return users_list

# 全局认证服务实例
_auth_service = None

def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
