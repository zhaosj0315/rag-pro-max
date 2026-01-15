import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 数字化指挥中心样式表 (v8.2 高对比度手术版) ---
    st.markdown("""
        <style>
        /* 全局容器设定 */
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
            height: 100vh !important;
            font-family: 'Inter', sans-serif;
        }
        
        /* 核心背景：深空 + 科技网格 + 动态光晕 */
        .stApp {
            background-color: #0f172a;
            background-image: 
                radial-gradient(at 0% 0%, rgba(96, 165, 250, 0.18) 0px, transparent 50%),
                radial-gradient(at 98% 100%, rgba(244, 114, 182, 0.18) 0px, transparent 50%),
                linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
            background-position: 0 0, 0 0, -1px -1px, -1px -1px;
        }

        /* 布局容器调整：左右分栏，撑满屏幕 */
        .block-container {
            padding-top: 10vh !important;
            padding-bottom: 0rem !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
            max-width: 100% !important;
        }

        /* --- 左侧：品牌展示区 (保持高亮) --- */
        .hero-title {
            font-size: 5rem;
            font-weight: 900;
            letter-spacing: -2px;
            background: linear-gradient(120deg, #ffffff 40%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            line-height: 1.1;
            text-shadow: 0 0 30px rgba(255,255,255,0.1);
        }
        .hero-subtitle {
            font-size: 1.5rem;
            color: #e2e8f0; 
            font-weight: 400;
            margin-bottom: 3rem;
            max-width: 650px;
            line-height: 1.6;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .stats-row {
            display: flex;
            gap: 2rem;
            margin-bottom: 3rem;
        }
        .stat-item {
            border-left: 3px solid #60a5fa;
            padding-left: 1rem;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #ffffff;
            display: block;
            text-shadow: 0 0 10px rgba(96, 165, 250, 0.3);
        }
        .stat-label {
            font-size: 0.95rem;
            color: #cbd5e1; 
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }

        /* --- 右侧：登录控制台 (高对比度重构) --- */
        .login-panel {
            background: rgba(15, 23, 42, 0.85); /* 加深背景，突出前景内容 */
            backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 24px;
            padding: 3rem;
            box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.8);
        }
        
        /* 1. 输入框外科手术：纯白背景 + 纯黑文字 */
        .stTextInput input {
            background-color: #FFFFFF !important; /* 纯白背景 */
            border: 2px solid #e2e8f0 !important;
            color: #000000 !important; /* 纯黑输入字 */
            height: 3.5rem; 
            font-size: 1.1rem;
            border-radius: 8px !important;
            transition: all 0.2s ease;
            caret-color: #2563eb; /* 蓝色光标 */
        }
        
        /* 2. Placeholder 修复：中深灰，拒绝看不见 */
        .stTextInput input::placeholder {
            color: #64748b !important; /* Slate-500 中灰色 */
            opacity: 1 !important; /* 强制不透明 */
            font-weight: 500;
        }
        
        .stTextInput input:focus {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.3);
        }
        
        /* 3. Label 标签提亮：纯白粗体 */
        .stTextInput label p {
            color: #ffffff !important;
            font-size: 1rem !important;
            font-weight: 600 !important;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
        }
        
        /* 按钮风格 */
        button[kind="primary"] {
            height: 3.5rem;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            background: #3b82f6 !important; /* 纯色亮蓝，对比度更高 */
            border: none !important;
            color: white !important;
            margin-top: 1rem;
        }
        button[kind="primary"]:hover {
            background: #2563eb !important;
        }
        button[kind="secondary"] {
            border: 1px solid rgba(255,255,255,0.4) !important;
            color: #ffffff !important;
            background: transparent !important;
            font-weight: 500 !important;
        }

        /* Tabs 优化 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            margin-bottom: 1.5rem;
            background: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: auto;
            padding: 0 0 10px 0;
            background: transparent !important;
            border: none !important;
            color: #94a3b8;
            font-size: 1.2rem;
            font-weight: 600;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #fff;
            border-bottom: 3px solid #3b82f6 !important;
        }
        
        /* 底部状态胶囊 */
        .status-capsule {
            background: rgba(255,255,255,0.1);
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 0.85rem;
            color: #e2e8f0; 
            border: 1px solid rgba(255,255,255,0.2);
            display: flex;
            align-items: center;
            gap: 8px;
            backdrop-filter: blur(4px);
        }
        </style>
    """, unsafe_allow_html=True)

    # 布局：左6 右4，中间留白
    col_left, col_spacer, col_right = st.columns([1.4, 0.3, 1])

    # --- 左侧：品牌区 ---
    with col_left:
        st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True) 
        
        st.markdown('<div class="hero-title">RAG Pro Max</div>', unsafe_allow_html=True)
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

        st.markdown("""
        <div style="margin-top: 4rem; display: flex; gap: 15px;">
            <div class="status-capsule">
                <span style="color:#4ade80">●</span> System Ready
            </div>
            <div class="status-capsule">
                <span style="color:#60a5fa">⚡</span> Metal Acceleration
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 右侧：登录控制台 ---
    with col_right:
        st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True) 
        
        with st.container():
            st.markdown('<div class="login-panel">', unsafe_allow_html=True)
            
            # 4. 消灭神秘黑框：添加显式标题
            st.markdown("""
            <h2 style='color:white; margin:0 0 1.5rem 0; font-size:1.8rem;'>Command Center</h2>
            """, unsafe_allow_html=True)
            
            tab_login, tab_register = st.tabs(["Access Login", "Create Account"])
            
            with tab_login:
                with st.form("login_form"):
                    # 使用 visible label，配合 CSS 提亮
                    u = st.text_input("Username", placeholder="Enter your ID", label_visibility="visible")
                    p = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="visible")
                    
                    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
                    
                    if st.form_submit_button("Launch System", use_container_width=True, type="primary"):
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
                
                st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                if st.button("Guest Access (Read Only)", use_container_width=True, type="secondary"):
                    st.session_state.logged_in = True
                    st.session_state.user = "guest_user"; st.session_state.role = "guest"; st.rerun()

            with tab_register:
                with st.form("reg_form"):
                    nu = st.text_input("New Username", placeholder="Choose an ID", label_visibility="visible")
                    np = st.text_input("New Password", type="password", placeholder="Set a password", label_visibility="visible")
                    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
                    if st.form_submit_button("Create Account", use_container_width=True, type="primary"):
                        if nu and np:
                            success, msg = register_user(nu, np)
                            if success:
                                from src.auth.audit_logger import AuditLogger
                                from src.common.utils import get_client_ip
                                AuditLogger.log(nu, "REGISTER", "注册成功", action_type="AUTH", ip=get_client_ip())
                                st.success("✅ Account Created")
                            else: st.error(f"❌ {msg}")
            
            st.markdown('</div>', unsafe_allow_html=True) 

    # --- 底部版权 ---
    st.markdown(f"""
    <div style="position: fixed; bottom: 2rem; left: 0; width: 100%; text-align: center; color: rgba(255,255,255,0.6); font-size: 0.75rem; font-family: monospace; pointer-events: none; letter-spacing: 1px;">
        RAG PRO MAX ENTERPRISE EDITION v6.6.0 &copy; 2026
    </div>
    """, unsafe_allow_html=True)
