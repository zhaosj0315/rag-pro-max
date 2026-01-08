import streamlit as st
import time
from src.auth.user_auth import authenticate_user, register_user

def render_login_page():
    st.markdown("""
        <style>
        .login-container {
            max-width: 400px;
            margin: auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            background: white;
        }
        .stButton button {
            width: 100%;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<h1 style='text-align: center; color: #FF4B4B;'>🚀 RAG Pro Max</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #666;'>企业级智能化知识库管控平台</p>", unsafe_allow_html=True)
        
        login_tab, register_tab = st.tabs(["🔑 账号登录", "📝 自助注册"])
        
        with login_tab:
            with st.form("login_form"):
                user = st.text_input("用户名", placeholder="输入您的账号")
                pwd = st.text_input("密码", type="password", placeholder="输入您的密码")
                submit = st.form_submit_button("立即登录", type="primary")
                
                if submit:
                    if user and pwd:
                        from src.auth.audit_logger import AuditLogger
                        success, info = authenticate_user(user, pwd)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.session_state.role = info.get('role', 'standard_user')
                            AuditLogger.log(user, "LOGIN", "用户登录成功")
                            st.success(f"欢迎回来，{user}！")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            AuditLogger.log(user, "LOGIN_FAILED", f"登录失败: {info}", status="warning")
                            st.error(f"登录失败: {info}")
                    else:
                        st.warning("请填写完整的登录信息")
            
            st.markdown("<p style='text-align: center; color: #999; font-size: 0.8rem;'>或</p>", unsafe_allow_html=True)
            if st.button("🚪 以访客身份进入 (Guest Mode)", use_container_width=True):
                from src.auth.audit_logger import AuditLogger
                st.session_state.logged_in = True
                st.session_state.user = "guest_user"
                st.session_state.role = "guest"
                AuditLogger.log("guest_user", "GUEST_LOGIN", "通过访客模式进入系统")
                st.toast("已进入访客预览模式")
                time.sleep(0.5)
                st.rerun()

        with register_tab:
            with st.form("register_form"):
                new_user = st.text_input("设置用户名", placeholder="建议使用英文字母")
                new_pwd = st.text_input("设置密码", type="password", placeholder="请妥善保管")
                new_pwd_confirm = st.text_input("确认密码", type="password")
                reg_submit = st.form_submit_button("提交注册")
                
                if reg_submit:
                    if not new_user or not new_pwd:
                        st.warning("用户名或密码不能为空")
                    elif new_pwd != new_pwd_confirm:
                        st.error("两次输入的密码不一致")
                    else:
                        success, msg = register_user(new_user, new_pwd)
                        if success:
                            from src.auth.audit_logger import AuditLogger
                            AuditLogger.log(new_user, "REGISTER", "用户自助注册成功")
                            st.success("注册成功！请切换到登录标签页进行登录。")
                        else:
                            st.error(msg)
