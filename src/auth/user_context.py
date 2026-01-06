#!/usr/bin/env python3
"""
用户上下文管理器
提供基于用户的数据路径隔离
"""

import streamlit as st
import os

class UserContext:
    """用户上下文管理器"""
    
    @staticmethod
    def get_current_user() -> dict:
        """获取当前用户信息"""
        return st.session_state.get('user_context', {})
    
    @staticmethod
    def get_username() -> str:
        """获取当前用户名"""
        return UserContext.get_current_user().get('username', 'anonymous')
    
    @staticmethod
    def is_guest() -> bool:
        """判断是否为游客"""
        username = UserContext.get_username()
        return username.startswith('guest_')
    
    @staticmethod
    def is_admin() -> bool:
        """判断是否为管理员"""
        if UserContext.is_guest():
            return False
        return UserContext.get_current_user().get('is_admin', False)
    
    @staticmethod
    def get_user_kb_path(kb_name: str = None) -> str:
        """获取用户知识库路径"""
        username = UserContext.get_username()
        base_path = f"vector_db_storage/{username}"
        
        if kb_name:
            return f"{base_path}/{kb_name}"
        return base_path
    
    @staticmethod
    def get_user_chat_path(kb_name: str = None) -> str:
        """获取用户对话历史路径"""
        username = UserContext.get_username()
        base_path = f"chat_histories/{username}"
        
        if kb_name:
            return f"{base_path}/{kb_name}.json"
        return base_path
    
    @staticmethod
    def get_user_temp_path() -> str:
        """获取用户临时文件路径"""
        username = UserContext.get_username()
        return f"temp_uploads/{username}"
    
    @staticmethod
    def ensure_user_directories():
        """确保用户目录存在"""
        username = UserContext.get_username()
        
        directories = [
            f"vector_db_storage/{username}",
            f"chat_histories/{username}",
            f"temp_uploads/{username}"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def list_user_knowledge_bases():
        """列出用户的知识库"""
        if UserContext.is_admin():
            # 管理员可以看到所有用户的知识库
            return UserContext.list_all_knowledge_bases()
        else:
            # 普通用户只能看到自己的知识库
            user_kb_path = UserContext.get_user_kb_path()
            if not os.path.exists(user_kb_path):
                return []
            
            kbs = []
            for item in os.listdir(user_kb_path):
                item_path = os.path.join(user_kb_path, item)
                if os.path.isdir(item_path):
                    kbs.append(item)
            return sorted(kbs)
    
    @staticmethod
    def list_all_knowledge_bases():
        """列出所有知识库（管理员专用）"""
        if not os.path.exists("vector_db_storage"):
            return []
        
        all_kbs = []
        for username in os.listdir("vector_db_storage"):
            user_path = os.path.join("vector_db_storage", username)
            if os.path.isdir(user_path):
                for kb_name in os.listdir(user_path):
                    kb_path = os.path.join(user_path, kb_name)
                    if os.path.isdir(kb_path):
                        all_kbs.append(f"{username}/{kb_name}")
        
        return sorted(all_kbs)
    
    @staticmethod
    def migrate_existing_data():
        """迁移现有数据到admin用户下"""
        admin_kb_path = "vector_db_storage/admin"
        admin_chat_path = "chat_histories/admin"
        
        # 迁移知识库数据
        if os.path.exists("vector_db_storage") and not os.path.exists(admin_kb_path):
            # 检查是否有直接在vector_db_storage下的知识库
            for item in os.listdir("vector_db_storage"):
                item_path = os.path.join("vector_db_storage", item)
                if os.path.isdir(item_path) and item != "admin":
                    # 这可能是旧的知识库，移动到admin下
                    os.makedirs(admin_kb_path, exist_ok=True)
                    import shutil
                    shutil.move(item_path, os.path.join(admin_kb_path, item))
        
        # 迁移对话历史
        if os.path.exists("chat_histories") and not os.path.exists(admin_chat_path):
            # 检查是否有直接在chat_histories下的文件
            os.makedirs(admin_chat_path, exist_ok=True)
            for item in os.listdir("chat_histories"):
                if item.endswith('.json') and item != "admin":
                    item_path = os.path.join("chat_histories", item)
                    if os.path.isfile(item_path):
                        import shutil
                        shutil.move(item_path, os.path.join(admin_chat_path, item))
    
    @staticmethod
    def can_access_kb(kb_name: str) -> bool:
        """检查用户是否可以访问指定知识库"""
        try:
            import streamlit as st
            if not hasattr(st, 'session_state') or 'user_context' not in st.session_state:
                return True  # 向后兼容
            
            user_context = st.session_state.user_context
            username = user_context.get('username', '')
            is_admin = user_context.get('is_admin', False)
            
            # 管理员可以访问所有知识库
            if is_admin:
                return True
            
            # 普通用户只能访问自己的知识库
            user_kb_path = UserContext.get_user_kb_path(kb_name)
            return os.path.exists(user_kb_path)
            
        except Exception:
            return False
    
    @staticmethod
    def validate_kb_access(kb_name: str):
        """验证知识库访问权限并返回结果"""
        if not kb_name:
            return False, "知识库名称不能为空"
        
        if not UserContext.can_access_kb(kb_name):
            username = UserContext.get_username()
            return False, f"用户 {username} 无权访问知识库 '{kb_name}'"
        
        return True, "访问权限验证通过"

# 全局用户上下文实例
user_context = UserContext()
