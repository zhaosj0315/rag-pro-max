#!/usr/bin/env python3
"""
用户管理界面
"""

import streamlit as st
from src.auth.user_auth import user_auth
from src.auth.login_page import logout
import os
import shutil

def show_user_management():
    """显示用户管理界面"""
    user_context = st.session_state.get('user_context', {})
    
    st.title("👤 用户管理")
    
    # 当前用户信息
    st.subheader("📋 当前用户")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**用户名**: {user_context.get('username', 'Unknown')}")
    with col2:
        st.info(f"**角色**: {user_context.get('role', 'Unknown')}")
    with col3:
        if st.button("🚪 退出登录", type="secondary"):
            logout()
    
    st.markdown("---")
    
    # 管理员功能
    if user_context.get('is_admin', False):
        show_admin_panel()
    else:
        show_user_panel()

def show_admin_panel():
    """管理员面板"""
    st.subheader("🔧 管理员面板")
    
    tab1, tab2, tab3 = st.tabs(["👥 用户管理", "📊 使用统计", "🗂️ 数据管理"])
    
    with tab1:
        show_user_list()
        show_add_user_form()
    
    with tab2:
        show_usage_statistics()
    
    with tab3:
        show_data_management()

def show_user_panel():
    """普通用户面板"""
    st.subheader("📊 我的统计")
    
    username = st.session_state.user_context['username']
    
    # 用户知识库统计
    user_kb_path = f"vector_db_storage/{username}"
    if os.path.exists(user_kb_path):
        kb_count = len([d for d in os.listdir(user_kb_path) if os.path.isdir(os.path.join(user_kb_path, d))])
    else:
        kb_count = 0
    
    # 用户对话历史统计
    user_chat_path = f"chat_histories/{username}"
    if os.path.exists(user_chat_path):
        chat_count = len([f for f in os.listdir(user_chat_path) if f.endswith('.json')])
    else:
        chat_count = 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📚 我的知识库", kb_count)
    with col2:
        st.metric("💬 对话历史", chat_count)

def show_user_list():
    """显示用户列表"""
    st.markdown("#### 👥 用户列表")
    
    users = user_auth.get_all_users()
    
    if not users:
        st.info("暂无用户")
        return
    
    for username, user_data in users.items():
        with st.expander(f"👤 {username} ({user_data['role']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**创建时间**: {user_data['created_at'][:19]}")
            with col2:
                last_login = user_data.get('last_login')
                if last_login:
                    st.write(f"**最后登录**: {last_login[:19]}")
                else:
                    st.write("**最后登录**: 从未登录")
            with col3:
                if username != "admin":  # 保护管理员账户
                    if st.button(f"🗑️ 删除", key=f"del_{username}"):
                        if user_auth.delete_user(username):
                            # 删除用户数据
                            cleanup_user_data(username)
                            st.success(f"✅ 用户 {username} 已删除")
                            st.rerun()
                        else:
                            st.error("❌ 删除失败")

def show_add_user_form():
    """添加用户表单"""
    st.markdown("#### ➕ 添加新用户")
    
    with st.form("add_user_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_username = st.text_input("用户名")
        with col2:
            new_password = st.text_input("密码", type="password")
        with col3:
            new_role = st.selectbox("角色", ["user", "admin"])
        
        if st.form_submit_button("➕ 添加用户"):
            if new_username and new_password:
                if len(new_password) < 6:
                    st.error("❌ 密码长度至少6位")
                elif user_auth.register_user(new_username, new_password, new_role):
                    st.success(f"✅ 用户 {new_username} 添加成功")
                    st.rerun()
                else:
                    st.error("❌ 用户名已存在")
            else:
                st.error("❌ 请填写完整信息")

def show_usage_statistics():
    """显示使用统计"""
    st.markdown("#### 📊 系统使用统计")
    
    users = user_auth.get_all_users()
    total_users = len(users)
    
    # 统计各用户的知识库和对话数量
    user_stats = []
    for username in users.keys():
        # 知识库统计
        user_kb_path = f"vector_db_storage/{username}"
        kb_count = 0
        if os.path.exists(user_kb_path):
            kb_count = len([d for d in os.listdir(user_kb_path) if os.path.isdir(os.path.join(user_kb_path, d))])
        
        # 对话统计
        user_chat_path = f"chat_histories/{username}"
        chat_count = 0
        if os.path.exists(user_chat_path):
            chat_count = len([f for f in os.listdir(user_chat_path) if f.endswith('.json')])
        
        user_stats.append({
            'username': username,
            'role': users[username]['role'],
            'kb_count': kb_count,
            'chat_count': chat_count
        })
    
    # 显示统计表格
    if user_stats:
        import pandas as pd
        df = pd.DataFrame(user_stats)
        st.dataframe(df, use_container_width=True)
    
    # 总体统计
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("👥 总用户数", total_users)
    with col2:
        total_kbs = sum(stat['kb_count'] for stat in user_stats)
        st.metric("📚 总知识库", total_kbs)
    with col3:
        total_chats = sum(stat['chat_count'] for stat in user_stats)
        st.metric("💬 总对话数", total_chats)

def show_data_management():
    """数据管理"""
    st.markdown("#### 🗂️ 数据管理")
    
    st.warning("⚠️ 危险操作，请谨慎使用")
    
    if st.button("🧹 清理临时文件"):
        # 清理临时上传文件
        temp_path = "temp_uploads"
        if os.path.exists(temp_path):
            for file in os.listdir(temp_path):
                file_path = os.path.join(temp_path, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    st.error(f"清理失败: {e}")
            st.success("✅ 临时文件清理完成")

def cleanup_user_data(username: str):
    """清理用户数据"""
    # 清理用户知识库
    user_kb_path = f"vector_db_storage/{username}"
    if os.path.exists(user_kb_path):
        shutil.rmtree(user_kb_path)
    
    # 清理用户对话历史
    user_chat_path = f"chat_histories/{username}"
    if os.path.exists(user_chat_path):
        shutil.rmtree(user_chat_path)
