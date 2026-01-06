"""
用户登录界面组件
"""

import streamlit as st
from src.services.auth_service import get_auth_service

class LoginUI:
    def __init__(self):
        self.auth_service = get_auth_service()
    
    def show_login_page(self):
        """显示登录页面"""
        st.set_page_config(
            page_title="RAG Pro Max - 用户登录",
            page_icon="🔐",
            layout="centered"
        )
        
        # 页面标题
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1>🚀 RAG Pro Max</h1>
            <h3>智能文档问答系统</h3>
            <p style="color: #666;">请登录以继续使用</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 登录表单
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                tab1, tab2 = st.tabs(["🔑 登录", "📝 注册"])
                
                with tab1:
                    self._show_login_form()
                
                with tab2:
                    self._show_register_form()
    
    def _show_login_form(self):
        """显示登录表单"""
        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="请输入用户名")
            password = st.text_input("密码", type="password", placeholder="请输入密码")
            
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button("🔑 登录", use_container_width=True)
            with col2:
                demo_btn = st.form_submit_button("👤 演示账号", use_container_width=True)
            
            if login_btn:
                if username and password:
                    if self.auth_service.authenticate(username, password):
                        self.auth_service.login(username)
                        st.success(f"欢迎回来，{username}！")
                        st.rerun()
                    else:
                        st.error("用户名或密码错误")
                else:
                    st.warning("请输入用户名和密码")
            
            if demo_btn:
                # 创建演示账号
                demo_user = "demo"
                demo_pass = "demo123"
                
                # 如果演示账号不存在，创建它
                if demo_user not in self.auth_service.users:
                    self.auth_service.register_user(demo_user, demo_pass, "demo@example.com")
                
            if demo_btn:
                # 创建演示账号
                demo_user = "demo"
                demo_pass = "demo123"
                
                # 如果演示账号不存在，创建它
                if demo_user not in self.auth_service.users:
                    self.auth_service.register_user(demo_user, demo_pass, "demo@example.com")
                
                if self.auth_service.authenticate(demo_user, demo_pass):
                    self.auth_service.login(demo_user)
                    st.success("已使用演示账号登录！")
                    st.rerun()
    
    def _show_register_form(self):
        """显示注册表单"""
        with st.form("register_form"):
            username = st.text_input("用户名", placeholder="请输入用户名（3-20个字符）")
            email = st.text_input("邮箱", placeholder="请输入邮箱（可选）")
            password = st.text_input("密码", type="password", placeholder="请输入密码（至少6位）")
            confirm_password = st.text_input("确认密码", type="password", placeholder="请再次输入密码")
            
            register_btn = st.form_submit_button("📝 注册", use_container_width=True)
            
            if register_btn:
                if not username or not password:
                    st.error("用户名和密码不能为空")
                elif len(username) < 3 or len(username) > 20:
                    st.error("用户名长度应在3-20个字符之间")
                elif len(password) < 6:
                    st.error("密码长度至少6位")
                elif password != confirm_password:
                    st.error("两次输入的密码不一致")
                else:
                    if self.auth_service.register_user(username, password, email):
                        st.success("注册成功！请切换到登录标签页登录")
                    else:
                        st.error("用户名已存在，请选择其他用户名")
    
    def show_user_menu(self):
        """显示用户菜单（在主界面顶部）"""
        if self.auth_service.is_logged_in():
            current_user = self.auth_service.get_current_user()
            
            with st.sidebar:
                st.markdown("---")
                
                # 用户信息区域
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"👤 **{current_user}**")
                with col2:
                    # 用户管理按钮（小人图标）
                    if st.button("👤", help="用户管理", key="user_menu_btn"):
                        st.session_state.show_user_dialog = True
                
                # 快速退出按钮
                if st.button("🚪 退出登录", use_container_width=True):
                    self.auth_service.logout()
                    st.rerun()
        
        # 用户管理对话框
        self._show_user_dialog()
    
    def _show_user_dialog(self):
        """显示用户管理对话框"""
        if st.session_state.get('show_user_dialog', False):
            current_user = self.auth_service.get_current_user()
            
            # 使用模态对话框
            with st.container():
                st.markdown("---")
                st.markdown("### 👤 用户管理")
                
                # 用户信息标签页
                if self.auth_service.is_admin():
                    tab1, tab2, tab3 = st.tabs(["📋 个人信息", "🔒 修改密码", "👥 用户管理"])
                else:
                    tab1, tab2 = st.tabs(["📋 个人信息", "🔒 修改密码"])
                    tab3 = None
                
                with tab1:
                    self._show_user_info(current_user)
                
                with tab2:
                    self._show_change_password(current_user)
                
                if self.auth_service.is_admin() and tab3:
                    with tab3:
                        self._show_admin_panel()
                
                # 关闭按钮
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("✖️ 关闭", use_container_width=True):
                        st.session_state.show_user_dialog = False
                        st.rerun()
    
    def _show_user_info(self, username):
        """显示用户信息"""
        user_info = self.auth_service.get_user_info(username)
        if user_info:
            st.write(f"**用户名**: {username}")
            st.write(f"**邮箱**: {user_info.get('email', '未设置')}")
            st.write(f"**注册时间**: {user_info.get('created_at', '未知')[:10]}")
            if user_info.get('last_login'):
                st.write(f"**上次登录**: {user_info.get('last_login', '未知')[:16]}")
            
            role = user_info.get('role', '普通用户')
            if role == 'admin':
                st.write("**角色**: 👑 管理员")
            else:
                st.write("**角色**: 👤 普通用户")
            
            # 添加全量下载功能
            st.markdown("---")
            st.markdown("**📦 我的知识库**")
            
            # 获取用户的知识库统计
            from src.ui.kb_management_ui import get_knowledge_base_list
            if self.auth_service.is_admin():
                user_kbs = [kb for kb in get_knowledge_base_list() if kb.get('owner') == username]
            else:
                user_kbs = get_knowledge_base_list()  # 普通用户只能看到自己的
            
            if user_kbs:
                # 显示知识库统计
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("知识库数量", len(user_kbs))
                with col2:
                    total_docs = sum(kb.get('doc_count', 0) for kb in user_kbs)
                    st.metric("文档总数", total_docs)
                
                # 显示知识库列表（前5个）
                st.markdown("**知识库列表**:")
                for i, kb in enumerate(user_kbs[:5]):
                    kb_name = kb.get('name', '未知')
                    doc_count = kb.get('doc_count', 0)
                    st.write(f"📚 {kb_name} ({doc_count}个文档)")
                
                if len(user_kbs) > 5:
                    st.caption(f"... 还有 {len(user_kbs) - 5} 个知识库")
                
                # 批量下载按钮
                st.markdown("**数据导出**:")
                if st.button("📥 下载所有知识库", key=f"download_all_{username}", use_container_width=True, type="primary"):
                    self._handle_bulk_download(username, user_kbs)
                st.caption("💡 将打包所有知识库的完整数据，包括原始文件、元数据、向量索引、摘要和聊天历史")
            else:
                st.info("暂无知识库")
                st.caption("💡 创建知识库后，可以在这里查看和导出您的所有数据")
    
    def _handle_bulk_download(self, username: str, kb_list: list):
        """处理批量下载"""
        from src.services.kb_download_service import get_download_service
        import tempfile
        import zipfile
        import os
        
        try:
            with st.spinner("正在打包所有知识库..."):
                # 创建临时目录
                temp_dir = tempfile.mkdtemp()
                zip_path = os.path.join(temp_dir, f"{username}_all_knowledge_bases.zip")
                
                download_service = get_download_service()
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as main_zipf:
                    # 为每个知识库创建子目录
                    for kb in kb_list:
                        kb_name = kb['name']
                        
                        # 获取知识库的所有内容
                        items = download_service.get_downloadable_items(kb_name)
                        
                        if not any(items.values()):
                            continue
                        
                        # 创建单个知识库的临时包（包含聊天历史）
                        kb_zip_path = download_service.create_download_package(
                            kb_name, 
                            ['original_files', 'metadata', 'vector_data', 'summaries', 'chat_history']
                        )
                        
                        if kb_zip_path and os.path.exists(kb_zip_path):
                            # 将知识库包添加到主包中
                            main_zipf.write(kb_zip_path, f"{kb_name}/{kb_name}_export.zip")
                            
                            # 清理临时文件
                            try:
                                os.remove(kb_zip_path)
                            except:
                                pass
                    
                    # 添加总体说明文件
                    readme_content = f"""用户 {username} 的知识库导出包
=================================

导出时间: {st.session_state.get('current_time', '未知')}
知识库数量: {len(kb_list)}

目录结构:
"""
                    for kb in kb_list:
                        readme_content += f"- {kb['name']}/: {kb.get('description', '无描述')}\n"
                    
                    readme_content += """
使用说明:
每个知识库都打包在独立的目录中，包含完整的导出数据。
可以单独解压使用，或批量导入到新的 RAG Pro Max 实例。
"""
                    main_zipf.writestr("README.txt", readme_content)
            
            # 提供下载
            if os.path.exists(zip_path):
                with open(zip_path, 'rb') as f:
                    zip_data = f.read()
                
                st.download_button(
                    label="💾 下载完整数据包",
                    data=zip_data,
                    file_name=f"{username}_all_knowledge_bases.zip",
                    mime="application/zip",
                    key=f"bulk_download_{username}",
                    use_container_width=True
                )
                
                st.success(f"✅ 已打包 {len(kb_list)} 个知识库！")
                
                # 清理临时文件
                try:
                    os.remove(zip_path)
                    os.rmdir(temp_dir)
                except:
                    pass
            else:
                st.error("创建数据包失败")
                
        except Exception as e:
            st.error(f"批量下载失败: {e}")
    
    def _show_change_password(self, username):
        """显示修改密码表单"""
        with st.form("change_password_form_dialog"):
            old_password = st.text_input("当前密码", type="password")
            new_password = st.text_input("新密码", type="password")
            confirm_new_password = st.text_input("确认新密码", type="password")
            
            if st.form_submit_button("🔒 修改密码", use_container_width=True):
                if not old_password or not new_password:
                    st.error("请填写所有字段")
                elif len(new_password) < 6:
                    st.error("新密码长度至少6位")
                elif new_password != confirm_new_password:
                    st.error("两次输入的新密码不一致")
                else:
                    if self.auth_service.change_password(username, old_password, new_password):
                        st.success("密码修改成功！")
                    else:
                        st.error("当前密码错误")
    
    def _show_admin_panel(self):
        """显示管理员面板"""
        from src.ui.user_management_ui import UserManagementUI
        user_mgmt = UserManagementUI()
        user_mgmt.show_user_management()

def require_auth():
    """装饰器：要求用户登录"""
    auth_service = get_auth_service()
    
    if not auth_service.is_logged_in():
        login_ui = LoginUI()
        login_ui.show_login_page()
        st.stop()
    
    return True
