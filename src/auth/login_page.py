#!/usr/bin/env python3
"""
登录界面组件
"""

import streamlit as st
from src.auth.user_auth import user_auth

def show_login_page():
    """显示登录页面"""
    st.set_page_config(
        page_title="RAG Pro Max - 登录",
        page_icon="🚀",
        layout="centered"
    )
    
    # 页面样式
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .login-title {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 登录表单
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        st.markdown('<h1 class="login-title">🚀 RAG Pro Max</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #666;">请登录以继续使用</p>', unsafe_allow_html=True)
        
        # 登录表单
        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button("🔑 登录", use_container_width=True)
            with col2:
                register_btn = st.form_submit_button("📝 注册", use_container_width=True)
        
        # 处理登录
        if login_btn:
            if username and password:
                success, result = user_auth.authenticate(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_info = result
                    st.success(f"✅ 登录成功！欢迎 {result['username']}")
                    st.rerun()
                else:
                    if isinstance(result, dict) and result.get('error') == 'password_reset_required':
                        st.error("🔐 " + result['message'])
                        st.code("python scripts/reset_admin_password.py")
                    else:
                        st.error("❌ 用户名或密码错误")
            else:
                st.error("❌ 请输入用户名和密码")
        
        # 处理注册
        if register_btn:
            if username and password:
                if len(password) < 6:
                    st.error("❌ 密码长度至少6位")
                elif user_auth.register_user(username, password):
                    st.success(f"✅ 注册成功！请使用 {username} 登录")
                else:
                    st.error("❌ 用户名已存在")
            else:
                st.error("❌ 请输入用户名和密码")
        
        # 游客登录
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👤 游客登录", use_container_width=True):
                guest_info = user_auth.create_guest_session()
                st.session_state.authenticated = True
                st.session_state.user_info = guest_info
                st.success(f"✅ 游客登录成功！")
                st.rerun()
        with col2:
            st.info("💡 游客模式数据临时保存")
        
        st.markdown('</div>', unsafe_allow_html=True)

def check_authentication():
    """检查用户认证状态"""
    if not st.session_state.get('authenticated', False):
        show_login_page()
        st.stop()
    
    # 设置用户上下文
    if 'user_context' not in st.session_state:
        user_info = st.session_state.user_info
        st.session_state.user_context = {
            'username': user_info['username'],
            'role': user_info['role'],
            'is_admin': user_info['role'] == 'admin'
        }

def logout():
    """用户登出"""
    for key in ['authenticated', 'user_info', 'user_context']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
