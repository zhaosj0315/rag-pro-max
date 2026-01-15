import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 数字化指挥中心样式表 (v9.0 驾驶舱仪表盘版) ---
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

        /* --- 左侧：仪表盘组件库 --- */
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
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }
        
        /* 1. 能力标签云 */
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
            display: flex;
            align-items: center;
            gap: 6px;
        }
        
        /* 2. 新手引导流程卡片 (Flow Card) */
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
            color: #60a5fa;
            font-size: 0.7rem;
            font-weight: 700;
            margin-bottom: 4px;
            display: block;
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

        /* 3. Bento Grid 技术秀场 */
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
            transition: all 0.3s ease;
        }
        .bento-card:hover {
            background: rgba(255,255,255,0.06);
            border-color: rgba(96, 165, 250, 0.3);
            transform: translateY(-2px);
        }
        .card-icon {
            font-size: 1.5rem;
            margin-bottom: 0.8rem;
            display: block;
        }
        .card-title {
            color: #e2e8f0;
            font-size: 0.95rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            display: block;
        }
        .card-desc {
            color: #94a3b8;
            font-size: 0.8rem;
            line-height: 1.4;
        }

        /* 4. 底部更新日志 */
        .update-log {
            font-family: monospace;
            font-size: 0.75rem;
            color: #64748b;
            padding-top: 1rem;
            border-top: 1px dashed rgba(255,255,255,0.1);
        }
        .update-tag {
            background: #10b981;
            color: #000;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 700;
            margin-right: 8px;
        }

        /* --- 右侧：登录控制台 (保持 v8.5) --- */
        .login-panel {
            background: rgba(15, 23, 42, 0.85); 
            backdrop-filter: blur(24px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 24px;
            padding: 3rem 3rem 2.5rem 3rem; 
            box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.8);
            position: relative;
            margin-top: 0;
        }
        
        .status-dot {
            width: 8px; height: 8px; background-color: #4ade80; border-radius: 50%;
            display: inline-block; margin-right: 6px; box-shadow: 0 0 8px #4ade80;
        }
        
        .stTextInput input {
            background-color: #f8fafc !important;
            border: 2px solid #cbd5e1 !important;
            color: #000000 !important;
            height: 3.5rem; font-size: 1.1rem; border-radius: 10px !important;
        }
        .stTextInput input::placeholder { color: #475569 !important; opacity: 1 !important; }
        .stTextInput label p { color: #ffffff !important; font-size: 1rem !important; font-weight: 700 !important; }
        .stTabs [data-baseweb="tab"] { color: #cbd5e1 !important; font-size: 1.1rem !important; font-weight: 600 !important; }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { color: #ffffff !important; border-bottom: 3px solid #3b82f6 !important; }
        button[kind="primary"] {
            height: 3.5rem; font-size: 1.1rem !important; font-weight: 700 !important;
            background: #3b82f6 !important; box-shadow: 0 10px 20px -5px rgba(59, 130, 246, 0.5) !important;
        }
        button[kind="secondary"] {
            height: 3rem; border: 1px solid rgba(255,255,255,0.3) !important; color: #cbd5e1 !important; background: transparent !important;
        }
        </style>
    """, unsafe_allow_html=True)

    col_left, col_spacer, col_right = st.columns([1.5, 0.2, 1])

    # --- 左侧：驾驶舱仪表盘 ---
    with col_left:
        # 1. 品牌与定义
        st.markdown('<div class="hero-title">RAG Pro Max</div>', unsafe_allow_html=True)
        st.markdown('<div class="hero-subtitle">企业级认知中台 · 深度融合全模态解析 · 专家级 SQL 推演 · 决策智能</div>', unsafe_allow_html=True)
        
        # 能力标签云
        st.markdown("""
        <div class="tag-cloud">
            <div class="capability-tag">📄 毫秒级检索</div>
            <div class="capability-tag">🧠 Deep Research</div>
            <div class="capability-tag">🕷️ 高保真爬虫</div>
            <div class="capability-tag">📊 智能 SQL 分析</div>
            <div class="capability-tag">🖼️ OCR 全模态</div>
        </div>
        """, unsafe_allow_html=True)

        # 2. 新手引导流程 (How to Start)
        st.markdown("""
        <div class="flow-container">
            <div class="flow-title">🚀 快速启动指南 / HOW TO START</div>
            <div class="flow-steps">
                <div class="flow-step">
                    <span class="step-num">STEP 01</span>
                    <span class="step-head">新建资产</span>
                    <span class="step-desc">支持上传 PDF/Excel、粘贴文本或抓取网页 URL</span>
                </div>
                <div class="flow-step">
                    <span class="step-num">STEP 02</span>
                    <span class="step-head">素材投喂</span>
                    <span class="step-desc">拖拽上传，系统自动 OCR 识别并提取元数据</span>
                </div>
                <div class="flow-step">
                    <span class="step-num">STEP 03</span>
                    <span class="step-head">智能洞察</span>
                    <span class="step-desc">开启 Deep Think 模式，进行多轮对话与溯源查证</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 3. Bento Grid 技术秀场
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

        # 4. 底部更新日志
        st.markdown("""
        <div class="update-log">
            <span class="update-tag">NEW</span> v6.6.0 - 极光战略指挥中心上线 | 智能数据分析师智能体实装
        </div>
        """, unsafe_allow_html=True)

    # --- 右侧：登录控制台 (保持不变) ---
    with col_right:
        st.markdown('<div class="login-panel">', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
            <div style="display:flex; align-items:center; justify-content:space-between;">
                <h1 style='color:white; margin:0; font-size:2rem; font-weight:800; letter-spacing:0.5px;'>指挥中心</h1>
                <div style="display:flex; align-items:center; background:rgba(74,222,128,0.1); padding:4px 10px; border-radius:20px; border:1px solid rgba(74,222,128,0.3);">
                    <div class="status-dot"></div>
                    <span style="color:#4ade80; font-size:0.7rem; font-weight:700; letter-spacing:0.5px;">在线</span>
                </div>
            </div>
            <div style="color:#94a3b8; font-size:0.85rem; letter-spacing:1px; margin-top:6px; font-weight:500;">SECURE ACCESS TERMINAL v6.6.0</div>
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
                        else: st.error(f"❌ {info}")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            if st.button("访客模式 (仅预览)", use_container_width=True, type="secondary"):
                st.session_state.logged_in = True; st.session_state.user = "guest_user"; st.session_state.role = "guest"; st.rerun()

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

    # --- 底部版权 ---
    st.markdown(f"""
    <div style="position: fixed; bottom: 1.5rem; left: 0; width: 100%; text-align: center; color: rgba(255,255,255,0.3); font-size: 0.7rem; font-family: monospace; pointer-events: none;">
        RAG PRO MAX 企业版 v6.6.0 &copy; 2026 | 系统运行正常
    </div>
    """, unsafe_allow_html=True)
