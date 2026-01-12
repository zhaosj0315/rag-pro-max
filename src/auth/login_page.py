import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # --- 1. 现代化视觉样式注入 ---
    st.markdown("""
        <style>
        /* 动态波浪背景 */
        .stApp {
            background: linear-gradient(-45deg, #ee7752, #e73c7e, #23a6d5, #23d5ab);
            background-size: 400% 400%;
            animation: gradient 15s ease infinite;
        }
        @keyframes gradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        /* 覆盖层：增加白色半透明遮罩，避免背景过吵 */
        .stApp::before {
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(255,255,255, 0.85);
            z-index: -1;
        }

        /* 登录卡片容器 */
        div[data-testid="stVerticalBlock"] > div[style*="border"] {
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            border: none !important;
            padding: 20px;
        }

        /* 标题渐变特效 */
        .brand-text {
            font-size: 3.2rem;
            font-weight: 800;
            background: -webkit-linear-gradient(45deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0px;
            line-height: 1.2;
        }
        
        /* 特性胶囊 */
        .feature-pill {
            display: inline-flex;
            align-items: center;
            background: #f3f4f6;
            padding: 6px 16px;
            border-radius: 20px;
            margin: 4px;
            font-size: 0.85rem;
            color: #4b5563;
            border: 1px solid #e5e7eb;
        }
        
        /* 权限列表优化 */
        .perm-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 0.9rem;
        }
        .perm-row:last-child { border-bottom: none; }
        .perm-check { color: #10b981; font-weight: bold; }
        .perm-cross { color: #ef4444; opacity: 0.5; }
        
        /* 按钮美化 */
        button[kind="primary"] {
            background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
            border: none;
            transition: all 0.3s;
        }
        button[kind="primary"]:hover {
            box-shadow: 0 4px 12px rgba(37,99,235,0.3);
            transform: translateY(-1px);
        }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. 布局结构 (左右分栏：品牌介绍 vs 登录表单) ---
    col_brand, col_spacer, col_form = st.columns([1.3, 0.2, 1])

    # --- 左侧：品牌与价值主张 ---
    with col_brand:
        st.markdown("<div style='padding-top: 2rem;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 class='brand-text'>RAG Pro Max</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: #64748b; font-weight: 400; margin-top:0;'>企业级私有化知识中台</h3>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='margin: 2rem 0;'>
            <div class='feature-pill'>🔒 100% 数据私有化</div>
            <div class='feature-pill'>🧠 多模型混合编排</div>
            <div class='feature-pill'>🚀 全量资产导出</div>
            <div class='feature-pill'>🕸️ 深度网页爬虫</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 权限对比卡片
        with st.container(border=True):
            st.markdown("##### 💎 会员权益对比")
            
            features = [
                ("🗨️ 智能对话 & 上下文记忆", True, True),
                ("📁 创建私有知识库", False, True),
                ("📊 数据分析 & 深度研究", False, True),
                ("🌐 联网搜索 & 爬虫", False, True),
                ("📥 全量资产镜像导出", False, True)
            ]
            
            # 表头
            st.markdown("""
            <div style='display:flex; justify-content:space-between; color:#9ca3af; font-size:0.8rem; padding-bottom:8px; border-bottom:2px solid #f3f4f6;'>
                <div style='width:50%'>功能权益</div>
                <div style='width:20%; text-align:center'>访客</div>
                <div style='width:20%; text-align:center; color:#3b82f6; font-weight:bold'>注册用户</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 列表内容
            for feat, guest_has, user_has in features:
                g_icon = "✅" if guest_has else "<span class='perm-cross'>×</span>"
                u_icon = "✅" if user_has else "×"
                st.markdown(f"""
                <div class='perm-row'>
                    <div style='width:50%'>{feat}</div>
                    <div style='width:20%; text-align:center'>{g_icon}</div>
                    <div style='width:20%; text-align:center; font-weight:bold; color:#10b981'>{u_icon}</div>
                </div>
                """, unsafe_allow_html=True)

        st.caption("🛡️ 系统底层架构: ChromaDB + Local Embeddings + Multi-Agent")

    # --- 右侧：登录/注册表单 ---
    with col_form:
        st.markdown("<div style='padding-top: 3rem;'></div>", unsafe_allow_html=True)
        
        # 使用 tabs 切换登录/注册
        tab_login, tab_register = st.tabs(["🔐 账号登录", "✨ 立即注册"])
        
        with tab_login:
            st.write("") # Spacer
            with st.container(border=True):
                st.markdown("### 欢迎回来")
                st.caption("请输入您的账号密码以继续")
                
                with st.form("login_form", clear_on_submit=False):
                    username = st.text_input("用户名 / Email", placeholder="例如: admin", key="login_user")
                    password = st.text_input("密码", type="password", placeholder="••••••••", key="login_pwd")
                    
                    # 提交按钮
                    st.write("")
                    submitted = st.form_submit_button("🚀 立即登录", use_container_width=True, type="primary")
                    
                    if submitted:
                        if not username or not password:
                            st.toast("⚠️ 请输入完整的用户名和密码")
                        else:
                            from src.auth.audit_logger import AuditLogger
                            from src.common.utils import get_client_ip
                            client_ip = get_client_ip()
                            success, info = authenticate_user(username, password)
                            
                            if success:
                                # 生成持久化 Token
                                from src.auth.session_manager import create_session
                                token, days = create_session(username)
                                st.query_params["session_token"] = token
                                
                                st.session_state.logged_in = True
                                st.session_state.user = username
                                st.session_state.role = info.get('role', 'standard_user')
                                
                                AuditLogger.log(username, "LOGIN", f"登录成功 (保持 {days} 天)", ip=client_ip)
                                st.balloons()
                                st.success("✅ 验证通过！正在跳转...")
                                time.sleep(0.8)
                                st.rerun()
                            else:
                                AuditLogger.log(username, "LOGIN_FAILED", f"失败: {info}", status="warning", ip=client_ip)
                                st.error(f"❌ {info}")

            # 访客通道
            st.markdown("""
            <div style='text-align: center; margin: 1.5rem 0 1rem 0; position: relative;'>
                <span style='background: #f0f2f6; padding: 0 10px; color: #9ca3af; font-size: 0.8rem;'>或者</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("👻 以访客身份试用", use_container_width=True):
                from src.auth.audit_logger import AuditLogger
                from src.common.utils import get_client_ip
                st.session_state.logged_in = True
                st.session_state.user = "guest_user"
                st.session_state.role = "guest"
                AuditLogger.log("guest_user", "GUEST_LOGIN", "访客试用", ip=get_client_ip())
                st.rerun()

        with tab_register:
            st.write("")
            with st.container(border=True):
                st.markdown("### 创建新账号")
                st.caption("注册即享 100MB 免费私有空间")
                
                # 在表单外或表单内通过变量控制
                show_reg_pwd = st.checkbox("👁️ 显示密码", key="show_reg_pwd")
                
                with st.form("register_form"):
                    new_user = st.text_input("设置用户名", placeholder="仅支持字母与数字", help="这将是您的唯一标识ID")
                    new_pwd = st.text_input(
                        "设置密码", 
                        type="default" if show_reg_pwd else "password",
                        placeholder="建议包含大小写字母"
                    )
                    
                    st.write("")
                    reg_submit = st.form_submit_button("✨ 提交注册", use_container_width=True, type="primary")
                    
                    if reg_submit:
                        if not new_user or not new_pwd:
                            st.warning("⚠️ 字段不能为空")
                        else:
                            success, msg = register_user(new_user, new_pwd)
                            if success:
                                from src.auth.audit_logger import AuditLogger
                                AuditLogger.log(new_user, "REGISTER", "用户成功注册")
                                st.success("✅ 注册成功！请切换到“账号登录”标签页进行登录。")
                            else:
                                st.error(f"❌ {msg}")

    # --- 底部版权 ---
    st.markdown("""
    <div style='text-align: center; margin-top: 4rem; color: #9ca3af; font-size: 0.8rem;'>
        RAG Pro Max v4.5.2 &copy; 2026 Enterprise Edition<br>
        Powered by Streamlit & LlamaIndex
    </div>
    """, unsafe_allow_html=True)
