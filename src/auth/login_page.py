import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 数字化指挥中心样式表 (v7.8 均衡大气版) ---
    st.markdown("""
        <style>
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
            height: 100vh !important;
        }
        .stApp {
            background: radial-gradient(circle at 50% 50%, #1e1b4b 0%, #020617 100%) !important;
        }
        .brand-header {
            font-size: 3.2rem; /* 恢复大气字号 */
            font-weight: 900;
            background: linear-gradient(135deg, #60a5fa 0%, #f472b6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: -1.5rem; 
            margin-bottom: 0.5rem;
            letter-spacing: -1px;
        }
        .intro-text {
            font-size: 1.1rem;
            color: #94a3b8;
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }
        .feature-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            transition: all 0.3s ease;
        }
        .feature-card:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: rgba(96, 165, 250, 0.3);
            transform: translateX(5px);
        }
        .feature-icon {
            font-size: 1.5rem;
            margin-right: 12px;
            background: rgba(96, 165, 250, 0.1);
            width: 40px;
            height: 40px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .feature-content b {
            color: #e2e8f0;
            font-size: 0.95rem;
            display: block;
            margin-bottom: 2px;
        }
        .feature-content span {
            color: #64748b;
            font-size: 0.8rem;
        }
        .block-container {
            padding-top: 2rem !important; /* 再上移一点，从容不迫 */
            padding-bottom: 0rem !important;
            max-width: 95% !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
        }
        /* 登录框样式优化 */
        [data-testid="stVerticalBlock"] > div:has(div[style*="border"]) {
            padding: 2.5rem !important;
            border-radius: 24px !important;
            background: rgba(15, 23, 42, 0.6) !important;
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
            margin-top: 1rem; /* 保持与左侧视觉齐平 */
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            margin-bottom: 1rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 3rem;
            padding: 0 1.5rem;
            font-size: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    from datetime import datetime
    now = datetime.now()
    greeting = "🚀 智慧中台 · 全速进化" if 5 <= now.hour < 18 else "🌙 深夜备战 · 永不熄灯"

    col_brand, col_space, col_auth = st.columns([1.2, 0.2, 1]) 

    with col_brand:
        st.markdown(f"<h1 class='brand-header'>RAG Pro Max</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #60a5fa; font-weight: 600; margin-bottom: 1.5rem; font-size:1rem; display:flex; align-items:center;'><span style='margin-right:8px'></span>{greeting}</p>", unsafe_allow_html=True)
        
        # --- [v7.8] 卡片式指引 ---
        steps = [
            ("📁 投喂素材", "左侧工具栏上传 PDF/CSV 或抓取网页"),
            ("⚙️ 模式选径", "切换标准对话或数据分析，精准匹配需求"),
            ("💡 洞察产出", "提问即获镜像报告与中英双语结论")
        ]
        
        for icon_title, desc in steps:
            icon, title = icon_title.split(" ")
            st.markdown(f"""
            <div class='feature-card'>
                <div class='feature-icon'>{icon}</div>
                <div class='feature-content'>
                    <b>{title}</b>
                    <span>{desc}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # --- [v7.8] 核心能力速览 (微调间距) ---
        st.markdown("""
        <div style='display: flex; gap: 12px; margin-top: 1rem;'>
            <div style='flex: 1; background: rgba(16,185,129,0.05); border: 1px solid rgba(16,185,129,0.2); padding: 10px; border-radius: 10px; text-align: center;'>
                <div style='color: #10b981; font-weight: bold; font-size: 0.9rem; margin-bottom: 2px;'>📄 文档检索</div>
                <div style='color: #64748b; font-size: 0.7rem;'>海量知识 毫秒召回</div>
            </div>
            <div style='flex: 1; background: rgba(96,165,250,0.05); border: 1px solid rgba(96,165,250,0.2); padding: 10px; border-radius: 10px; text-align: center;'>
                <div style='color: #60a5fa; font-weight: bold; font-size: 0.9rem; margin-bottom: 2px;'>📊 数据推演</div>
                <div style='color: #64748b; font-size: 0.7rem;'>业务逻辑 深度洞察</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-top: 1.5rem; color: #475569; font-size: 0.75rem; font-family: monospace; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 15px; display: flex; justify-content: space-between; align-items: center;">
            <span>STATUS: <span style="color:#10b981">● READY</span></span>
            <span>ACCELERATION: <span style="color:#60a5fa">METAL</span></span>
            <span>v6.6.0</span>
        </div>
        """, unsafe_allow_html=True)

    with col_auth:
        tab_login, tab_register = st.tabs(["🔐 登录", "✨ 注册"])
        with tab_login:
            with st.container(border=True):
                with st.form("login_form"):
                    u = st.text_input("User", placeholder="用户名", label_visibility="collapsed")
                    p = st.text_input("Pass", type="password", placeholder="密码", label_visibility="collapsed")
                    if st.form_submit_button("进入指挥中心", use_container_width=True, type="primary"):
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
                if st.button("🚪 游客模式", use_container_width=True):
                    st.session_state.logged_in = True
                    st.session_state.user = "guest_user"; st.session_state.role = "guest"; st.rerun()

        with tab_register:
            with st.container(border=True):
                with st.form("reg_form"):
                    nu = st.text_input("New User", placeholder="新账号", label_visibility="collapsed")
                    np = st.text_input("New Pass", type="password", placeholder="新密码", label_visibility="collapsed")
                    if st.form_submit_button("提交注册", use_container_width=True, type="primary"):
                        if nu and np:
                            success, msg = register_user(nu, np)
                            if success:
                                from src.auth.audit_logger import AuditLogger
                                from src.common.utils import get_client_ip
                                AuditLogger.log(nu, "REGISTER", "注册成功", action_type="AUTH", ip=get_client_ip())
                                st.success("✅ 注册成功！")
                            else: st.error(f"❌ {msg}")
