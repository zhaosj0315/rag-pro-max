import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 恢复酷炫黑风格 + 增强可读性补丁 ---
    st.markdown("""
        <style>
        /* 动态深色极光背景 */
        .stApp {
            background: linear-gradient(-45deg, #020617, #0f172a, #1e1b4b, #020617);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* 品牌标题：渐变 + 发光 */
        .brand-header {
            font-size: 4rem;
            font-weight: 900;
            background: linear-gradient(to right, #60a5fa, #a78bfa, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 10px rgba(96, 165, 250, 0.3));
            margin-bottom: 0.5rem;
            letter-spacing: -2px;
        }

        /* 引导卡片：深色背景增强对比 */
        .guide-card {
            background: rgba(30, 41, 59, 0.7); /* 加深背景 */
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
        }
        .guide-card:hover {
            background: rgba(30, 41, 59, 0.9);
            border-color: #3b82f6;
            transform: translateX(8px);
        }

        /* 文字颜色增强：确保高对比度 */
        .card-title {
            font-weight: 700;
            color: #ffffff !important; /* 纯白 */
            font-size: 1.15rem;
            margin-bottom: 0.4rem;
        }
        .card-desc {
            color: #cbd5e1 !important; /* 明亮的亮灰蓝 */
            font-size: 0.95rem;
            line-height: 1.5;
        }
        
        .step-num {
            background: #3b82f6;
            color: white;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            margin-right: 12px;
            font-weight: 800;
        }

        /* 登录表单：实体化处理 */
        [data-testid="stVerticalBlock"] > div:has(div[style*="border"]) {
            background: #ffffff !important; /* 登录框保持纯白实体，对比最强烈 */
            border-radius: 24px !important;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.8) !important;
            padding: 40px !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. 布局 ---
    col_brand, col_spacer, col_auth = st.columns([1.4, 0.1, 1])

    # --- 左侧：指引区 ---
    with col_brand:
        st.markdown("<div style='margin-top: 3.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 class='brand-header'>RAG Pro Max</h1>", unsafe_allow_html=True)
        st.markdown("<h4 style='color: #94a3b8; font-weight: 300; margin-bottom: 3.5rem;'>下一代企业级私有化知识大脑 · v5.5.8</h4>", unsafe_allow_html=True)
        
        # 步骤
        steps = [
            ("📁 注入知识", "支持本地 PDF/Excel 拖拽上传，或使用**深度爬虫**自动同步网页资产。"),
            ("🧠 智能建模", "自动执行 **OCR 视觉识别**、多维元数据提取，构建企业级语义知识索引。"),
            ("💬 深度对话", "基于全量索引，开启**多专家会审**与数据推演模式，获取极致精准的答案。")
        ]
        
        for i, (title, desc) in enumerate(steps, 1):
            st.markdown(f"""
            <div class='guide-card'>
                <div class='card-title'><span class='step-num'>{i}</span>{title}</div>
                <div class='card-desc' style='padding-left: 38px;'>{desc}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 2.5rem;'></div>", unsafe_allow_html=True)
        # 技术统计
        tc1, tc2, tc3 = st.columns(3)
        tc1.metric("安全性", "100% 本地")
        tc2.metric("并发", "GPU 加速")
        tc3.metric("兼容性", "全格式支持")

    # --- 右侧：登录区 ---
    with col_auth:
        st.markdown("<div style='margin-top: 5rem;'></div>", unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 身份验证", "✨ 开启新账户"])
        
        with tab_login:
            with st.container(border=True):
                st.markdown("<h3 style='color:#1e293b;'>欢迎归来</h3>", unsafe_allow_html=True)
                st.caption("系统已就绪，请输入凭据以访问控制台")
                
                with st.form("login_form"):
                    u = st.text_input("用户名", placeholder="admin", label_visibility="collapsed")
                    p = st.text_input("密码", type="password", placeholder="••••••••", label_visibility="collapsed")
                    if st.form_submit_button("立即进入控制台", use_container_width=True, type="primary"):
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
                
                if st.button("🚪 访客试用模式", use_container_width=True):
                    st.session_state.logged_in = True
                    st.session_state.user = "guest_user"
                    st.session_state.role = "guest"
                    st.rerun()

        with tab_register:
            with st.container(border=True):
                st.markdown("<h3 style='color:#1e293b;'>注册新身份</h3>", unsafe_allow_html=True)
                st.caption("注册后即可获得独立物理存储空间")
                
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
    <div style='position: fixed; bottom: 25px; width: 100%; text-align: center; color: rgba(255,255,255,0.4); font-size: 0.8rem;'>
        <b>RAG Pro Max v5.5.8</b> · 企业私有化知识中台 · &copy; 2026<br>
        <span style='font-size: 0.7rem; opacity: 0.6;'>Powered by Streamlit & LlamaIndex · 系统状态: 正常</span>
    </div>
    """, unsafe_allow_html=True)