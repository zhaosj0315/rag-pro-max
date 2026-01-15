import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 数字化指挥中心样式表 (v8.0 终极全屏沉浸版) ---
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
                radial-gradient(at 0% 0%, rgba(96, 165, 250, 0.15) 0px, transparent 50%),
                radial-gradient(at 98% 100%, rgba(244, 114, 182, 0.15) 0px, transparent 50%),
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
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
            background: linear-gradient(120deg, #fff 30%, #94a3b8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 1rem;
            line-height: 1.1;
        }
        .hero-subtitle {
            font-size: 1.5rem;
            color: #94a3b8;
            font-weight: 400;
            margin-bottom: 3rem;
            max-width: 600px;
            line-height: 1.6;
        }
        
        /* 核心能力：横向统计形态 */
        .stats-row {
            display: flex;
            gap: 2rem;
            margin-bottom: 3rem;
        }
        .stat-item {
            border-left: 3px solid #3b82f6;
            padding-left: 1rem;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: 700;
            color: #fff;
            display: block;
        }
        .stat-label {
            font-size: 0.9rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* --- 右侧：登录控制台 --- */
        .login-panel {
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 24px;
            padding: 3rem;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }
        
        /* 输入框极简风格 */
        .stTextInput input {
            background-color: rgba(15, 23, 42, 0.8) !important;
            border: 1px solid rgba(51, 65, 85, 1) !important;
            color: white !important;
            height: 3.5rem; /* 更高的输入框 */
            font-size: 1.1rem;
            border-radius: 12px !important;
            transition: all 0.3s ease;
        }
        .stTextInput input:focus {
            border-color: #60a5fa !important;
            box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.2);
        }
        
        /* 按钮大气风格 */
        button[kind="primary"] {
            height: 3.5rem;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            border-radius: 12px !important;
            background: linear-gradient(to right, #2563eb, #4f46e5) !important;
            border: none !important;
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
        }
        button[kind="secondary"] {
            border: 1px solid rgba(255,255,255,0.1) !important;
            color: #94a3b8 !important;
            background: transparent !important;
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
            color: #64748b;
            font-size: 1.1rem;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #fff;
            border-bottom: 2px solid #60a5fa !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # 布局：左6 右4，中间留白
    col_left, col_spacer, col_right = st.columns([1.4, 0.3, 1])

    # --- 左侧：宏大叙事 ---
    with col_left:
        st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True) # 顶部弹性留白
        
        # 品牌
        st.markdown('<div class="hero-title">RAG Pro Max</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">企业级认知中台。深度融合全模态解析、专家级 SQL 推演与即时决策智能，重塑数据价值。</div>', unsafe_allow_html=True)
        
        # 核心指标（横向排布，打破列表感）
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

        # 底部快捷状态（左侧底部）
        st.markdown("""
        <div style="margin-top: 4rem; display: flex; gap: 15px;">
            <div style="background: rgba(255,255,255,0.05); padding: 10px 20px; border-radius: 50px; font-size: 0.8rem; color: #94a3b8; border: 1px solid rgba(255,255,255,0.1);">
                🟢 System Ready
            </div>
            <div style="background: rgba(255,255,255,0.05); padding: 10px 20px; border-radius: 50px; font-size: 0.8rem; color: #94a3b8; border: 1px solid rgba(255,255,255,0.1);">
                ⚡ Metal Acceleration
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 右侧：沉浸式登录面板 ---
    with col_right:
        st.markdown('<div style="height: 5vh;"></div>', unsafe_allow_html=True) # 顶部对齐微调
        
        # 使用卡片样式包裹
        with st.container(): # 这里的 container 实际上是被 CSS .block-container 控制的，我们用 markdown 模拟 panel
            # 由于 Streamlit 限制，我们无法直接给 container 加 class，
            # 但我们可以通过在内部放入 html div wrapper 或者利用上面的 CSS 选择器。
            # 这里利用 CSS 选择器 [data-testid="column"]:nth-child(3) 可能会更精准，但为了稳健，
            # 我们直接渲染表单， relying on the removal of the specific border container to let CSS handle inputs.
            # 实际上，为了实现 "Login Panel" 效果，我们可以手动写一个 div wrapper start
            
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
            
            st.markdown('</div>', unsafe_allow_html=True) # End login-panel

    # --- 底部版权 ---
    st.markdown(f"""
    <div style="position: fixed; bottom: 2rem; left: 0; width: 100%; text-align: center; color: rgba(255,255,255,0.2); font-size: 0.7rem; font-family: monospace; pointer-events: none;">
        RAG PRO MAX ENTERPRISE EDITION v6.6.0 &copy; 2026
    </div>
    """, unsafe_allow_html=True)
