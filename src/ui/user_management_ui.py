"""
用户管理界面（管理员功能）
"""

import streamlit as st
from src.services.auth_service import get_auth_service

class UserManagementUI:
    def __init__(self):
        self.auth_service = get_auth_service()
    
    def show_user_management(self):
        """显示用户管理界面（简化版）"""
        # 获取所有用户
        users = self.auth_service.get_all_users()
        
        if not users:
            st.info("暂无用户")
            return
        
        # 统计信息
        active_users = sum(1 for user in users if user.get('is_active', True))
        total_users = len(users)
        
        # 知识库统计
        from src.ui.kb_management_ui import get_knowledge_base_list
        all_kbs = get_knowledge_base_list()  # 管理员可以看到所有知识库
        total_kbs = len(all_kbs)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总用户", total_users)
        with col2:
            st.metric("活跃用户", active_users)
        with col3:
            st.metric("知识库", total_kbs)
        
        st.info("💡 提示：在个人信息标签页可以下载用户的所有知识库数据")
        
        # 用户列表（简化显示）
        st.markdown("**用户列表**")
        for user in users:
            # 统计该用户的知识库数量
            user_kbs = [kb for kb in all_kbs if kb.get('owner') == user['username']]
            
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                role_icon = "👑" if user.get('role') == 'admin' else "👤"
                st.write(f"{role_icon} {user['username']}")
            
            with col2:
                st.write(f"📚 {len(user_kbs)}")  # 知识库数量
            
            with col3:
                status = "✅" if user.get('is_active', True) else "❌"
                st.write(status)
            
            with col4:
                if user.get('is_active', True):
                    if st.button("禁用", key=f"disable_{user['username']}", help="禁用用户"):
                        self._toggle_user_status(user['username'], False)
                        st.rerun()
                else:
                    if st.button("启用", key=f"enable_{user['username']}", help="启用用户"):
                        self._toggle_user_status(user['username'], True)
                        st.rerun()
    
    def _toggle_user_status(self, username: str, is_active: bool):
        """切换用户状态"""
        if username in self.auth_service.users:
            self.auth_service.users[username]['is_active'] = is_active
            self.auth_service._save_users()
            
            status_text = "启用" if is_active else "禁用"
            st.success(f"已{status_text}用户 {username}")

def show_admin_panel():
    """显示管理员面板"""
    auth_service = get_auth_service()
    
    # 检查管理员权限
    if auth_service.is_admin():
        user_mgmt = UserManagementUI()
        user_mgmt.show_user_management()
    else:
        st.warning("只有管理员可以访问此页面")
