import streamlit as st
import os
import json
import time
from src.auth.user_auth import load_users, save_users
from src.auth.session_manager import load_sharing_config, save_sharing_config, set_kb_public
from src.kb.kb_manager import KBManager

USER_CONFIG_PATH = "config/users.json"
ROLE_TEMPLATE_PATH = "config/role_templates.json"

def render_admin_management():
    st.markdown("### 👥 系统用户与资源调度")
    
    users = load_users()
    sharing_config = load_sharing_config()
    
    # [v4.5.2 核心增强] 物理一致性实时审计器
    kb_storage_root = os.path.join(os.getcwd(), "vector_db_storage")
    physical_kbs = set()
    if os.path.exists(kb_storage_root):
        physical_kbs = {d for d in os.listdir(kb_storage_root) if os.path.isdir(os.path.join(kb_storage_root, d)) and not d.startswith('.')}
    
    # 自动修复 sharing_config
    original_public_count = len(sharing_config.get("public_kbs", []))
    sharing_config["public_kbs"] = [kb for kb in sharing_config.get("public_kbs", []) if kb in physical_kbs]
    
    # 自动修复 role_sharing
    for role in sharing_config.get("role_sharing", {}):
        sharing_config["role_sharing"][role] = [kb for kb in sharing_config["role_sharing"][role] if kb in physical_kbs]
    
    # 自动修复用户白名单 (kb_whitelist)
    users_modified = False
    for username in users:
        if "kb_whitelist" in users[username]:
            orig_list = users[username]["kb_whitelist"]
            new_list = [kb for kb in orig_list if kb in physical_kbs]
            if len(orig_list) != len(new_list):
                users[username]["kb_whitelist"] = new_list
                users_modified = True
    
    # 如果检测到差异，执行静默修复
    if len(sharing_config.get("public_kbs", [])) != original_public_count or users_modified:
        save_sharing_config(sharing_config)
        if users_modified: save_users(users)
        st.toast("🧹 已自动清理消失的物理知识库关联记录", icon="🧼")

    public_kbs = sharing_config.get("public_kbs", [])
    
    # 提前加载角色配置，供各标签页共享
    if os.path.exists(ROLE_TEMPLATE_PATH):
        with open(ROLE_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            roles_config = json.load(f)
    else:
        roles_config = {}
    
    # 1. 顶部统计
    s_col1, s_col2, s_col3 = st.columns(3)
    s_col1.metric("总注册用户", len(users))
    s_col2.metric("公开知识库", len(public_kbs))
    s_col3.metric("管理员", len([u for u in users.values() if u.get('role')=='admin']))
    
    st.divider()
    
    tab_batch, tab_users, tab_kbs, tab_assets, tab_roles, tab_sessions, tab_audit = st.tabs(["⚡ 批量授权", "👤 用户台账", "📂 知识库分发", "🗄️ 资产全览", "🎭 角色定义", "🍪 会话控制", "📜 审计记录"])
    
    with tab_batch:
        st.caption("一键管理多名用户的权限与访问权")
        non_admin_users = [u for u in users.keys() if users[u].get('role') != 'admin']
        
        if not non_admin_users:
            st.info("当前暂无可管理的非管理员用户")
        else:
            col_sel, col_act = st.columns([2, 3])
            with col_sel:
                selected_batch_users = st.multiselect("第一步：选择目标用户", options=non_admin_users, help="可搜索并勾选多名用户")
                if st.checkbox("全选所有用户"):
                    selected_batch_users = non_admin_users
            
            with col_act:
                batch_action = st.selectbox("第二步：选择批量操作", ["--- 请选择 ---", "批量赋予访问权", "批量封禁账号", "批量解封账号", "批量变更为访客"])
                
                if batch_action != "--- 请选择 ---" and selected_batch_users:
                    if batch_action == "批量赋予访问权":
                        kb_manager = KBManager()
                        kb_manager.base_path = os.path.join(os.getcwd(), "vector_db_storage")
                        all_kbs = kb_manager.list_all()
                        target_kbs = st.multiselect("第三步：选择要分享的知识库", options=all_kbs)
                        
                        if st.button("🔥 执行批量授权", type="primary"):
                            from src.auth.audit_logger import AuditLogger
                            for u in selected_batch_users:
                                current_white = set(users[u].get('kb_whitelist', []))
                                users[u]['kb_whitelist'] = list(current_white.union(set(target_kbs)))
                            save_users(users)
                            AuditLogger.log(st.session_state.get('user'), "BATCH_AUTH", f"为 {len(selected_batch_users)} 名用户批量授权知识库: {', '.join(target_kbs)}", ip=get_client_ip())
                            st.success(f"已成功为 {len(selected_batch_users)} 名用户授权")
                            time.sleep(1); st.rerun()
                            
                    elif batch_action == "批量封禁账号":
                        if st.button("🔒 立即执行封禁", type="secondary"):
                            from src.auth.audit_logger import AuditLogger
                            for u in selected_batch_users:
                                users[u]['is_active'] = False
                            save_users(users)
                            AuditLogger.log(st.session_state.get('user'), "BATCH_LOCK", f"批量封禁了 {len(selected_batch_users)} 名用户", ip=get_client_ip())
                            st.toast("账号已批量封禁")
                            time.sleep(1); st.rerun()

    with tab_sessions:
        st.caption("管理用户登录会话的有效期与强制下线策略")
        from src.auth.session_manager import get_session_settings, set_session_setting, revoke_user_sessions
        
        settings = get_session_settings()
        
        # 1. 全局策略
        with st.container(border=True):
            st.markdown("**🌍 全局会话策略**")
            global_days = settings.get("global_default", 7)
            new_global = st.number_input("默认登录保持天数", min_value=1, max_value=365, value=global_days, help="所有用户的默认设置")
            if st.button("保存全局设置"):
                set_session_setting("global_default", new_global)
                st.success("全局策略已更新")
                time.sleep(1); st.rerun()
                
        # 2. 用户级策略
        with st.container(border=True):
            st.markdown("**👤 用户级特权设置**")
            target_user = st.selectbox("选择用户", [u for u in users.keys()])
            current_user_days = settings.get(target_user, global_days)
            
            c1, c2 = st.columns([2, 1])
            with c1:
                new_user_days = st.number_input(f"设置 {target_user} 的保持天数", min_value=1, max_value=365, value=current_user_days)
            with c2:
                st.write("") # Spacer
                if st.button("应用到该用户"):
                    set_session_setting(target_user, new_user_days)
                    st.success(f"{target_user} 的设置已更新")
                    time.sleep(1); st.rerun()
            
            st.divider()
            
            # 3. 强制操作
            st.markdown("**🚨 风险操作**")
            if st.button(f"强制注销 {target_user} 的所有会话", type="primary"):
                count = revoke_user_sessions(target_user)
                st.success(f"已清除 {count} 个有效会话，用户下次需重新登录")

    with tab_users:
        st.caption("管理账号生命周期、角色及存储配额")
        from src.auth.session_manager import get_user_storage_usage, format_size
        
        for username, info in users.items():
            with st.expander(f"{'🟢' if info.get('is_active', True) else '🔴'} {username} - {info.get('role')}"):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    # 动态加载角色选项
                    role_options = list(roles_config.keys())
                    current_role = info.get('role', 'standard_user')
                    try:
                        role_idx = role_options.index(current_role)
                    except: role_idx = 0
                    
                    new_role = st.selectbox("角色修改", role_options, 
                                            index=role_idx,
                                            format_func=lambda x: f"{roles_config[x]['name']} ({x})",
                                            key=f"role_{username}")
                with c2:
                    current_quota = info.get("storage_quota_mb", 100)
                    new_quota = st.number_input("存储配额 (MB)", min_value=-1, value=int(current_quota), key=f"quota_{username}")
                
                used_bytes = get_user_storage_usage(username)
                used_mb = used_bytes / (1024 * 1024)
                
                if current_quota > 0:
                    usage_pct = min(used_mb / current_quota, 1.0)
                    st.progress(usage_pct, text=f"空间占用: {format_size(used_bytes)} / {current_quota} MB")
                else:
                    st.caption(f"空间占用: {format_size(used_bytes)} (无限)")

                is_active = st.toggle("允许登录", value=info.get('is_active', True), key=f"active_{username}")
                
                if new_role != info.get('role') or is_active != info.get('is_active') or new_quota != current_quota:
                    users[username]['role'] = new_role
                    users[username]['is_active'] = is_active
                    users[username]['storage_quota_mb'] = new_quota
                    save_users(users)
                    st.toast(f"✅ {username} 配置已更新")
                    st.rerun()

    with tab_kbs:
        st.caption("资源调度中心：批量控制知识库的可见性与共享范围")
        
        # 获取基础数据
        kb_manager = KBManager()
        kb_manager.base_path = os.path.join(os.getcwd(), "vector_db_storage")
        all_kbs = kb_manager.list_all()
        
        if not all_kbs:
            st.info("当前暂无物理知识库可供分发")
        else:
            # --- 顶部批量操作栏 ---
            with st.container(border=True):
                st.markdown("**⚡ 批量分发工具栏**")
                col_kb_sel, col_role_sel, col_user_sel = st.columns([2, 1.5, 1.5])
                
                with col_kb_sel:
                    selected_kbs = st.multiselect("1. 勾选目标知识库", options=all_kbs, help="支持多选")
                    if st.checkbox("全选所有物理库", key="all_kb_check"):
                        selected_kbs = all_kbs
                
                with col_role_sel:
                    target_roles = st.multiselect("2. 授权给角色 (可选)", options=list(roles_config.keys()))
                
                with col_user_sel:
                    target_users_list = st.multiselect("3. 授权给用户 (可选)", options=[u for u in users.keys() if users[u].get('role')!='admin'])

                # 执行批量按钮
                if selected_kbs:
                    b_col1, b_col2, b_col3 = st.columns(3)
                    with b_col1:
                        if st.button("🌍 设为全系统公开", use_container_width=True, type="primary"):
                            for kb in selected_kbs:
                                set_kb_public(kb, True)
                            st.success(f"已公开 {len(selected_kbs)} 个库")
                            time.sleep(1); st.rerun()
                    with b_col2:
                        if st.button("🤝 执行精准授权", use_container_width=True):
                            # 更新角色共享
                            sharing_conf = load_sharing_config()
                            for r in target_roles:
                                r_list = set(sharing_conf.get('role_sharing', {}).get(r, []))
                                sharing_conf['role_sharing'][r] = list(r_list.union(set(selected_kbs)))
                            save_sharing_config(sharing_conf)
                            
                            # 更新用户白名单
                            for u in target_users_list:
                                u_white = set(users[u].get('kb_whitelist', []))
                                users[u]['kb_whitelist'] = list(u_white.union(set(selected_kbs)))
                            save_users(users)
                            
                            st.success("批量授权已下发")
                            time.sleep(1); st.rerun()
                    with b_col3:
                        if st.button("🔒 设为私有/取消全部分享", use_container_width=True):
                            # 移除公开
                            sharing_conf = load_sharing_config()
                            for kb in selected_kbs:
                                if kb in sharing_conf.get('public_kbs', []):
                                    sharing_conf['public_kbs'].remove(kb)
                                # 移除角色分享
                                for r in sharing_conf.get('role_sharing', {}):
                                    if kb in sharing_conf['role_sharing'][r]:
                                        sharing_conf['role_sharing'][r].remove(kb)
                            save_sharing_config(sharing_conf)
                            
                            # 移除用户分享
                            for u in users:
                                if users[u].get('kb_whitelist'):
                                    for kb in selected_kbs:
                                        if kb in users[u]['kb_whitelist']:
                                            users[u]['kb_whitelist'].remove(kb)
                            save_users(users)
                            st.toast("已重置选中库的访问权限")
                            time.sleep(1); st.rerun()

            # --- 下方明细列表 ---
            st.markdown("**📂 资源明细状态**")
            for kb in all_kbs:
                is_public = kb in sharing_config.get("public_kbs", [])
                # 获取该库被哪些角色共享
                shared_roles = [r for r, kbs in sharing_config.get("role_sharing", {}).items() if kb in kbs]
                
                with st.expander(f"📂 {kb} {' (🌍公开)' if is_public else ' (🛡️已授权)' if shared_roles else ' (🔒私有)'}"):
                    st.write(f"**公开状态**: {'✅ 已公开' if is_public else '❌ 私有'}")
                    if shared_roles:
                        st.write(f"**已授权角色**: {', '.join([roles_config[r]['name'] for r in shared_roles])}")
                    
                    # 单独细调逻辑保留...
                    if st.button(f"重置该库权限", key=f"reset_{kb}"):
                        # 复用上面的单库重置逻辑
                        pass

    with tab_assets:
        st.caption("知识库全资产画像：深度审计所有物理存储与元数据模型")
        from src.config.manifest_manager import ManifestManager
        import pandas as pd
        from datetime import datetime
        from src.auth.session_manager import format_size

        # 1. 深度扫描与数据准备
        asset_data = []
        for kb in all_kbs:
            kb_path = os.path.join(kb_storage_root, kb)
            manifest = ManifestManager.load(kb_path)
            
            # 计算物理大小
            total_size = 0
            file_count = 0
            try:
                for root, dirs, files in os.walk(kb_path):
                    for f in files:
                        total_size += os.path.getsize(os.path.join(root, f))
                        file_count += 1
            except: pass
            
            # 获取时间
            c_time_val = manifest.get('created_at')
            c_date = datetime.now().date()
            c_time_str = "未知"
            
            try:
                if c_time_val:
                    if isinstance(c_time_val, (int, float)):
                        dt = datetime.fromtimestamp(c_time_val)
                        c_date = dt.date()
                        c_time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    elif isinstance(c_time_val, str):
                        # 尝试解析字符串格式
                        try:
                            dt = datetime.strptime(c_time_val[:19], '%Y-%m-%d %H:%M:%S')
                        except:
                            try:
                                dt = datetime.fromisoformat(c_time_val)
                            except:
                                dt = datetime.now()
                        c_date = dt.date()
                        c_time_str = c_time_val
                else:
                    # Fallback: 使用目录创建时间
                    try:
                        stat = os.stat(kb_path)
                        # 在Unix上 st_ctime 可能是元数据变更时间，st_birthtime 是创建时间(macOS)
                        # 为了跨平台，优先用 st_birthtime (if available), else st_ctime
                        ts = getattr(stat, 'st_birthtime', stat.st_ctime)
                        dt = datetime.fromtimestamp(ts)
                        c_date = dt.date()
                        c_time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        pass
            except Exception:
                pass

            asset_data.append({
                "☑️ 选择": False,
                "知识库名称": kb,
                "所有人": manifest.get('owner', 'admin'),
                "文件数": file_count,
                "存储占用": total_size,
                "格式化大小": format_size(total_size),
                "创建日期": c_date,
                "完整时间": c_time_str
            })

        df_assets = pd.DataFrame(asset_data)

        # 2. 筛选矩阵
        with st.container(border=True):
            f_col1, f_col2, f_col3 = st.columns([1.5, 2, 1.5])
            with f_col1:
                u_filter = st.multiselect("👤 按所有人筛选", options=df_assets['所有人'].unique())
            with f_col2:
                d_filter = st.date_input("📅 按创建时间段筛选", value=(df_assets['创建日期'].min(), df_assets['创建日期'].max()))
            with f_col3:
                k_filter = st.text_input("🔍 搜索名称/所有人", placeholder="如: 外贸")

        # 应用筛选逻辑
        filtered_df = df_assets.copy()
        if u_filter:
            filtered_df = filtered_df[filtered_df['所有人'].isin(u_filter)]
        if len(d_filter) == 2:
            filtered_df = filtered_df[(filtered_df['创建日期'] >= d_filter[0]) & (filtered_df['创建日期'] <= d_filter[1])]
        if k_filter:
            filtered_df = filtered_df[filtered_df['知识库名称'].str.contains(k_filter, case=False) | filtered_df['所有人'].str.contains(k_filter, case=False)]

        # 3. 结果展示与批量操作
        if filtered_df.empty:
            st.warning("未找到匹配的知识库资产")
        else:
            # 统计栏
            st.info(f"📊 筛选结果: {len(filtered_df)} 个库 | 总占用: {format_size(filtered_df['存储占用'].sum())}")
            
            # 利用 st.data_editor 实现多选
            edited_df = st.data_editor(
                filtered_df[["☑️ 选择", "知识库名称", "所有人", "文件数", "格式化大小", "创建日期"]],
                use_container_width=True,
                hide_index=True,
                disabled=["知识库名称", "所有人", "文件数", "格式化大小", "创建日期"],
                key="asset_editor"
            )

            # 批量操作逻辑
            selected_to_delete = edited_df[edited_df["☑️ 选择"] == True]["知识库名称"].tolist()
            
            if selected_to_delete:
                st.divider()
                st.markdown(f"**⚡ 批量操作 ({len(selected_to_delete)} 项)**")
                
                # 操作类型选择
                batch_op_type = st.radio("选择批量操作类型", ["👤 移交所有权", "🗑️ 物理删除"], horizontal=True, label_visibility="collapsed")
                
                if batch_op_type == "👤 移交所有权":
                    c_trans1, c_trans2 = st.columns([2, 1])
                    with c_trans1:
                        target_new_owner = st.selectbox("选择新所有者", options=list(users.keys()), key="batch_new_owner_sel")
                    with c_trans2:
                        if st.button("➡️ 确认移交", type="primary", use_container_width=True):
                            from src.auth.audit_logger import AuditLogger
                            success_cnt = 0
                            for kb_name in selected_to_delete:
                                try:
                                    kb_path = os.path.join(kb_storage_root, kb_name)
                                    manifest = ManifestManager.load(kb_path)
                                    old_owner = manifest.get('owner', 'unknown')
                                    manifest['owner'] = target_new_owner
                                    
                                    # 保存 Manifest
                                    mf_path = os.path.join(kb_path, "manifest.json")
                                    with open(mf_path, 'w', encoding='utf-8') as f:
                                        json.dump(manifest, f, indent=4, ensure_ascii=False)
                                    
                                    # 自动更新白名单（如果旧用户有白名单，可能需要处理，这里简化为只改所有权）
                                    success_cnt += 1
                                    AuditLogger.log(st.session_state.get('user'), "BATCH_TRANSFER", f"将 {kb_name} 所有权从 {old_owner} 移交给 {target_new_owner}", ip=get_client_ip())
                                except Exception as e:
                                    st.error(f"{kb_name} 移交失败: {e}")
                            
                            st.success(f"✅ 已成功移交 {success_cnt} 个知识库")
                            time.sleep(1); st.rerun()

                elif batch_op_type == "🗑️ 物理删除":
                    st.warning(f"⚠️ 警告：即将物理删除 {len(selected_to_delete)} 个知识库及其所有关联数据（不可恢复）！")
                    if st.button("🚨 确认批量物理删除", type="primary", use_container_width=True):
                        from src.kb.kb_processor import KBProcessor
                        from src.auth.audit_logger import AuditLogger
                        
                        with st.status(f"正在深度清理 {len(selected_to_delete)} 个资产...") as status:
                            for target_kb in selected_to_delete:
                                st.write(f"正在清除: {target_kb}")
                                # 1. 物理目录删除
                                target_path = os.path.join(kb_storage_root, target_kb)
                                if os.path.exists(target_path):
                                    import shutil
                                    shutil.rmtree(target_path)
                                
                                # 2. 对话历史删除
                                hist_file = os.path.join("chat_histories", f"{target_kb}.json")
                                if os.path.exists(hist_file): os.remove(hist_file)
                                
                                # 3. 推荐配置删除
                                sug_file = os.path.join("suggestion_config", f"{target_kb}_config.json")
                                if os.path.exists(sug_file): os.remove(sug_file)
                                
                                AuditLogger.log(st.session_state.get('user'), "BATCH_DELETE_KB", f"物理删除了知识库: {target_kb}", ip=get_client_ip())
                            
                            status.update(label="✅ 资产批量清理完成", state="complete")
                        
                        time.sleep(1); st.rerun()

    with tab_roles:
        st.caption("角色权限中台：定义角色的底层功能矩阵与默认资源配额")
        
        ALL_PERMISSIONS_MAP = {
            "chat": "🗨️ 基础对话", 
            "kb_create": "➕ 创建库", 
            "kb_delete_own": "🗑️ 删除个人库",
            "kb_rename": "✏️ 重命名库",
            "kb_rebuild_index": "🔄 重建索引",
            "upload_files": "📤 上传文件", 
            "paste_text": "📝 粘贴文本", 
            "use_crawler": "🌐 网页爬虫",
            "smart_search": "🔍 联网搜索", 
            "deep_research": "🧠 深度研究",
            "data_analysis": "📊 数据分析",
            "summary_gen": "✨ AI 摘要", 
            "download_knowledge_base": "📥 资产下载",
            "kb_export_report": "📝 导出报告",
            "kb_export_full": "🏗️ 全量镜像",
            "kb_filesystem_access": "📂 系统访问",
            "manage_system_config": "🛠️ 系统配置",
            "view_stats": "📊 查看监控"
        }
        
        # 布局：左侧角色列表，右侧编辑器
        role_col1, role_col2 = st.columns([1, 2])
        
        with role_col1:
            st.markdown("**现有角色**")
            # 按钮样式的角色选择
            selected_role_id = st.radio("选择要编辑的角色", list(roles_config.keys()), 
                                        format_func=lambda x: f"{roles_config[x]['name']} ({x})",
                                        label_visibility="collapsed")
            
            st.divider()
            # ➕ 新增角色表单
            with st.expander("➕ 新增自定义角色"):
                new_role_id = st.text_input("角色ID (字母)", placeholder="如: auditor")
                new_role_name = st.text_input("显示名称", placeholder="如: 审计员")
                if st.button("立即创建角色", use_container_width=True):
                    if new_role_id and new_role_name:
                        if new_role_id not in roles_config:
                            roles_config[new_role_id] = {
                                "name": new_role_name,
                                "description": "自定义角色",
                                "permissions": ["chat"],
                                "default_quota_mb": 100
                            }
                            with open(ROLE_TEMPLATE_PATH, 'w', encoding='utf-8') as f:
                                json.dump(roles_config, f, indent=4, ensure_ascii=False)
                            st.success(f"角色 {new_role_name} 创建成功")
                            st.rerun()
                        else: st.error("角色ID已存在")
                    else: st.warning("请填全信息")

        with role_col2:
            target_role = roles_config[selected_role_id]
            st.markdown(f"#### 🛠️ 编辑角色: {target_role['name']}")
            
            with st.container(border=True):
                # 1. 基础描述
                new_desc = st.text_input("角色描述", value=target_role.get('description', ''))
                
                # 2. 配额设置
                new_default_quota = st.number_input("默认存储配额 (MB)", min_value=-1, value=int(target_role.get('default_quota_mb', 100)), help="-1 表示无限")
                
                # 3. 权限矩阵
                st.markdown("**功能权限位:**")
                current_perms = target_role.get("permissions", [])
                
                new_perms_list = []
                p_cols = st.columns(2)
                for i, (p_id, p_name) in enumerate(ALL_PERMISSIONS_MAP.items()):
                    with p_cols[i % 2]:
                        # 如果是管理员且为 * 权限，强制勾选
                        is_checked = (p_id in current_perms or "*" in current_perms)
                        if st.checkbox(p_name, value=is_checked, key=f"p_edit_{selected_role_id}_{p_id}", disabled=(selected_role_id=="admin")):
                            new_perms_list.append(p_id)
                
                # 4. 保存与删除
                st.write("")
                save_c1, save_c2 = st.columns([2, 1])
                with save_c1:
                    if st.button("💾 保存该角色配置", use_container_width=True, type="primary"):
                        roles_config[selected_role_id]["description"] = new_desc
                        roles_config[selected_role_id]["default_quota_mb"] = new_default_quota
                        roles_config[selected_role_id]["permissions"] = new_perms_list
                        with open(ROLE_TEMPLATE_PATH, 'w', encoding='utf-8') as f:
                            json.dump(roles_config, f, indent=4, ensure_ascii=False)
                        st.success("配置已保存")
                        st.rerun()
                with save_c2:
                    # 保护内置角色不被删除
                    if selected_role_id not in ["admin", "standard_user", "guest"]:
                        if st.button("🗑️ 删除角色", use_container_width=True):
                            del roles_config[selected_role_id]
                            with open(ROLE_TEMPLATE_PATH, 'w', encoding='utf-8') as f:
                                json.dump(roles_config, f, indent=4, ensure_ascii=False)
                            st.rerun()

    with tab_audit:
        from src.auth.audit_logger import AuditLogger
        from src.common.utils import get_client_ip
        st.caption("系统审计日志：追踪所有关键操作、访问来源与执行状态")
        
        raw_logs = AuditLogger.get_logs()
        if not raw_logs:
            st.info("暂无审计记录")
        else:
            # 1. 筛选矩阵
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                with c1:
                    u_list = sorted(list(set(l['user'] for l in raw_logs)))
                    sel_users = st.multiselect("👤 操作人", options=u_list)
                with c2:
                    a_list = sorted(list(set(l['action'] for l in raw_logs)))
                    sel_actions = st.multiselect("⚡ 动作类型", options=a_list)
                with c3:
                    sel_status = st.multiselect("🚦 状态", options=["success", "failed", "warning"])

            # 过滤逻辑
            filtered_logs = raw_logs
            if sel_users:
                filtered_logs = [l for l in filtered_logs if l['user'] in sel_users]
            if sel_actions:
                filtered_logs = [l for l in filtered_logs if l['action'] in sel_actions]
            if sel_status:
                filtered_logs = [l for l in filtered_logs if l.get('status', 'success') in sel_status]

            # 2. 统计概览与全局操作
            col_stat, col_clear = st.columns([3, 1])
            with col_stat:
                st.info(f"📊 匹配结果: {len(filtered_logs)} 条记录")
            with col_clear:
                if st.button("🗑️ 清空所有审计", use_container_width=True, type="secondary", help="永久删除所有审计日志文件"):
                    if AuditLogger.clear_logs():
                        st.toast("✅ 审计日志已清空")
                        time.sleep(0.5); st.rerun()

            # 3. 渲染记录
            for l in filtered_logs[:100]: # 限制显示前100条
                status_color = "#10b981" if l.get('status') == 'success' else "#ef4444" if l.get('status') == 'failed' else "#f59e0b"
                ts = l.get('timestamp', '')
                
                with st.container(border=True):
                    header_col1, header_col2, header_col3 = st.columns([3, 1, 0.3])
                    with header_col1:
                        st.markdown(f"**{l['action']}** | `{l['user']}`")
                    with header_col2:
                        st.markdown(f"<div style='text-align:right; font-size:0.8rem; color:#666;'>{ts[:19].replace('T', ' ')}</div>", unsafe_allow_html=True)
                    with header_col3:
                        if st.button("❌", key=f"del_audit_{ts}", help="删除此条记录"):
                            if AuditLogger.delete_log(ts):
                                st.rerun()
                    
                    st.caption(l['details'])
                    
                    footer_col1, header_col2 = st.columns([2, 1])
                    with footer_col1:
                        ip_val = l.get('ip', 'unknown')
                        st.markdown(f"<span style='font-size:0.75rem; color:#999;'>🌐 IP: {ip_val}</span>", unsafe_allow_html=True)
                    with header_col2:
                        st.markdown(f"<div style='text-align:right; font-size:0.75rem; color:{status_color}; font-weight:bold;'>{l.get('status', 'success').upper()}</div>", unsafe_allow_html=True)