import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 数字化指挥中心样式表 (v9.2 最终对齐高亮版) ---
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
                radial-gradient(at 0% 0%, rgba(96, 165, 250, 0.15) 0px, transparent 50%),
                radial-gradient(at 98% 100%, rgba(244, 114, 182, 0.15) 0px, transparent 50%),
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
        }

        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 0rem !important;
            padding-left: 4rem !important;
            padding-right: 4rem !important;
            max-width: 98% !important;
        }

        /* --- 左侧：驾驶舱仪表盘 --- */
        .hero-title {
            font-size: 4.5rem;
            font-weight: 900;
            letter-spacing: -2px;
            color: #ffffff !important; 
            margin-bottom: 0.5rem;
            line-height: 1.1;
            text-shadow: 0 0 40px rgba(59, 130, 246, 0.4);
        }
        .hero-subtitle {
            font-size: 1.2rem;
            color: #cbd5e1;
            font-weight: 400;
            margin-bottom: 2rem;
            line-height: 1.6;
        }
        
        .tag-cloud {
            display: flex;
            gap: 10px;
            margin-bottom: 2.5rem;
            flex-wrap: wrap;
        }
        .capability-tag {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            color: #e2e8f0;
            backdrop-filter: blur(4px);
        }
        
        .flow-container {
            background: rgba(30, 41, 59, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
        }
        .flow-title {
            color: #94a3b8;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 1rem;
            font-weight: 600;
        }
        .flow-steps {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
        }
        .flow-step {
            flex: 1;
            padding-right: 1rem;
            position: relative;
        }
        .flow-step:not(:last-child)::after {
            content: "→";
            position: absolute;
            right: 0;
            top: 5px;
            color: #475569;
            font-size: 1.2rem;
        }
        .step-num {
            color: #00FFFF; 
            font-size: 0.75rem;
            font-weight: 800;
            margin-bottom: 4px;
            display: block;
            text-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
        }
        .step-head {
            color: #fff;
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 4px;
            display: block;
        }
        .step-desc {
            color: #94a3b8;
            font-size: 0.8rem;
            line-height: 1.4;
        }

        .bento-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.2rem;
            margin-bottom: 2rem;
        }
        .bento-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 1.2rem;
        }
        .card-icon { font-size: 1.5rem; margin-bottom: 0.8rem; display: block; }
        .card-title { color: #fff; font-size: 0.95rem; font-weight: 700; margin-bottom: 0.5rem; display: block; }
        /* 紧急修复：描述文字强制高亮，拒绝隐身 */
        .bento-card .card-desc {
            color: #E5E7EB !important; 
            font-size: 0.85rem !important;
            line-height: 1.5 !important;
            font-weight: 500 !important;
            opacity: 1 !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.8);
        }

        /* --- 右侧：登录控制台 (统一卡片化) --- */
        .login-panel {
            background: rgba(15, 23, 42, 0.85); 
            backdrop-filter: blur(32px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 28px;
            padding: 0 !important; /* 移除内边距，交给内部容器精确控制 */
            box-shadow: 0 40px 80px -15px rgba(0, 0, 0, 0.9);
            position: relative;
            margin-top: -2rem !important;
            overflow: hidden;
        }

        .panel-header {
            padding: 2rem 2.5rem 1.5rem 2.5rem;
            background: rgba(255, 255, 255, 0.03);
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .panel-content {
            padding: 1.5rem 2.5rem 2rem 2.5rem;
        }

        .guest-link-container {
            text-align: center;
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        .stTextInput input {
            background-color: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            height: 3.2rem; font-size: 1rem; border-radius: 12px !important;
        }
        .stTextInput input:focus {
            border-color: #3b82f6 !important;
            background-color: rgba(255, 255, 255, 0.08) !important;
        }
        .stTextInput label p { color: #94a3b8 !important; font-size: 0.85rem !important; font-weight: 500 !important; margin-bottom: 4px; }
        
        /* Tab 样式深度定制：消除漂浮感 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            background-color: transparent !important;
            padding-left: 2.5rem !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        .stTabs [data-baseweb="tab"] {
            height: 45px !important;
            color: #64748b !important;
            font-size: 0.95rem !important;
            font-weight: 600 !important;
            padding: 0 !important;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #3b82f6 !important;
            background-color: transparent !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #3b82f6 !important;
        }

        button[kind="primary"] {
            width: 100% !important;
            height: 3.5rem; font-size: 1rem !important; font-weight: 700 !important;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
        }
        button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px -8px rgba(59, 130, 246, 0.6) !important;
        }
        </style>
    """, unsafe_allow_html=True)

    from datetime import datetime
    now = datetime.now()
    greeting = "🚀 智慧中台 · 全速进化" if 5 <= now.hour < 18 else "🌙 深夜备战 · 永不熄灯"

    col_left, col_spacer, col_right = st.columns([1.4, 0.15, 1.1])

    # --- 左侧：驾驶舱 ---
    with col_left:
        st.markdown('<div class="hero-title">RAG Pro Max</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#60a5fa; font-weight:700; margin-bottom:1rem; font-size:1.1rem;">{greeting}</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">企业级认知中台 · 深度融合全模态解析 · 专家级 SQL 推演 · 决策智能</div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div class="tag-cloud">
            <div class="capability-tag">📄 毫秒级检索</div>
            <div class="capability-tag">🧠 Deep Research</div>
            <div class="capability-tag">🕷️ 高保真爬虫</div>
            <div class="capability-tag">📊 智能 SQL 分析</div>
            <div class="capability-tag">🖼️ OCR 全模态</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="flow-container">
            <div class="flow-title">🚀 快速启动指南 / HOW TO START</div>
            <div class="flow-steps">
                <div class="flow-step">
                    <span class="step-num">STEP 01</span>
                    <span class="step-head">构建基地</span>
                    <span class="step-desc">新建知识库，一键挂载私有业务文档</span>
                </div>
                <div class="flow-step">
                    <span class="step-num">STEP 02</span>
                    <span class="step-head">投喂素材</span>
                    <span class="step-desc">全模态 OCR 识别，实时提取核心元数据</span>
                </div>
                <div class="flow-step">
                    <span class="step-num">STEP 03</span>
                    <span class="step-head">智能洞察</span>
                    <span class="step-desc">深度逻辑推演，产出镜像级业务报告</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="bento-grid">
            <div class="bento-card">
                <span class="card-icon">🖼️</span>
                <span class="card-title">全模态解析</span>
                <span class="card-desc">集成 macOS 原生 OCR，支持 JPG/PNG/PDF 混合解析，零配置即用。</span>
            </div>
            <div class="bento-card">
                <span class="card-icon">🧠</span>
                <span class="card-title">深度思考链</span>
                <span class="card-desc">模拟专家级多步分析，事实核查与跨领域知识整合，提供严谨回答。</span>
            </div>
            <div class="bento-card">
                <span class="card-icon">⚡</span>
                <span class="card-title">性能基准</span>
                <span class="card-desc">PDF 处理 ~45秒 (10MB)，支持 GPU/Metal 加速，工业级日志引擎自愈。</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # --- 右侧：指挥中心 (合体重构版) ---
    with col_right:
        # 1. 开启统一卡片容器 + 头部区
        panel_header_html = """
        <div class="login-panel">
            <div class="panel-header">
                <div style="display:flex; align-items:center; justify-content:space-between;">
                    <h1 style='color:white; margin:0; font-size:1.8rem; font-weight:800; letter-spacing:0.5px;'>指挥中心</h1>
                    <div style="display:flex; align-items:center; background:rgba(74,222,128,0.1); padding:4px 12px; border-radius:20px; border:1px solid rgba(74,222,128,0.25);">
                        <div class="status-dot"></div>
                        <span style="color:#4ade80; font-size:0.75rem; font-weight:700; letter-spacing:0.5px;">在线</span>
                    </div>
                </div>
                <div style="color:#64748b; font-size:0.8rem; letter-spacing:1px; margin-top:8px; font-weight:500; font-family:monospace;">SECURE ACCESS TERMINAL v6.7.2</div>
            </div>
        """
        st.markdown(panel_header_html, unsafe_allow_html=True)
        
        # 2. 内容区 (Tab 与 表单)
        # 注意：Streamlit 的 tabs 无法完全嵌套在 HTML div 内部渲染，
        # 我们通过 CSS padding 控制其视觉位置，使其看起来在卡片内。
        tab_login, tab_register = st.tabs(["账号登录", "快速注册"])
        
        with tab_login:
            st.markdown('<div class="panel-content">', unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                u = st.text_input("用户名", placeholder="请输入用户名", label_visibility="visible")
                p = st.text_input("密码", type="password", placeholder="请输入密码", label_visibility="visible")
                st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
                submit = st.form_submit_button("启动指挥系统", use_container_width=True, type="primary")
                
                if submit:
                    if u and p:
                        from src.auth.user_auth import authenticate_user
                        success, info = authenticate_user(u, p)
                        if success:
                            from src.auth.session_manager import create_session
                            token, _ = create_session(u)
                            st.query_params["session_token"] = token
                            st.session_state.logged_in = True
                            st.session_state.user = u
                            st.session_state.role = info.get('role', 'standard_user')
                            st.rerun()
                        else: st.error(f"❌ {info}")
            
            # 3. 访客模式弱化：改造成卡片页脚的文字链接
            st.markdown('<div class="guest-link-container">', unsafe_allow_html=True)
            if st.button("以访客身份进入预览模式", key="guest_btn", help="仅限浏览公开知识库", use_container_width=False):
                st.session_state.logged_in = True; st.session_state.user = "guest_user"; st.session_state.role = "guest"; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True) # 闭合 login-content

        with tab_register:
            st.markdown('<div class="panel-content">', unsafe_allow_html=True)
            with st.form("reg_form"):
                nu = st.text_input("新用户名", placeholder="设置您的登录 ID", label_visibility="visible")
                np = st.text_input("设置密码", type="password", placeholder="设置安全密码", label_visibility="visible")
                st.markdown("<div style='margin-bottom: 1.5rem;'></div>", unsafe_allow_html=True)
                if st.form_submit_button("完成初始化", use_container_width=True, type="primary"):
                    if nu and np:
                        success, msg = register_user(nu, np)
                        if success: st.success("✅ 注册成功！请切换至登录页")
                        else: st.error(f"❌ {msg}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True) # 闭合 login-panel外层容器

    # --- 底部版权 ---
    st.markdown(f"""
    <div style="position: fixed; bottom: 1.5rem; left: 0; width: 100%; text-align: center; color: rgba(255,255,255,0.2); font-size: 0.7rem; font-family: monospace; pointer-events: none;">
        RAG PRO MAX STRATEGIC EDITION v6.7.2 &copy; 2026 | 系统运行正常
    </div>
    """, unsafe_allow_html=True)


    # --- 底部版权 ---
    st.markdown(f"""
    <div style="position: fixed; bottom: 1.5rem; left: 0; width: 100%; text-align: center; color: rgba(255,255,255,0.3); font-size: 0.7rem; font-family: monospace; pointer-events: none;">
        RAG PRO MAX 企业版 v6.6.0 &copy; 2026 | 系统运行正常
    </div>
    """, unsafe_allow_html=True)
