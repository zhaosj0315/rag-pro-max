import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 数字化指挥中心样式表 (Digital Command Center) ---
    st.markdown("""
        <style>
        /* 1. 动态噪点极光背景 - 强制锁定深色 */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stToolbar"] {
            background: radial-gradient(circle at 50% 50%, #1e1b4b 0%, #0f172a 50%, #020617 100%) !important;
            background-attachment: fixed !important;
            background-size: cover !important;
        }
        .stApp::before {
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background-image: url("https://grainy-gradients.vercel.app/noise.svg");
            opacity: 0.05;
            pointer-events: none;
            z-index: 1;
        }

        /* 2. 品牌标题：极致发光 */
        .brand-header {
            font-size: 4.5rem;
            font-weight: 900;
            background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 50%, #f472b6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 20px rgba(167, 139, 250, 0.4));
            margin-bottom: 0rem;
            letter-spacing: -3px;
        }

        /* 3. 系统 HUD 仪表盘 */
        .hud-panel {
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 12px;
            padding: 10px 15px;
            display: flex;
            gap: 20px;
            margin-top: 2rem;
            backdrop-filter: blur(5px);
        }
        .hud-item {
            display: flex;
            flex-direction: column;
        }
        .hud-label { color: #cbd5e1; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1px; }
        .hud-value { color: #60a5fa; font-size: 0.9rem; font-weight: 700; font-family: 'Courier New', monospace; text-shadow: 0 0 8px rgba(96,165,250,0.3); }
        .hud-status { width: 8px; height: 8px; border-radius: 50%; background: #10b981; display: inline-block; margin-right: 5px; box-shadow: 0 0 8px #10b981; }

        /* 4. 引导卡片：交互式深度 */
        .guide-card {
            background: rgba(30, 41, 59, 0.5);
            border-left: 4px solid transparent;
            border-radius: 0 16px 16px 0;
            padding: 1.2rem;
            margin-bottom: 1rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .guide-card:hover {
            background: rgba(30, 41, 59, 0.8);
            border-left-color: #60a5fa;
            transform: translateX(12px);
            box-shadow: -20px 0 40px -20px rgba(59, 130, 246, 0.4);
        }

        /* 5. 登录框：深度玻璃拟态 (极致全天候适配) */
        [data-testid="stVerticalBlock"] > div:has(div[style*="border"]) {
            background: rgba(15, 23, 42, 0.85) !important;
            backdrop-filter: blur(25px) !important;
            border: 1px solid rgba(59, 130, 246, 0.4) !important;
            border-radius: 28px !important;
            box-shadow: 0 40px 100px -15px rgba(0, 0, 0, 0.9) !important;
            padding: 2.5rem !important;
        }

        /* --- 极致对比度文字覆盖 (针对白天模式下黑字看不清的问题) --- */
        
        /* 1. 强制所有文本颜色 */
        [data-testid="stAppViewContainer"] * {
            color: #ffffff !important; /* 基础设为纯白 */
        }

        /* 2. 特别针对标题和子标题 */
        .brand-header, h1, h2, h3 {
            color: #ffffff !important;
            text-shadow: 0 0 20px rgba(96, 165, 250, 0.5) !important;
        }

        /* 3. 特别针对 Streamlit 标签 (Label) - 强制避开白天模式的黑色 */
        .stTextInput label, .stSelectbox label, .stTextArea label, .stCheckbox label {
            color: #60a5fa !important; /* 亮蓝色标签，极其醒目 */
            font-weight: 700 !important;
            text-transform: uppercase !important;
            font-size: 0.8rem !important;
            letter-spacing: 0.5px !important;
        }

        /* 4. 特别针对输入框内部文字 - 强制深色背景防止白底白字 */
        .stTextInput input {
            color: #ffffff !important;
            background-color: rgba(2, 6, 23, 0.8) !important; /* 深蓝色背景 */
            border: 1px solid rgba(59, 130, 246, 0.6) !important;
            border-radius: 8px !important;
        }
        .stTextInput input:focus {
            border-color: #60a5fa !important;
            box-shadow: 0 0 10px rgba(96, 165, 250, 0.4) !important;
            background-color: rgba(2, 6, 23, 1) !important;
        }

        /* 5. 特别针对 Tabs 标签 - 强制避开系统灰色 */
        .stTabs [data-baseweb="tab"] {
            color: #cbd5e1 !important;
        }
        .stTabs [baseweb="tab-list"] {
            gap: 20px !important;
        }
        .stTabs [aria-selected="true"] {
            color: #ffffff !important;
            font-weight: bold !important;
            border-bottom-color: #60a5fa !important;
            background: rgba(59, 130, 246, 0.1) !important;
        }

        /* 6. 特别针对 Caption (说明文字) */
        [data-testid="stCaptionContainer"], .stCaption, small {
            color: #cbd5e1 !important; /* 较亮的银灰色 */
            font-size: 0.85rem !important;
        }

        /* 7. 引导卡片文字增强 */
        .guide-card div {
            color: #ffffff !important;
        }
        .guide-card div:last-child {
            color: #cbd5e1 !important;
        }

        /* 8. 修复按钮文字颜色与背景 */
        .stButton button {
            color: #ffffff !important;
            background: rgba(255, 255, 255, 0.1) !important;
            border: 1px solid rgba(255, 255, 255, 0.2) !important;
            transition: all 0.3s ease !important;
        }
        .stButton button:hover {
            border-color: #60a5fa !important;
            background: rgba(96, 165, 250, 0.2) !important;
            box-shadow: 0 0 15px rgba(96, 165, 250, 0.3) !important;
        }
        .stButton button p {
            color: #ffffff !important;
        }

        /* 9. 输入框占位符颜色 */
        ::placeholder {
            color: rgba(255, 255, 255, 0.4) !important;
        }

        /* 6. 激励语录 */
        .quote-box {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.05);
            font-style: italic;
            color: #cbd5e1;
            font-size: 0.9rem;
            border: 1px dashed rgba(255,255,255,0.2);
            line-height: 1.6;
        }

        /* 知识神经元动画 */
        @keyframes pulse-brain {
            0% { transform: scale(1); opacity: 0.3; }
            50% { transform: scale(1.05); opacity: 0.6; }
            100% { transform: scale(1); opacity: 0.3; }
        }
        .brain-svg {
            position: absolute;
            top: -100px; right: -50px;
            z-index: -1;
            animation: pulse-brain 8s ease-in-out infinite;
            filter: blur(2px);
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. 动态逻辑：日期感应与语录 ---
    from datetime import datetime
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour
    
    # 动态语录池
    if weekday == 0: # 周一
        quotes = [
            "“新的一周，从将繁琐交给 AI 开始。”",
            "“智慧的本质是减轻大脑的负担，而非增加它的负荷。”",
            "“周一的深夜是为明天的闪耀蓄力。”"
        ]
    else:
        quotes = [
            "“数据本身没有价值，直到它变成了洞察。”",
            "“本地化部署，是对数据主权最高级别的尊重。”",
            "“在 RAG Pro Max 的世界里，没有被遗忘的文档。”"
        ]
    import random
    daily_quote = quotes[hour % len(quotes)]

    # 状态问候
    if weekday == 0:
        greeting = "🚀 智慧中台 · 开启新周" if hour < 18 else "🌙 深夜备战 · 蓄势待发"
    else:
        greeting = "☀️ 保持好奇 · 持续进化" if 5 <= hour < 18 else "🌒 深度学习 · 永不熄灯"

    # --- 3. 布局 ---
    # 背景 SVG 装饰
    st.markdown("""
        <svg class="brain-svg" width="500" height="500" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <path fill="#3b82f6" d="M44.7,-76.4C58.2,-69.2,70.1,-58.5,78.2,-45.5C86.3,-32.5,90.6,-17.3,91.3,-1.8C92.1,13.8,89.3,29.7,81.4,43.4C73.6,57.1,60.7,68.7,46.1,76.5C31.5,84.3,15.7,88.3,0.5,87.4C-14.7,86.5,-29.4,80.7,-42.6,72.2C-55.8,63.7,-67.4,52.5,-75.6,39.2C-83.8,25.9,-88.6,10.5,-87.4,-4.3C-86.2,-19.1,-79,-33.4,-68.8,-45C-58.7,-56.6,-45.6,-65.5,-32,-72.6C-18.4,-79.8,-4.2,-85.1,10.3,-84.9C24.7,-84.7,48.9,-78.9,44.7,-76.4Z" transform="translate(100 100)" />
        </svg>
    """, unsafe_allow_html=True)

    col_brand, col_spacer, col_auth = st.columns([1.4, 0.1, 1])

    with col_brand:
        st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 class='brand-header'>RAG Pro Max</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='color: #60a5fa; font-weight: 800; letter-spacing: 1px; text-shadow: 0 4px 12px rgba(0,0,0,0.5); margin-top: -10px;'>{greeting}</h2>", unsafe_allow_html=True)
        
        # 核心功能卡片
        steps = [
            ("⚡ 毫秒级知识吞噬", "本地分布式扫描，支持 **100MB+** 超大文档秒级解析与入库。"),
            ("🧬 语义神经元对齐", "内置 **MiniLM-L6** 极速向量化引擎，精准捕捉每一丝业务关联。"),
            ("🛡️ 物理级隐私堡垒", "数据、模型、索引全流程离线。您的每一行代码都是安全的。")
        ]
        
        for title, desc in steps:
            st.markdown(f"""
            <div class='guide-card'>
                <div style='color: white; font-weight: 700; margin-bottom: 5px; font-size: 1.1rem; text-shadow: 0 2px 4px rgba(0,0,0,0.3);'>{title}</div>
                <div style='color: #cbd5e1; font-size: 0.95rem; line-height: 1.5;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        # HUD 面板
        st.markdown(f"""
        <div class='hud-panel'>
            <div class='hud-item'>
                <div class='hud-label'>System Core</div>
                <div class='hud-value'><span class='hud-status'></span>Active</div>
            </div>
            <div class='hud-item'>
                <div class='hud-label'>Engine</div>
                <div class='hud-value'>LlamaIndex v0.12</div>
            </div>
            <div class='hud-item'>
                <div class='hud-label'>AI Accelerator</div>
                <div class='hud-value'>Metal (MPS)</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 激励语录
        st.markdown(f"<div class='quote-box'>{daily_quote}</div>", unsafe_allow_html=True)

    with col_auth:
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 身份验证", "✨ 开启新账户"])
        
        with tab_login:
            with st.container(border=True):
                st.markdown("<h3 style='color:#ffffff; margin-bottom:0;'>控制台登录</h3>", unsafe_allow_html=True)
                st.markdown("<p style='color:#cbd5e1; font-size:0.85rem; margin-bottom:1.5rem;'>验证身份以激活您的私有知识大脑</p>", unsafe_allow_html=True)
                
                with st.form("login_form"):
                    u = st.text_input("Username", placeholder="请输入用户名", label_visibility="collapsed")
                    p = st.text_input("Password", type="password", placeholder="••••••••", label_visibility="collapsed")
                    if st.form_submit_button("立即进入指挥中心", use_container_width=True, type="primary"):
                        if u and p:
                            from src.auth.audit_logger import AuditLogger
                            from src.common.utils import get_client_ip
                            client_ip = get_client_ip()
                            success, info = authenticate_user(u, p)
                            if success:
                                from src.auth.session_manager import create_session
                                token, days = create_session(u)
                                st.query_params["session_token"] = token
                                st.session_state.logged_in = True
                                st.session_state.user = u
                                st.session_state.role = info.get('role', 'standard_user')
                                AuditLogger.log(u, "LOGIN", f"登录成功 (有效期 {days} 天)", ip=client_ip)
                                st.balloons()
                                st.rerun()
                            else:
                                AuditLogger.log(u, "LOGIN_FAILED", f"失败: {info}", status="warning", ip=client_ip)
                                st.error(f"❌ {info}")
                
                st.markdown("<div style='text-align:center; margin: 1rem 0; color:#ffffff; font-size:0.8rem; font-weight:bold;'>—— 或 ——</div>", unsafe_allow_html=True)
                if st.button("🚪 游客登录 (试用模式)", use_container_width=True, help="以受限权限访问系统演示"):
                    st.session_state.logged_in = True
                    st.session_state.user = "guest_user"
                    st.session_state.role = "guest"
                    st.rerun()

        with tab_register:
            with st.container(border=True):
                st.markdown("<h3 style='color:#ffffff;'>注册新身份</h3>", unsafe_allow_html=True)
                st.markdown("<p style='color:#cbd5e1; font-size:0.85rem; margin-bottom:1.5rem;'>注册后即可获得独立物理存储空间</p>", unsafe_allow_html=True)
                
                show_p = st.checkbox("显示密码", key="reg_show_p")
                with st.form("reg_form"):
                    nu = st.text_input("设置用户名", placeholder="支持拼音/英文")
                    np = st.text_input("设置密码", type="default" if show_p else "password")
                    if st.form_submit_button("✨ 提交注册", use_container_width=True, type="primary"):
                        if nu and np:
                            success, msg = register_user(nu, np)
                            if success:
                                st.success("✅ 注册成功！请切换标签页登录。")
                            else:
                                st.error(f"❌ {msg}")

    # --- 页脚 ---
    st.markdown("""
    <div style='margin-top: 4rem; padding-bottom: 2rem; width: 100%; text-align: center; color: rgba(255,255,255,0.2); font-size: 0.75rem; font-family: monospace;'>
        SYSTEM STATUS: ONLINE | ENCRYPTION: AES-256 | RAG PRO MAX v5.6.8
    </div>
    """, unsafe_allow_html=True)
