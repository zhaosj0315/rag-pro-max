import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 数字化指挥中心样式表 (v8.5 重心上提重构版) ---
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

        /* 布局容器调整：大幅减少顶部留白，解决“掉底”问题 */
        .block-container {
            padding-top: 2rem !important; /* 从 10vh 减到 2rem，强制上提 */
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
            /* 确保与右侧标题视觉对齐 */
            margin-top: 1rem; 
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

        /* --- 右侧：登录控制台 (v8.5 废墟清理版) --- */
        .login-panel {
            background: rgba(15, 23, 42, 0.85); /* 加深背景，突出前景 */
            backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 24px;
            padding: 3rem 3rem 2.5rem 3rem; /* 调整内边距，底部收紧 */
            box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.8);
            position: relative;
            margin-top: 0; /* 移除顶部额外间距，直接顶上去 */
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background-color: #4ade80;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
            box-shadow: 0 0 8px #4ade80;
        }
        
        /* 输入框 */
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
        
        /* Label */
        .stTextInput label p {
            color: #ffffff !important;
            font-size: 1rem !important;
            font-weight: 700 !important;
            margin-bottom: 0.5rem;
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab"] {
            color: #cbd5e1 !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            padding-bottom: 12px !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #ffffff !important;
            border-bottom: 3px solid #3b82f6 !important;
        }

        /* 按钮：区分主次 */
        button[kind="primary"] {
            height: 3.5rem;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            background: #3b82f6 !important; 
            box-shadow: 0 10px 20px -5px rgba(59, 130, 246, 0.5) !important;
            margin-top: 0.5rem;
        }
        /* 幽灵按钮 (Ghost Button) */
        button[kind="secondary"] {
            height: 3rem;
            border: 1px solid rgba(255,255,255,0.3) !important;
            color: #cbd5e1 !important;
            background: transparent !important;
            font-weight: 500 !important;
            margin-top: 0.5rem;
        }
        button[kind="secondary"]:hover {
            border-color: #fff !important;
            color: #fff !important;
            background: rgba(255,255,255,0.05) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    from datetime import datetime
    now = datetime.now()
    greeting = "🚀 智慧中台 · 全速进化" if 5 <= now.hour < 18 else "🌙 深夜备战 · 永不熄灯"

    col_left, col_spacer, col_right = st.columns([1.4, 0.3, 1])

    with col_left:
        # 品牌
        st.markdown('<div class="hero-title">RAG Pro Max</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#60a5fa; font-weight:700; margin-bottom:1rem; font-size:1.1rem;">{greeting}</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">企业级认知中台。深度融合全模态解析、专家级 SQL 推演与即时决策智能，重塑数据价值。</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="stats-row">
            <div class="stat-item">
                <span class="stat-value">多模态解析</span>
                <span class="stat-label">Multi-Modal</span>
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
        # 移除了所有顶部占位符 div，让面板自然上浮
        
        st.markdown('<div class="login-panel">', unsafe_allow_html=True)
        
        # 标题区：紧凑设计
        st.markdown("""
        <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <h1 style='color:white; margin:0; font-size:2rem; font-weight:800; letter-spacing:0.5px;'>指挥中心</h1>
                <div style="display:flex; align-items:center; background:rgba(74,222,128,0.1); padding:4px 10px; border-radius:20px; border:1px solid rgba(74,222,128,0.3);">
                    <div class="status-dot"></div>
                    <span style="color:#4ade80; font-size:0.7rem; font-weight:700; letter-spacing:0.5px;">在线</span>
                </div>
            </div>
            <div style="color:#94a3b8; font-size:0.85rem; letter-spacing:1px; margin-top:6px; font-weight:500;">安全接入终端 v6.6.0</div>
        </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["账号登录", "注册账号"])
        
        with tab_login:
            with st.form("login_form"):
                u = st.text_input("用户名", placeholder="请输入用户名", label_visibility="visible")
                p = st.text_input("密码", type="password", placeholder="请输入密码", label_visibility="visible")
                
                st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
                
                if st.form_submit_button("启动指挥系统", use_container_width=True, type="primary"):
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
            
            # 幽灵按钮重构
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            if st.button("访客模式 (仅预览)", use_container_width=True, type="secondary"):
                st.session_state.logged_in = True
                st.session_state.user = "guest_user"; st.session_state.role = "guest"; st.rerun()

        with tab_register:
            with st.form("reg_form"):
                nu = st.text_input("新用户名", placeholder="设置您的登录 ID", label_visibility="visible")
                np = st.text_input("新密码", type="password", placeholder="设置安全密码", label_visibility="visible")
                st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
                if st.form_submit_button("初始化账号", use_container_width=True, type="primary"):
                    if nu and np:
                        success, msg = register_user(nu, np)
                        if success:
                            from src.auth.audit_logger import AuditLogger
                            from src.common.utils import get_client_ip
                            AuditLogger.log(nu, "REGISTER", "注册成功", action_type="AUTH", ip=get_client_ip())
                            st.success("✅ 注册成功！请切换至登录页")
                        else: st.error(f"❌ {msg}")
        
        st.markdown('</div>', unsafe_allow_html=True) 

    # --- [v7.9] 全局状态页脚：全屏居中 (固定于底部) ---
    st.markdown(f"""
    <div style="position: fixed; bottom: 2rem; left: 0; width: 100%; color: #475569; font-size: 0.75rem; font-family: monospace; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 20px; display: flex; justify-content: center; gap: 60px; align-items: center; z-index: 100;">
        <span>系统状态: <span style="color:#10b981">● 就绪</span></span>
        <span>硬件加速: <span style="color:#60a5fa">苹果芯片加速</span></span>
        <span>版本 v6.6.0</span>
    </div>
    """, unsafe_allow_html=True)