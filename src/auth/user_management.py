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
    
    tab_batch, tab_users, tab_kbs, tab_assets, tab_roles, tab_audit = st.tabs(["⚡ 批量授权", "👤 用户台账", "📂 知识库分发", "🗄️ 资产全览", "🎭 角色定义", "📜 审计记录"])
    
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
                            AuditLogger.log(st.session_state.get('user'), "BATCH_AUTH", f"为 {len(selected_batch_users)} 名用户批量授权知识库: {', '.join(target_kbs)}")
                            st.success(f"已成功为 {len(selected_batch_users)} 名用户授权")
                            time.sleep(1); st.rerun()
                            
                    elif batch_action == "批量封禁账号":
                        if st.button("🔒 立即执行封禁", type="secondary"):
                            from src.auth.audit_logger import AuditLogger
                            for u in selected_batch_users:
                                users[u]['is_active'] = False
                            save_users(users)
                            AuditLogger.log(st.session_state.get('user'), "BATCH_LOCK", f"批量封禁了 {len(selected_batch_users)} 名用户")
                            st.toast("账号已批量封禁")
                            time.sleep(1); st.rerun()

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
            c_time_raw = manifest.get('created_at', '2025-01-01 00:00:00')
            try:
                c_date = datetime.strptime(c_time_raw[:10], '%Y-%m-%d').date()
            except: c_date = datetime.now().date()

            asset_data.append({
                "☑️ 选择": False,
                "知识库名称": kb,
                "所有人": manifest.get('owner', 'admin'),
                "文件数": file_count,
                "存储占用": total_size,
                "格式化大小": format_size(total_size),
                "创建日期": c_date,
                "完整时间": c_time_raw
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
                            
                            AuditLogger.log(st.session_state.get('user'), "BATCH_DELETE_KB", f"物理删除了知识库: {target_kb}")
                        
                        status.update(label="✅ 资产批量清理完成", state="complete")
                    
                    time.sleep(1); st.rerun()

    with tab_roles:
        st.caption("角色权限中台：定义角色的底层功能矩阵与默认资源配额")
        
        all_perms = {
            "chat": "🗨️ 基础对话", 
            "kb_create": "➕ 创建库", 
            "kb_delete_own": "🗑️ 删除个人库",
            "upload_files": "📤 上传文件", 
            "paste_text": "📝 粘贴文本", 
            "use_crawler": "🌐 网页爬虫",
            "smart_search": "🔍 联网搜索", 
            "summary_gen": "✨ AI 摘要", 
            "kb_export_full": "🏗️ 全量镜像",
            "kb_export_report": "📝 导出报告",
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
                for i, (p_id, p_name) in enumerate(all_perms.items()):
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
        st.caption("系统审计日志")
        logs = AuditLogger.get_logs()
        for l in logs[:50]:
            with st.container(border=True):
                st.markdown(f"**{l['action']}** | `{l['user']}` | {l['timestamp'][:19]}")
                st.caption(l['details'])