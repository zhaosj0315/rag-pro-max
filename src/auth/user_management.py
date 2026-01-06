#!/usr/bin/env python3
"""
用户管理界面
"""

import streamlit as st
from src.auth.user_auth import user_auth
from src.auth.login_page import logout
import os
import shutil
from datetime import datetime

def show_user_management():
    """显示用户管理界面"""
    user_context = st.session_state.get('user_context', {})
    
    st.title("👤 用户管理")
    
    # 当前用户信息
    st.subheader("📋 当前用户")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**用户名**: {user_context.get('username', 'Unknown')}")
    with col2:
        st.info(f"**角色**: {user_context.get('role', 'Unknown')}")
    with col3:
        if st.button("🚪 退出登录", type="secondary"):
            logout()
    
    st.markdown("---")
    
    # 管理员功能
    if user_context.get('is_admin', False):
        show_admin_panel()
    else:
        show_user_panel()

def show_admin_panel():
    """管理员面板"""
    st.subheader("🔧 管理员面板")
    
    tab1, tab2, tab3 = st.tabs(["👥 用户管理", "📊 使用统计", "🗂️ 数据管理"])
    
    with tab1:
        show_user_list()
        show_add_user_form()
    
    with tab2:
        show_usage_statistics()
    
    with tab3:
        show_data_management()
    
    with st.tabs(["📦 批量下载"])[0]:
        show_batch_download()

def show_user_panel():
    """普通用户面板"""
    username = st.session_state.user_context['username']
    is_guest = username.startswith('guest_')
    
    tab1, tab2 = st.tabs(["📊 我的统计", "📦 批量下载"])
    
    with tab1:
        st.subheader("📊 我的统计")
        
        if is_guest:
            st.warning("👤 您正在使用游客模式，数据将在会话结束后清理")
        
        # 用户知识库统计
        user_kb_path = f"vector_db_storage/{username}"
        if os.path.exists(user_kb_path):
            kb_count = len([d for d in os.listdir(user_kb_path) if os.path.isdir(os.path.join(user_kb_path, d))])
        else:
            kb_count = 0
        
        # 用户对话历史统计
        user_chat_path = f"chat_histories/{username}"
        if os.path.exists(user_chat_path):
            chat_count = len([f for f in os.listdir(user_chat_path) if f.endswith('.json')])
        else:
            chat_count = 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📚 我的知识库", kb_count)
        with col2:
            st.metric("💬 对话历史", chat_count)
        
        # 游客模式额外功能
        if is_guest:
            st.markdown("---")
            st.subheader("🔄 游客操作")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📝 转为正式用户"):
                    st.info("请先退出登录，然后注册正式账户")
            with col2:
                if st.button("🗑️ 清理我的数据"):
                    from src.auth.user_auth import user_auth
                    user_auth.cleanup_guest_data(username)
                    st.success("✅ 游客数据已清理")
                    st.rerun()
    
    with tab2:
        show_user_batch_download()

def show_user_list():
    """显示用户列表"""
    st.markdown("#### 👥 用户列表")
    
    users = user_auth.get_all_users()
    
    if not users:
        st.info("暂无用户")
        return
    
    for username, user_data in users.items():
        with st.expander(f"👤 {username} ({user_data['role']})"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**创建时间**: {user_data['created_at'][:19]}")
            with col2:
                last_login = user_data.get('last_login')
                if last_login:
                    st.write(f"**最后登录**: {last_login[:19]}")
                else:
                    st.write("**最后登录**: 从未登录")
            with col3:
                if username != "admin":  # 保护管理员账户
                    if st.button(f"🗑️ 删除", key=f"del_{username}"):
                        if user_auth.delete_user(username):
                            # 删除用户数据
                            cleanup_user_data(username)
                            st.success(f"✅ 用户 {username} 已删除")
                            st.rerun()
                        else:
                            st.error("❌ 删除失败")

def show_add_user_form():
    """添加用户表单"""
    st.markdown("#### ➕ 添加新用户")
    
    with st.form("add_user_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_username = st.text_input("用户名")
        with col2:
            new_password = st.text_input("密码", type="password")
        with col3:
            new_role = st.selectbox("角色", ["user", "admin"])
        
        if st.form_submit_button("➕ 添加用户"):
            if new_username and new_password:
                if len(new_password) < 6:
                    st.error("❌ 密码长度至少6位")
                elif user_auth.register_user(new_username, new_password, new_role):
                    st.success(f"✅ 用户 {new_username} 添加成功")
                    st.rerun()
                else:
                    st.error("❌ 用户名已存在")
            else:
                st.error("❌ 请填写完整信息")

def show_usage_statistics():
    """显示使用统计"""
    st.markdown("#### 📊 系统使用统计")
    
    # 获取所有用户数据
    users = user_auth.get_all_users()
    
    # 统计信息
    total_users = len(users)
    admin_count = len([u for u in users.values() if u.get('role') == 'admin'])
    user_count = len([u for u in users.values() if u.get('role') == 'user'])
    
    # 游客统计 - 检查临时数据目录
    guest_dirs = []
    guest_storage_path = "vector_db_storage"
    if os.path.exists(guest_storage_path):
        for item in os.listdir(guest_storage_path):
            if item.startswith("guest_"):
                guest_dirs.append(item)
    
    guest_count = len(guest_dirs)
    
    # 显示统计卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("总用户数", total_users)
    with col2:
        st.metric("管理员", admin_count)
    with col3:
        st.metric("普通用户", user_count)
    with col4:
        st.metric("活跃游客", guest_count)
    
    # 详细用户列表
    st.write("### 📋 详细用户信息")
    
    # 注册用户
    if users:
        st.write("**注册用户:**")
        for username, user_info in users.items():
            role_icon = "👑" if user_info.get('role') == 'admin' else "👤"
            last_login = user_info.get('last_login', '从未登录')
            
            # 统计用户知识库
            user_kb_path = f"vector_db_storage/{username}"
            kb_count = 0
            if os.path.exists(user_kb_path):
                kb_count = len([d for d in os.listdir(user_kb_path) if os.path.isdir(os.path.join(user_kb_path, d))])
            
            st.write(f"- {role_icon} **{username}** ({user_info.get('role', 'user')}) - 知识库: {kb_count} - 最后登录: {last_login}")
    
    # 游客用户
    if guest_dirs:
        st.write("**活跃游客:**")
        for guest_dir in guest_dirs:
            # 获取目录创建时间和知识库数量
            dir_path = os.path.join(guest_storage_path, guest_dir)
            if os.path.exists(dir_path):
                import time
                create_time = time.ctime(os.path.getctime(dir_path))
                kb_count = len([d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))])
                st.write(f"- 👻 **{guest_dir}** - 知识库: {kb_count} - 创建时间: {create_time}")
    
    # 历史知识库统计
    historical_kbs = []
    if os.path.exists(guest_storage_path):
        for item in os.listdir(guest_storage_path):
            item_path = os.path.join(guest_storage_path, item)
            if os.path.isdir(item_path) and not item.startswith(('admin', 'guest_')) and item not in users:
                historical_kbs.append(item)
    
    if historical_kbs:
        st.write("**历史数据:**")
        st.write(f"- 📜 **历史知识库**: {len(historical_kbs)} 个")
        with st.expander("查看历史知识库详情"):
            for kb in historical_kbs:
                st.write(f"  - {kb}")
    
    # 系统资源统计
    st.write("### 💾 系统资源统计")
    
    # 计算存储空间使用
    def get_dir_size(path):
        total = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        except:
            pass
        return total
    
    # 各目录大小
    storage_stats = {}
    if os.path.exists("vector_db_storage"):
        storage_stats["向量数据库"] = get_dir_size("vector_db_storage") / (1024*1024)  # MB
    if os.path.exists("chat_histories"):
        storage_stats["对话历史"] = get_dir_size("chat_histories") / (1024*1024)  # MB
    if os.path.exists("uploaded_files"):
        storage_stats["上传文件"] = get_dir_size("uploaded_files") / (1024*1024)  # MB
    
    if storage_stats:
        col1, col2, col3 = st.columns(3)
        cols = [col1, col2, col3]
        for i, (name, size_mb) in enumerate(storage_stats.items()):
            with cols[i % 3]:
                st.metric(name, f"{size_mb:.1f} MB")

def show_batch_download():
    """管理员批量下载功能"""
    st.subheader("📦 批量下载管理")
    
    # 获取所有用户的知识库
    all_kbs = {}
    
    # 注册用户的知识库
    users = user_auth.get_all_users()
    for username in users.keys():
        user_kb_path = f"vector_db_storage/{username}"
        if os.path.exists(user_kb_path):
            user_kbs = [d for d in os.listdir(user_kb_path) if os.path.isdir(os.path.join(user_kb_path, d))]
            if user_kbs:
                all_kbs[f"👑 {username}" if users[username].get('role') == 'admin' else f"👤 {username}"] = user_kbs
    
    # 游客的知识库
    guest_storage_path = "vector_db_storage"
    if os.path.exists(guest_storage_path):
        for item in os.listdir(guest_storage_path):
            if item.startswith("guest_"):
                guest_path = os.path.join(guest_storage_path, item)
                if os.path.exists(guest_path):
                    guest_kbs = [d for d in os.listdir(guest_path) if os.path.isdir(os.path.join(guest_path, d))]
                    if guest_kbs:
                        all_kbs[f"👻 {item}"] = guest_kbs
    
    # 历史知识库
    historical_kbs = []
    if os.path.exists(guest_storage_path):
        for item in os.listdir(guest_storage_path):
            item_path = os.path.join(guest_storage_path, item)
            if os.path.isdir(item_path) and not item.startswith(('admin', 'guest_')) and item not in users:
                historical_kbs.append(item)
    
    if historical_kbs:
        all_kbs["📜 历史数据"] = historical_kbs
    
    if not all_kbs:
        st.info("暂无可下载的知识库")
        return
    
    # 知识库选择界面
    st.write("### 📋 选择要下载的知识库")
    
    selected_kbs = []
    
    # 全选/全不选按钮
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("✅ 全选"):
            st.session_state.batch_select_all = True
            st.rerun()
    with col2:
        if st.button("❌ 全不选"):
            st.session_state.batch_select_all = False
            st.rerun()
    
    # 按用户分组显示知识库
    for user_label, kbs in all_kbs.items():
        with st.expander(f"{user_label} ({len(kbs)} 个知识库)", expanded=True):
            for kb in kbs:
                default_checked = st.session_state.get('batch_select_all', False)
                if st.checkbox(f"📚 {kb}", key=f"batch_{user_label}_{kb}", value=default_checked):
                    # 确定实际的用户名和知识库路径
                    actual_username = user_label.split(' ', 1)[1] if ' ' in user_label else user_label
                    if user_label == "📜 历史数据":
                        kb_path = f"vector_db_storage/{kb}"
                    else:
                        kb_path = f"vector_db_storage/{actual_username}/{kb}"
                    
                    selected_kbs.append({
                        'name': kb,
                        'path': kb_path,
                        'user': user_label
                    })
    
    # 下载选项
    if selected_kbs:
        st.write("### ⚙️ 下载选项")
        
        col1, col2 = st.columns(2)
        with col1:
            include_vectors = st.checkbox("📊 包含向量数据", value=True)
            include_docs = st.checkbox("📄 包含原始文档", value=True)
        with col2:
            include_configs = st.checkbox("⚙️ 包含配置文件", value=True)
            include_metadata = st.checkbox("📋 包含元数据", value=True)
        
        # 批量下载按钮
        st.write("### 📥 开始下载")
        st.info(f"已选择 {len(selected_kbs)} 个知识库")
        
        if st.button("📦 生成批量下载包", type="primary", use_container_width=True):
            with st.spinner("🔄 正在打包所有选中的知识库..."):
                batch_data = create_batch_download(selected_kbs, {
                    'vectors': include_vectors,
                    'documents': include_docs,
                    'configs': include_configs,
                    'metadata': include_metadata
                })
            
            if batch_data:
                from datetime import datetime
                filename = f"batch_kbs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                
                st.session_state.download_ready = {
                    'data': batch_data,
                    'filename': filename
                }
                
                st.success("✅ 批量下载包生成完成！")
                st.rerun()
            else:
                st.error("❌ 批量下载包生成失败")

def show_user_batch_download():
    """用户批量下载功能"""
    st.subheader("📦 我的知识库批量下载")
    
    username = st.session_state.user_context['username']
    user_kb_path = f"vector_db_storage/{username}"
    
    if not os.path.exists(user_kb_path):
        st.info("您还没有创建任何知识库")
        return
    
    # 获取用户的所有知识库
    user_kbs = [d for d in os.listdir(user_kb_path) if os.path.isdir(os.path.join(user_kb_path, d))]
    
    if not user_kbs:
        st.info("您还没有创建任何知识库")
        return
    
    st.write(f"### 📋 我的知识库清单 ({len(user_kbs)} 个)")
    
    selected_kbs = []
    
    # 全选/全不选按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ 全选我的知识库"):
            st.session_state.user_select_all = True
            st.rerun()
    with col2:
        if st.button("❌ 全不选"):
            st.session_state.user_select_all = False
            st.rerun()
    
    # 知识库列表
    for kb in user_kbs:
        default_checked = st.session_state.get('user_select_all', False)
        if st.checkbox(f"📚 {kb}", key=f"user_batch_{kb}", value=default_checked):
            selected_kbs.append({
                'name': kb,
                'path': os.path.join(user_kb_path, kb),
                'user': username
            })
    
    # 下载选项
    if selected_kbs:
        st.write("### ⚙️ 下载选项")
        
        col1, col2 = st.columns(2)
        with col1:
            include_vectors = st.checkbox("📊 包含向量数据", value=True, key="user_vectors")
            include_docs = st.checkbox("📄 包含原始文档", value=True, key="user_docs")
        with col2:
            include_configs = st.checkbox("⚙️ 包含配置文件", value=True, key="user_configs")
            include_metadata = st.checkbox("📋 包含元数据", value=True, key="user_metadata")
        
        # 下载按钮
        st.write("### 📥 开始下载")
        st.info(f"已选择 {len(selected_kbs)} 个知识库")
        
        if st.button("📦 下载我的知识库", type="primary", use_container_width=True):
            with st.spinner("🔄 正在打包您的知识库..."):
                batch_data = create_batch_download(selected_kbs, {
                    'vectors': include_vectors,
                    'documents': include_docs,
                    'configs': include_configs,
                    'metadata': include_metadata
                })
            
            if batch_data:
                from datetime import datetime
                filename = f"{username}_kbs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                
                st.session_state.download_ready = {
                    'data': batch_data,
                    'filename': filename
                }
                
                st.success("✅ 知识库打包完成！")
                st.rerun()
            else:
                st.error("❌ 知识库打包失败")

def create_batch_download(selected_kbs, options):
    """创建批量下载包"""
    import zipfile
    import io
    import json
    
    zip_buffer = io.BytesIO()
    
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # 添加批量下载信息
            batch_info = {
                'download_time': str(datetime.now()),
                'total_kbs': len(selected_kbs),
                'options': options,
                'knowledge_bases': []
            }
            
            for kb_info in selected_kbs:
                kb_name = kb_info['name']
                kb_path = kb_info['path']
                user = kb_info['user']
                
                if not os.path.exists(kb_path):
                    continue
                
                # 添加知识库信息到批量信息
                batch_info['knowledge_bases'].append({
                    'name': kb_name,
                    'user': user,
                    'path': kb_path
                })
                
                # 创建知识库文件夹
                kb_folder = f"{user.replace(' ', '_')}/{kb_name}/"
                
                # 添加向量数据
                if options.get('vectors', True):
                    for root, dirs, files in os.walk(kb_path):
                        for file in files:
                            if file.endswith(('.bin', '.pkl', '.index', '.faiss')):
                                file_path = os.path.join(root, file)
                                arc_path = kb_folder + "vectors/" + os.path.relpath(file_path, kb_path)
                                zip_file.write(file_path, arc_path)
                
                # 添加原始文档
                if options.get('documents', True):
                    docs_path = kb_path.replace('vector_db_storage', 'uploaded_files')
                    if os.path.exists(docs_path):
                        for root, dirs, files in os.walk(docs_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arc_path = kb_folder + "documents/" + os.path.relpath(file_path, docs_path)
                                zip_file.write(file_path, arc_path)
                
                # 添加配置文件
                if options.get('configs', True):
                    config_files = ['manifest.json', 'config.json', 'settings.json']
                    for config_file in config_files:
                        config_path = os.path.join(kb_path, config_file)
                        if os.path.exists(config_path):
                            zip_file.write(config_path, kb_folder + f"configs/{config_file}")
                
                # 添加元数据
                if options.get('metadata', True):
                    metadata_path = os.path.join(kb_path, 'metadata.json')
                    if os.path.exists(metadata_path):
                        zip_file.write(metadata_path, kb_folder + "metadata.json")
            
            # 添加批量下载信息文件
            zip_file.writestr("batch_info.json", json.dumps(batch_info, indent=2, ensure_ascii=False))
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
        
    except Exception as e:
        st.error(f"打包过程中出现错误: {str(e)}")
        return None

def show_data_management():
    """数据管理"""
    st.markdown("#### 🗂️ 数据管理")
    
    st.warning("⚠️ 危险操作，请谨慎使用")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧹 清理临时文件"):
            # 清理临时上传文件
            temp_path = "temp_uploads"
            if os.path.exists(temp_path):
                for file in os.listdir(temp_path):
                    file_path = os.path.join(temp_path, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        st.error(f"清理失败: {e}")
                st.success("✅ 临时文件清理完成")
    
    with col2:
        if st.button("👤 清理游客数据"):
            # 清理所有游客数据
            cleaned_count = 0
            for storage_dir in ["vector_db_storage", "chat_histories", "temp_uploads"]:
                if os.path.exists(storage_dir):
                    for item in os.listdir(storage_dir):
                        if item.startswith("guest_"):
                            item_path = os.path.join(storage_dir, item)
                            try:
                                if os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                                    cleaned_count += 1
                            except Exception as e:
                                st.error(f"清理游客数据失败: {e}")
            
            if cleaned_count > 0:
                st.success(f"✅ 已清理 {cleaned_count} 个游客数据目录")
            else:
                st.info("ℹ️ 没有找到游客数据")

def cleanup_user_data(username: str):
    """清理用户数据"""
    # 清理用户知识库
    user_kb_path = f"vector_db_storage/{username}"
    if os.path.exists(user_kb_path):
        shutil.rmtree(user_kb_path)
    
    # 清理用户对话历史
    user_chat_path = f"chat_histories/{username}"
    if os.path.exists(user_chat_path):
        shutil.rmtree(user_chat_path)
