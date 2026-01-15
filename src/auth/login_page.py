import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 数字化指挥中心样式表 (v8.1 高对比度防反光版) ---
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

        /* --- 左侧：品牌展示区 --- */
        .hero-title {
            font-size: 5rem; /* 极大字号 */
            font-weight: 900;
            letter-spacing: -2px;
            /* 提亮标题：纯白为主 */
            background: linear-gradient(120deg, #ffffff 40%, #cbd5e1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            line-height: 1.1;
            text-shadow: 0 0 30px rgba(255,255,255,0.1);
        }
        .hero-subtitle {
            font-size: 1.5rem;
            /* 提亮副标题：从 #94a3b8 提升至 #e2e8f0 (Slate-200) */
            color: #e2e8f0; 
            font-weight: 400;
            margin-bottom: 3rem;
            max-width: 650px;
            line-height: 1.6;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3); /* 增加阴影抗反光 */
        }
        
        /* 核心能力：横向统计形态 */
        .stats-row {
            display: flex;
            gap: 2rem;
            margin-bottom: 3rem;
        }
        .stat-item {
            border-left: 3px solid #60a5fa; /* 提亮边框色 */
            padding-left: 1rem;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #ffffff; /* 纯白 */
            display: block;
            text-shadow: 0 0 10px rgba(96, 165, 250, 0.3);
        }
        .stat-label {
            font-size: 0.95rem;
            /* 提亮标签：从深灰改为浅灰白 */
            color: #cbd5e1; 
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 500;
        }

        /* --- 右侧：登录控制台 --- */
        .login-panel {
            background: rgba(30, 41, 59, 0.6); /* 降低不透明度，增加通透感 */
            backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.15); /* 增强边框可见性 */
            border-radius: 24px;
            padding: 3rem;
            box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.6);
        }
        
        /* 输入框高对比度优化 */
        .stTextInput input {
            /* 背景提亮：从深色改为半透明白 */
            background-color: rgba(255, 255, 255, 0.08) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            color: #ffffff !important;
            height: 3.5rem; 
            font-size: 1.1rem;
            border-radius: 12px !important;
            transition: all 0.3s ease;
        }
        /* 修复 Placeholder 看不清的问题 */
        .stTextInput input::placeholder {
            color: rgba(255, 255, 255, 0.6) !important; /* 60% 白，显著提升可见度 */
            font-weight: 400;
        }
        .stTextInput input:focus {
            border-color: #60a5fa !important;
            background-color: rgba(255, 255, 255, 0.15) !important;
            box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.3);
        }
        
        /* 按钮大气风格 */
        button[kind="primary"] {
            height: 3.5rem;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            background: linear-gradient(to right, #3b82f6, #6366f1) !important; /* 更亮的蓝 */
            border: none !important;
            box-shadow: 0 10px 20px -5px rgba(59, 130, 246, 0.4);
            color: white !important;
        }
        button[kind="secondary"] {
            border: 1px solid rgba(255,255,255,0.3) !important; /* 增强边框 */
            color: #e2e8f0 !important; /* 提亮文字 */
            background: transparent !important;
        }
        button[kind="secondary"]:hover {
            border-color: #fff !important;
            color: #fff !important;
        }

        /* Tabs 优化 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
            margin-bottom: 2rem;
            background: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: auto;
            padding: 0 0 10px 0;
            background: transparent !important;
            border: none !important;
            color: #94a3b8; /* 未选中状态提亮 */
            font-size: 1.1rem;
            font-weight: 500;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #fff;
            border-bottom: 2px solid #60a5fa !important;
            text-shadow: 0 0 10px rgba(96, 165, 250, 0.5);
        }
        
        /* 底部状态胶囊：高亮版 */
        .status-capsule {
            background: rgba(255,255,255,0.1);
            padding: 8px 16px;
            border-radius: 50px;
            font-size: 0.85rem;
            color: #e2e8f0; /* 提亮 */
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

    # --- 左侧：宏大叙事 ---
    with col_left:
        st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True) 
        
        # 品牌
        st.markdown('<div class="hero-title">RAG Pro Max</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">企业级认知中台。深度融合全模态解析、专家级 SQL 推演与即时决策智能，重塑数据价值。</div>', unsafe_allow_html=True)
        
        # 核心指标
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

        # 底部快捷状态（左侧底部）- 使用新的高亮胶囊样式
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

    # --- 右侧：沉浸式登录面板 ---
    with col_right:
        st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True) 
        
        with st.container():
            st.markdown('<div class="login-panel">', unsafe_allow_html=True)
            
            tab_login, tab_register = st.tabs(["Access Login", "Create Account"])
            
            with tab_login:
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
                with st.form("login_form"):
                    u = st.text_input("Username", placeholder="Enter your ID", label_visibility="visible")
                    p = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="visible")
                    
                    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
                    
                    if st.form_submit_button("Launch Command Center", use_container_width=True, type="primary"):
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
                if st.button("Guest Access (Read Only)", use_container_width=True, type="secondary"):
                    st.session_state.logged_in = True
                    st.session_state.user = "guest_user"; st.session_state.role = "guest"; st.rerun()

            with tab_register:
                st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
                with st.form("reg_form"):
                    nu = st.text_input("New Username", placeholder="Choose an ID", label_visibility="visible")
                    np = st.text_input("New Password", type="password", placeholder="Set a password", label_visibility="visible")
                    st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
                    if st.form_submit_button("Register Account", use_container_width=True, type="primary"):
                        if nu and np:
                            success, msg = register_user(nu, np)
                            if success:
                                from src.auth.audit_logger import AuditLogger
                                from src.common.utils import get_client_ip
                                AuditLogger.log(nu, "REGISTER", "注册成功", action_type="AUTH", ip=get_client_ip())
                                st.success("✅ Account Created")
                            else: st.error(f"❌ {msg}")
            
            st.markdown('</div>', unsafe_allow_html=True) 

    # --- 底部版权（提亮） ---
    st.markdown(f"""
    <div style="position: fixed; bottom: 2rem; left: 0; width: 100%; text-align: center; color: rgba(255,255,255,0.5); font-size: 0.75rem; font-family: monospace; pointer-events: none; letter-spacing: 1px;">
        RAG PRO MAX ENTERPRISE EDITION v6.6.0 &copy; 2026
    </div>
    """, unsafe_allow_html=True)