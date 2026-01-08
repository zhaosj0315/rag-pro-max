import json
import os
import hashlib
from datetime import datetime

USER_CONFIG_PATH = "config/users.json"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_CONFIG_PATH):
        try:
            with open(USER_CONFIG_PATH, 'r', encoding='utf-8') as f:
                users = json.load(f)
                if not users: # 如果文件为空
                    return _init_admin()
                return users
        except:
            return _init_admin()
    return _init_admin()

def _init_admin():
    """初始化默认管理员"""
    admin_user = {
        "admin": {
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "created_at": datetime.now().isoformat(),
            "is_active": True,
            "kb_whitelist": [],
            "storage_quota_mb": -1  # 无限
        }
    }
    save_users(admin_user)
    return admin_user

def save_users(users):
    os.makedirs(os.path.dirname(USER_CONFIG_PATH), exist_ok=True)
    with open(USER_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

def register_user(username, password, role="standard_user"):
    users = load_users()
    if username in users:
        return False, "用户名已存在"
    
    users[username] = {
        "password_hash": hash_password(password),
        "role": role,
        "created_at": datetime.now().isoformat(),
        "is_active": True,
        "kb_whitelist": [],
        "storage_quota_mb": 100  # 默认 100MB
    }
    save_users(users)
    return True, "注册成功"

def authenticate_user(username, password):
    users = load_users()
    if username not in users:
        return False, "用户不存在"
    
    user_info = users[username]
    if not user_info.get('is_active', True):
        return False, "账号已被禁用"
        
    if user_info['password_hash'] == hash_password(password):
        # 更新最后登录时间
        user_info['last_login'] = datetime.now().isoformat()
        save_users(users)
        return True, user_info
    return False, "密码错误"
