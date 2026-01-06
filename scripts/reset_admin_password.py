#!/usr/bin/env python3
"""
管理员密码重置脚本
用于重置管理员密码，避免在前端暴露
"""

import sys
import os
import json
import hashlib
from datetime import datetime

def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()

def reset_admin_password():
    """重置管理员密码"""
    users_file = "config/users.json"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(users_file), exist_ok=True)
    
    # 读取现有用户数据
    users = {}
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
        except:
            pass
    
    # 提示输入新密码
    print("🔐 管理员密码重置工具")
    print("=" * 30)
    
    new_password = input("请输入新的管理员密码: ").strip()
    
    if len(new_password) < 6:
        print("❌ 密码长度至少6位")
        return False
    
    confirm_password = input("请再次确认密码: ").strip()
    
    if new_password != confirm_password:
        print("❌ 两次输入的密码不一致")
        return False
    
    # 更新管理员密码
    users["admin"] = {
        "password_hash": hash_password(new_password),
        "role": "admin",
        "created_at": users.get("admin", {}).get("created_at", datetime.now().isoformat()),
        "last_login": users.get("admin", {}).get("last_login")
    }
    
    # 保存用户数据
    with open(users_file, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    
    print("✅ 管理员密码重置成功！")
    print(f"用户名: admin")
    print(f"新密码: {new_password}")
    print("\n⚠️  请妥善保管密码，不要在代码中硬编码！")
    
    return True

if __name__ == "__main__":
    try:
        reset_admin_password()
    except KeyboardInterrupt:
        print("\n❌ 操作已取消")
    except Exception as e:
        print(f"❌ 重置失败: {e}")
