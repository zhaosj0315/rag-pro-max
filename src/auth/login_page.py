import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 数字化指挥中心样式表 (v8.4 终极标题重构版) ---
    st.markdown("""
        <style>
        /* 全局容器设定 */
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
            height: 100vh !important;
            font-family: 'Inter', sans-serif;
        }
        
        /* 核心背景 */
        .stApp {
            background-color: #0f172a;
            background-image: 
                radial-gradient(at 0% 0%, rgba(96, 165, 250, 0.2) 0px, transparent 50%),
                radial-gradient(at 98% 100%, rgba(244, 114, 182, 0.2) 0px, transparent 50%),
                linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
        }

        .block-container {
            padding-top: 10vh !important;
            padding-bottom: 0rem !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
            max-width: 100% !important;
        }

        /* --- 左侧品牌区 --- */
        .hero-title {
            font-size: 5rem;
            font-weight: 900;
            letter-spacing: -2px;
            color: #ffffff !important; 
            margin-bottom: 1rem;
            line-height: 1.1;
            text-shadow: 0 0 40px rgba(59, 130, 246, 0.5);
        }
        .hero-subtitle {
            font-size: 1.5rem;
            color: #f1f5f9;
            font-weight: 400;
            margin-bottom: 3rem;
            max-width: 650px;
            line-height: 1.6;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #ffffff;
            display: block;
        }
        .stat-label {
            font-size: 0.95rem;
            color: #e2e8f0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* --- 右侧：登录控制台 (v8.4 优化版) --- */
        .login-panel {
            background: rgba(15, 23, 42, 0.8);
            backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 24px;
            padding: 2.5rem 3rem 3rem 3rem; /* 调整顶部内边距 */
            box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.8);
            position: relative; /* 为呼吸灯定位 */
        }
        
        /* 呼吸灯效果 */
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(74, 222, 128, 0); }
            100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
        }
        .status-dot {
            width: 10px;
            height: 10px;
            background-color: #4ade80;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            animation: pulse-green 2s infinite;
        }
        
        /* 1. 输入框 */
        .stTextInput input {
            background-color: #f8fafc !important;
            border: 2px solid #cbd5e1 !important;
            color: #000000 !important;
            height: 3.5rem; 
            font-size: 1.1rem;
            border-radius: 10px !important;
        }
        .stTextInput input::placeholder {
            color: #475569 !important;
            opacity: 1 !important;
        }
        
        /* 2. Label */
        .stTextInput label p {
            color: #ffffff !important;
            font-size: 1.05rem !important;
            font-weight: 700 !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }
        
        /* 3. Tabs */
        .stTabs [data-baseweb="tab"] {
            color: #cbd5e1 !important;
            font-size: 1.2rem !important;
            font-weight: 600 !important;
            padding-bottom: 12px !important;
        }
        .stTabs [data-baseweb="tab"]:hover {
            color: #ffffff !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            border-bottom: 3px solid #3b82f6 !important;
        }

        /* 按钮 */
        button[kind="primary"] {
            height: 3.8rem;
            font-size: 1.2rem !important;
            font-weight: 800 !important;
            background: #3b82f6 !important; 
            box-shadow: 0 10px 20px -5px rgba(59, 130, 246, 0.5) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    from datetime import datetime
    now = datetime.now()
    greeting = "🚀 智慧中台 · 全速进化" if 5 <= now.hour < 18 else "🌙 深夜备战 · 永不熄灯"

    col_left, col_spacer, col_right = st.columns([1.4, 0.3, 1])

    with col_left:
        st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True) 
        st.markdown('<div class="hero-title">RAG Pro Max</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#60a5fa; font-weight:700; margin-bottom:1rem; font-size:1.1rem;">{greeting}</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">企业级认知中台。深度融合全模态解析、专家级 SQL 推演与即时决策智能，重塑数据价值。</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="stats-row">
            <div class="stat-item">
                <span class="stat-value">Multi-Modal</span>
                <span class="stat-label">全模态解析</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">Deep Think</span>
                <span class="stat-label">深度思考链</span>
            </div>
            <div class="stat-item">
                <span class="stat-value">Analyst Agent</span>
                <span class="stat-label">数据智能体</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True) 
        
        st.markdown('<div class="login-panel">', unsafe_allow_html=True)
        
        # 1. 标题区重构：名副其实的“门头”
        st.markdown("""
        <div style="margin-bottom: 2rem;">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <h1 style='color:white; margin:0; font-size:2.2rem; font-weight:800; letter-spacing:1px; line-height:1.2;'>Command Center</h1>
                <div style="display:flex; align-items:center; background:rgba(74,222,128,0.1); padding:4px 8px; border-radius:12px; border:1px solid rgba(74,222,128,0.3);">
                    <div class="status-dot"></div>
                    <span style="color:#4ade80; font-size:0.7rem; font-weight:700; letter-spacing:0.5px;">ONLINE</span>
                </div>
            </div>
            <div style="color:#94a3b8; font-size:0.9rem; letter-spacing:1px; margin-top:4px; font-weight:500;">SECURE ACCESS TERMINAL</div>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["Access Login", "Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                u = st.text_input("Username", placeholder="Enter your ID", label_visibility="visible")
                p = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="visible")
                
                st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
                
                if st.form_submit_button("Launch Command System", use_container_width=True, type="primary"):
                    if u and p:
                        from src.auth.audit_logger import AuditLogger
                        from src.common.utils import get_client_ip
                        success, info = authenticate_user(u, p)
                        if success:
                            from src.auth.session_manager import create_session
                            token, days = create_session(u)
                            st.query_params["session_token"] = token
                            st.session_state.logged_in = True
                            st.session_state.user = u
                            st.session_state.role = info.get('role', 'standard_user')
                            AuditLogger.log(u, "LOGIN", "登录成功", ip=get_client_ip())
                            st.rerun()
                        else:
                            st.error(f"❌ {info}")
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            if st.button("Guest Mode (Read Only)", use_container_width=True, type="secondary"):
                st.session_state.logged_in = True
                st.session_state.user = "guest_user"; st.session_state.role = "guest"; st.rerun()

        with tab_register:
            with st.form("reg_form"):
                nu = st.text_input("New Username", placeholder="Create your ID", label_visibility="visible")
                np = st.text_input("New Password", type="password", placeholder="Set secure password", label_visibility="visible")
                st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
                if st.form_submit_button("Initialize Account", use_container_width=True, type="primary"):
                    if nu and np:
                        success, msg = register_user(nu, np)
                        if success:
                            from src.auth.audit_logger import AuditLogger
                            from src.common.utils import get_client_ip
                            AuditLogger.log(nu, "REGISTER", "注册成功", action_type="AUTH", ip=get_client_ip())
                            st.success("✅ Success! Please Login")
                        else: st.error(f"❌ {msg}")
        
        st.markdown('</div>', unsafe_allow_html=True) 

    # --- 底部版权 ---
    st.markdown(f"""
    <div style="position: fixed; bottom: 2rem; left: 0; width: 100%; text-align: center; color: rgba(255,255,255,0.4); font-size: 0.75rem; font-family: monospace; pointer-events: none;">
        RAG PRO MAX ENTERPRISE EDITION v6.6.0 &copy; 2026 | ALL SYSTEMS OPERATIONAL
    </div>
    """, unsafe_allow_html=True)
