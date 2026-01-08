import json
import os

class PermissionManager:
    def __init__(self, templates_path="config/role_templates.json"):
        self.templates_path = templates_path
        self.roles = self._load_templates()

    def _load_templates(self):
        if os.path.exists(self.templates_path):
            with open(self.templates_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "admin": {"name": "管理员", "permissions": ["*"]},
            "standard_user": {"name": "注册用户", "permissions": ["create_kb", "upload_files", "chat"]},
            "guest": {"name": "访客", "permissions": ["chat"]}
        }

    def has_permission(self, username, permission):
        """实时检查用户权限"""
        from src.auth.user_auth import load_users
        users = load_users()
        user_info = users.get(username, {})
        
        # 访客处理
        if username == "guest_user":
            user_role = "guest"
        else:
            user_role = user_info.get("role", "guest")
            
        if user_role not in self.roles:
            return False
        
        role_data = self.roles[user_role]
        permissions = role_data.get("permissions", [])
        
        if "*" in permissions:
            return True
            
        return permission in permissions

    def get_role_name(self, user_role):
        return self.roles.get(user_role, {}).get("name", "未知角色")

permission_manager = PermissionManager()
