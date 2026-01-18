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
            background-color: #0f172a !important; /* 强制全局背景深色 */
        }
        
        [data-testid="stAppViewContainer"] {
            background-color: #0f172a !important;
        }
        
        /* 核心背景 */
        .stApp {
            background-color: #0f172a !important;
            background-image: 
                radial-gradient(at 0% 0%, rgba(96, 165, 250, 0.15) 0px, transparent 50%),
                radial-gradient(at 98% 100%, rgba(244, 114, 182, 0.15) 0px, transparent 50%),
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
        }

        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 5rem !important;
            padding-right: 5rem !important;
            max-width: 95% !important;
            display: flex !important;
            align-items: center !important;
            min-height: 100vh !important;
        }
        
        /* 核心：找回被切掉的主标题，确保RAG Pro Max完整显示 */
        [data-testid="stHorizontalBlock"] {
            transform: translateY(-130px) !important;
        }

        /* --- 左侧：驾驶舱仪表盘 --- */
        .hero-title {
            font-size: 4.8rem;
            font-weight: 900;
            letter-spacing: -2.5px;
            color: #ffffff !important; 
            margin-bottom: 0.8rem;
            line-height: 1.0;
            text-shadow: 0 0 50px rgba(59, 130, 246, 0.5);
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

        /* --- 右侧：登录控制台 (极致极简·悬浮版) --- */
        /* 1. 移除大方框，改用悬浮布局 */
        [data-testid="stVerticalBlock"]:has(.login-anchor) {
            background: transparent !important; 
            border: none !important;
            padding: 0 !important;
            gap: 0 !important;
            box-shadow: none !important;
            margin-top: 0rem !important; /* 移除手动位移，依靠 Flexbox 居中 */
            overflow: visible !important;
        }

        /* 2. 内容区净化 */
        .panel-content {
            padding: 1rem 0rem;
        }

        /* 3. 访客链接：彻底文字化 (利用 :has 穿透到真实的按钮容器) */
        /* 这里的核心逻辑是：找到包含 .login-anchor 的那一列，然后对其中的次要按钮进行“核武器级”样式清洗 */
        [data-testid="stVerticalBlock"]:has(.login-anchor) [data-testid="stButton"] {
            display: flex !important;
            justify-content: center !important;
            background: transparent !important;
            margin-top: 1.5rem !important; /* 增加顶部间距，避开上方按钮 */
        }

        [data-testid="stVerticalBlock"]:has(.login-anchor) button[kind="secondary"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
            outline: none !important;
            color: #9CA3AF !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            text-decoration: none !important;
            min-height: 0 !important;
            width: auto !important;
            line-height: 1.5 !important;
            -webkit-appearance: none !important;
            transition: color 0.2s ease !important;
        }

        /* 强制覆盖所有可能的子元素背景 */
        [data-testid="stVerticalBlock"]:has(.login-anchor) button[kind="secondary"] * {
            background: transparent !important;
            background-color: transparent !important;
        }

        /* 悬停状态：变蓝并加下划线 */
        [data-testid="stVerticalBlock"]:has(.login-anchor) button[kind="secondary"]:hover {
            color: #60a5fa !important;
            text-decoration: underline !important;
            background: transparent !important;
            background-color: transparent !important;
        }

        /* 激活与焦点状态：保持透明 */
        [data-testid="stVerticalBlock"]:has(.login-anchor) button[kind="secondary"]:active,
        [data-testid="stVerticalBlock"]:has(.login-anchor) button[kind="secondary"]:focus {
            background: transparent !important;
            background-color: transparent !important;
            color: #60a5fa !important;
            box-shadow: none !important;
        }
        
        /* 4. 右侧列对齐优化：将 Tab 栏下移，使其与左侧流程图顶部对齐 */
        .login-column-spacer {
            margin-top: 15.5rem; /* 经过精确计算，避开左侧标题与副标题的高度 */
        }
        
        /* 4. 输入框对比度强化 (全环境终极适配版) */
        /* 针对自动填充 (Autofill) 的强制覆盖，防止浏览器自动变白/变黄 */
        input:-webkit-autofill,
        input:-webkit-autofill:hover, 
        input:-webkit-autofill:focus, 
        input:-webkit-autofill:active {
            -webkit-box-shadow: 0 0 0 1000px #1e293b inset !important;
            -webkit-text-fill-color: #ffffff !important;
            caret-color: #ffffff !important;
            transition: background-color 5000s ease-in-out 0s;
        }

        /* 针对所有可能的输入框容器层级进行深色锁定 */
        .stTextInput, [data-testid="stTextInput"], div[data-baseweb="input"] {
            background-color: #1e293b !important;
            border-radius: 12px !important;
            border: 1px solid rgba(255, 255, 255, 0.3) !important; /* 提亮边框 */
        }

        /* 穿透所有层级，强制内联输入框样式 */
        .stTextInput input, 
        [data-testid="stTextInput"] input,
        div[data-baseweb="input"] input {
            background-color: transparent !important; /* 依靠外层容器显色 */
            color: #ffffff !important;
            -webkit-text-fill-color: #ffffff !important;
            caret-color: #ffffff !important; 
            height: 3.2rem !important; 
            font-size: 1.1rem !important; 
            padding: 0 1rem !important;
            border: none !important;
            box-shadow: none !important;
        }
        
        /* 强制覆盖所有内层可能出现的白色/灰色背景 div */
        div[data-baseweb="input"] div, 
        div[data-testid="stTextInput"] div {
            background-color: transparent !important;
        }

        /* 焦点状态下的增强 */
        [data-testid="stTextInput"]:focus-within, 
        div[data-baseweb="input"]:focus-within {
            border-color: #3b82f6 !important;
            background-color: #0f172a !important;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.4) !important;
        }
        
        /* 占位符颜色 (Placeholder) - 提高对比度到最佳可读性 */
        ::placeholder {
            color: #9CA3AF !important; /* 浅灰色，最佳可读性 */
            -webkit-text-fill-color: #9CA3AF !important;
        }

        /* 标签标题文字显色 */
        .stTextInput label p { 
            color: #cbd5e1 !important; 
            font-size: 0.9rem !important; 
            font-weight: 600 !important;
            margin-bottom: 4px;
        }
        
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
        
        /* 5. 彻底移除表单边框与背景 */
        [data-testid="stForm"] {
            background-color: transparent !important;
            border: none !important;
            padding: 0 !important;
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

    # --- 右侧：极简登录卡片 (完全封装版) ---
    with col_right:
        # 增加占位层，实现左右对齐
        st.markdown('<div class="login-column-spacer"></div>', unsafe_allow_html=True)
        
        # 1. 注入容器锁定锚点 (隐藏)
        st.markdown('<div class="login-anchor"></div>', unsafe_allow_html=True)
        
        # 2. 交互内容区 (Tabs 直接封顶)
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
            st.markdown('</div>', unsafe_allow_html=True)

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
        
        # 3. 访客页脚 (纯文字链接居中)
        if st.button("没有账号？以访客身份浏览", key="guest_btn", help="仅限浏览公开知识库", use_container_width=False):
            st.session_state.logged_in = True; st.session_state.user = "guest_user"; st.session_state.role = "guest"; st.rerun()

    # --- 4. 全局状态页脚 (固定沉底，全宽居中) ---
    st.markdown(f"""
    <div style="position: fixed; bottom: 1.5rem; left: 0; width: 100%; text-align: center; color: rgba(255,255,255,0.25); font-size: 0.7rem; font-family: monospace; pointer-events: none; letter-spacing: 1px; z-index: 9999;">
        RAG PRO MAX STRATEGIC EDITION v6.7.2 &copy; 2026 | 系统状态: 正常运行
    </div>
    """, unsafe_allow_html=True)
