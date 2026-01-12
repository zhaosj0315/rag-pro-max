import streamlit as st
import time
import os
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    # 注入全局视觉样式
    st.markdown("""
        <style>
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        .main-card {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        }
        .feature-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            font-size: 0.9rem;
        }
        .auth-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # 顶部品牌区
    st.markdown("<div class='auth-header'>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 3rem; margin-bottom: 0;'>🚀 RAG Pro Max</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #666; font-size: 1.2rem;'>您的私人 100% 数据掌控级知识大脑</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 主布局：左侧对比，右侧登录
    col_info, col_spacer, col_auth = st.columns([1.2, 0.2, 1])

    with col_info:
        st.markdown("### 🌟 为什么选择 RAG Pro Max?")
        st.caption("专业的本地化 RAG 解决方案，支持全量资产离线导出。")
        
        # 权限对比墙
        st.markdown("#### ⚖️ 权限对比")
        comparison_data = {
            "核心功能": ["🗨️ 智能对话", "➕ 创建知识库", "🌐 网页爬虫", "🔍 联网搜索", "✨ AI摘要生成", "🏗️ 全量镜像导出"],
            "访客模式": ["✅", "❌", "❌", "❌", "❌", "❌"],
            "注册用户": ["✅", "✅", "✅", "✅", "✅", "✅"]
        }
        st.table(comparison_data)
        
        st.info("💡 **提示**: 注册用户拥有 100MB 免费存储配额，支持对自己创建的知识库进行一键全量备份。")
        
        # 环境自检
        with st.container(border=True):
            st.markdown("**🛡️ 系统状态**")
            c1, c2 = st.columns(2)
            c1.markdown("● 数据库: `ChromaDB` 🟢")
            c2.markdown("● 存储引擎: `Local` 🟢")

    with col_auth:
        login_tab, register_tab = st.tabs(["🔑 账号登录", "📝 快速注册"])
        
        with login_tab:
            with st.container(border=True):
                st.markdown("#### 欢迎回来")
                with st.form("login_form"):
                    user = st.text_input("用户名", placeholder="输入账号", label_visibility="collapsed")
                    pwd = st.text_input("密码", type="password", placeholder="输入密码", label_visibility="collapsed")
                    submit = st.form_submit_button("立即登录", type="primary", use_container_width=True)
                    
                    if submit:
                        if user and pwd:
                            from src.auth.audit_logger import AuditLogger
                            success, info = authenticate_user(user, pwd)
                            if success:
                                # 生成持久化 Token
                                from src.auth.session_manager import create_session
                                token, days = create_session(user)
                                st.query_params["session_token"] = token
                                
                                st.session_state.logged_in = True
                                st.session_state.user = user
                                st.session_state.role = info.get('role', 'standard_user')
                                AuditLogger.log(user, "LOGIN", f"登录成功 (保持 {days} 天)")
                                st.success(f"验证通过！")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                AuditLogger.log(user, "LOGIN_FAILED", f"失败原因: {info}", status="warning")
                                st.error(f"❌ {info}")
                        else:
                            st.warning("请填写完整信息")
                
                st.markdown("<p style='text-align: center; color: #999; margin: 10px 0;'>或者</p>", unsafe_allow_html=True)
                if st.button("🚪 以访客身份一键进入", use_container_width=True):
                    from src.auth.audit_logger import AuditLogger
                    st.session_state.logged_in = True
                    st.session_state.user = "guest_user"
                    st.session_state.role = "guest"
                    AuditLogger.log("guest_user", "GUEST_LOGIN", "访客进入预览")
                    st.rerun()

        with register_tab:
            with st.container(border=True):
                st.markdown("#### 加入我们")
                with st.form("register_form"):
                    new_user = st.text_input("设置用户名", placeholder="推荐英文字母", label_visibility="collapsed")
                    new_pwd = st.text_input("设置密码", type="password", placeholder="设置强密码", label_visibility="collapsed")
                    new_pwd_confirm = st.text_input("确认密码", type="password", placeholder="再次确认", label_visibility="collapsed")
                    reg_submit = st.form_submit_button("立即提交注册", use_container_width=True)
                    
                    if reg_submit:
                        if not new_user or not new_pwd:
                            st.warning("字段不能为空")
                        elif new_pwd != new_pwd_confirm:
                            st.error("两次密码不一致")
                        else:
                            success, msg = register_user(new_user, new_pwd)
                            if success:
                                from src.auth.audit_logger import AuditLogger
                                AuditLogger.log(new_user, "REGISTER", "用户成功注册")
                                st.success("✅ 注册成功！请切换到登录标签页。")
                            else:
                                st.error(f"❌ {msg}")