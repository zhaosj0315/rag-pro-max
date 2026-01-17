import streamlit as st
import os
import json
import time
import pandas as pd
from datetime import datetime
from src.auth.user_auth import load_users, save_users
from src.auth.session_manager import load_sharing_config, save_sharing_config, set_kb_public
from src.kb.kb_manager import KBManager

USER_CONFIG_PATH = "config/users.json"
ROLE_TEMPLATE_PATH = "config/role_templates.json"

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

def render_resource_governance_v10():
    st.toast("已加载增强版资源矩阵 v10 (时间探测加固)", icon="🕒")
    from src.auth.audit_logger import AuditLogger
    st.markdown("### 👥 系统用户与资源调度")
    
    users = load_users()
    sharing_config = load_sharing_config()
    
    if os.path.exists(ROLE_TEMPLATE_PATH):
        with open(ROLE_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            roles_config = json.load(f)
    else:
        roles_config = {}

    kb_manager = KBManager()
    kb_manager.base_path = os.path.join(os.getcwd(), "vector_db_storage")
    all_kbs = kb_manager.list_all()
    
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    s_col1.metric("总注册用户", len(users))
    s_col2.metric("公开知识库", len(sharing_config.get("public_kbs", [])))
    s_col3.metric("总物理资产", len(all_kbs))
    s_col4.metric("自定义角色", len(roles_config))
    
    st.divider()
    
    tab_dist, tab_users, tab_roles, tab_audit, tab_term = st.tabs([
        "🛡️ 资源治理", "👤 用户与会话", "🎭 角色定义", "📜 行为审计", "💻 终端控制"
    ])
    
    # --- Tab 1: 资源治理 (融合版) ---
    with tab_dist:
        st.caption("全域资源控制台：统一管理知识库的物理生命周期与访问权限")
        
        # --- 资源矩阵模式 (原 资源视角 + 资产全览) ---
        from src.config.manifest_manager import ManifestManager
        import datetime
        kb_storage_root = os.path.join(os.getcwd(), "vector_db_storage")
        
        # 1. 构建详细资产数据
        asset_data = []
        for kb in all_kbs:
            # 物理信息
            kb_path = os.path.join(kb_storage_root, kb)
            manifest = ManifestManager.load(kb_path)
            
            total_size = 0
            file_count = 0
            doc_count = 0
            last_modified = 0
            
            try:
                for root, _, files in os.walk(kb_path):
                    for f in files:
                        fp = os.path.join(root, f)
                        total_size += os.path.getsize(fp)
                        file_count += 1
                        mtime = os.path.getmtime(fp)
                        if mtime > last_modified: last_modified = mtime
                        if f.endswith(('.pdf', '.docx', '.txt', '.md', '.csv', '.xlsx', '.pptx')):
                            doc_count += 1
            except: pass
            
            # 时间格式化 (v6.8.9 增强版：多级嗅探)
            created_raw = manifest.get('created_time') or manifest.get('created_at') or manifest.get('added_at')
            created_str = '未知'
            
            if created_raw:
                try:
                    # 尝试解析 ISO 格式 (处理 T, Z 等分隔符)
                    iso_str = str(created_raw).replace('Z', '').split('.')[0] # 移除毫秒位
                    if 'T' in iso_str:
                        dt = datetime.datetime.fromisoformat(iso_str)
                    else:
                        dt = datetime.datetime.strptime(iso_str, '%Y-%m-%d %H:%M:%S')
                    created_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    # 字符串截取保底 (YYYY-MM-DD HH:MM)
                    created_str = str(created_raw).replace('T', ' ')[:16]
            
            # 如果依然未知，使用物理文件夹创建时间保底
            if created_str == '未知' or not created_str:
                try:
                    ctime = os.path.getctime(kb_path)
                    created_str = datetime.datetime.fromtimestamp(ctime).strftime('%Y-%m-%d %H:%M')
                except:
                    created_str = '未知'

            last_mod_str = datetime.datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M') if last_modified > 0 else "无记录"

            # 类型推断
            kb_type = "📚 文档库"
            if "web" in kb.lower() or "crawl" in kb.lower(): kb_type = "🌐 网页库"
            elif "chat" in kb.lower(): kb_type = "💬 对话库"

            # 权限信息
            is_public = kb in sharing_config.get("public_kbs", [])
            shared_roles = [r for r, kbs in sharing_config.get('role_sharing', {}).items() if kb in kbs]
            shared_users = [u for u, info in users.items() if kb in info.get('kb_whitelist', [])]
            
            status_tags = []
            if is_public: status_tags.append("🌐 公开")
            if shared_roles: status_tags.append(f"🎭 {len(shared_roles)}角色")
            if shared_users: status_tags.append(f"👤 {len(shared_users)}用户")
            if not status_tags: status_tags.append("🔒 私有")

            asset_data.append({
                "☑️": False, # 默认不选中
                "知识库名称": kb,
                "类型": kb_type,
                "所有人": manifest.get('owner', 'admin'),
                "创建时间": created_str,
                "最后修改": last_mod_str,
                "权限状态": " | ".join(status_tags),
                "文档数": doc_count,
                "占用空间": format_size(total_size),
                "描述": manifest.get('description', '')
            })

        # 2. 筛选器
        with st.container(border=True):
            st.markdown("**🔍 资源精准筛选**")
            fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
            search_q = fc1.text_input("按名称搜索", placeholder="输入关键词...", key="res_search_q")
            all_owners = sorted(list(set([d['所有人'] for d in asset_data]))) if asset_data else []
            owner_f = fc2.multiselect("按所有人过滤", options=all_owners, key="res_owner_f")
            status_f = fc3.multiselect("按权限过滤", ["🌐 公开", "🔒 私有", "已分享"], key="res_status_f")
            type_f = fc4.multiselect("按类型过滤", ["📚 文档库", "🌐 网页库", "💬 对话库"], key="res_type_f")
            
            # 筛选状态提示
            active_filters = []
            if search_q: active_filters.append(f"名称包含 '{search_q}'")
            if owner_f: active_filters.append(f"所有人: {', '.join(owner_f)}")
            if status_f: active_filters.append(f"权限: {', '.join(status_f)}")
            if type_f: active_filters.append(f"类型: {', '.join(type_f)}")
            
            if active_filters:
                st.caption(f"⚡ 当前生效筛选: {' + '.join(active_filters)}")
        
        # 3. 执行过滤
        filtered_data = []
        for item in asset_data:
            match = True
            if search_q and search_q.lower() not in item['知识库名称'].lower(): match = False
            if owner_f and item['所有人'] not in owner_f: match = False
            if type_f and item['类型'] not in type_f: match = False
            if status_f:
                if "🌐 公开" in status_f and "🌐 公开" not in item['权限状态']: match = False
                if "🔒 私有" in status_f and "🔒 私有" not in item['权限状态']: match = False
                if "已分享" in status_f and "🔒 私有" in item['权限状态'] and "🌐 公开" not in item['权限状态']: match = False 
            
            if match: filtered_data.append(item)
        
        # 4. 全选控制
        st.markdown(f"**共找到 {len(filtered_data)} 个资源**")
        sc1, sc2, _ = st.columns([1, 1, 6])
        
        # 使用回调处理全选逻辑
        if sc1.button("✅ 全选列表", key="btn_select_all", use_container_width=True):
             st.session_state.batch_select_trigger = True
             st.rerun()
        if sc2.button("❌ 取消全选", key="btn_deselect_all", use_container_width=True):
             st.session_state.batch_select_trigger = False
             st.rerun()
        
        # 应用全选状态到数据源
        if st.session_state.get('batch_select_trigger'):
             for item in filtered_data:
                 item["☑️"] = True
        else:
             # 如果是取消全选，确保数据源也是False
             for item in filtered_data:
                 item["☑️"] = False

        # 5. 显示数据表
        if not filtered_data:
            st.info("未找到匹配资源")
        else:
            df_assets = pd.DataFrame(filtered_data)
            
            edited_df = st.data_editor(
                df_assets, 
                use_container_width=True, 
                hide_index=True, 
                column_config={
                    "☑️": st.column_config.CheckboxColumn(width="small"),
                    "知识库名称": st.column_config.TextColumn(width="medium"),
                    "类型": st.column_config.TextColumn(width="small"),
                    "创建时间": st.column_config.TextColumn(width="small", help="知识库创建时间"),
                    "最后修改": st.column_config.TextColumn(width="small", help="最近一次文件变动时间"),
                    "文档数": st.column_config.NumberColumn(width="small", help="有效文档数量"),
                    "占用空间": st.column_config.TextColumn(width="small"),
                    "描述": st.column_config.TextColumn(width="large"),
                },
                key=f"resource_gov_editor_v9_{st.session_state.get('batch_select_trigger')}" # 动态Key以强制刷新状态
            )
            
            # 获取选中项
            selected_kbs = edited_df[edited_df["☑️"] == True]["知识库名称"].tolist()
            
            if selected_kbs:
                st.divider()
                st.markdown(f"**⚡ 批量操作 ({len(selected_kbs)} 个选中)**")
                
                # 操作区域分栏：权限操作 | 资产操作
                op_tab1, op_tab2 = st.tabs(["🔐 权限管理", "⚙️ 资产处置"])
                
                with op_tab1:
                    c_p1, c_p2, c_p3 = st.columns(3)
                    if c_p1.button("🌍 设为全站公开", use_container_width=True, type="primary"):
                        for k in selected_kbs: set_kb_public(k, True)
                        AuditLogger.log(st.session_state.get('user'), "KB_PUBLIC_BATCH", f"将 {len(selected_kbs)} 个库设为公开", ip=get_client_ip())
                        st.rerun()
                        
                    with c_p2:
                        # 精准分发逻辑
                        with st.popover("🤝 精准分发...", use_container_width=True):
                            target_roles = st.multiselect("授予角色", options=list(roles_config.keys()))
                            target_users = st.multiselect("授予用户", options=[u for u in users.keys() if users[u].get('role')!='admin'])
                            if st.button("确认分发", type="primary"):
                                s_conf = load_sharing_config()
                                for r in target_roles:
                                    s_conf['role_sharing'][r] = list(set(s_conf.get('role_sharing',{}).get(r,[])).union(set(selected_kbs)))
                                save_sharing_config(s_conf)
                                for u in target_users:
                                    users[u]['kb_whitelist'] = list(set(users[u].get('kb_whitelist',[])).union(set(selected_kbs)))
                                save_users(users)
                                AuditLogger.log(st.session_state.get('user'), "KB_DIST_BATCH", f"分发了 {len(selected_kbs)} 个库", ip=get_client_ip())
                                st.rerun()

                    if c_p3.button("🔒 撤销分享 (变私有)", use_container_width=True):
                        sc = load_sharing_config()
                        for k in selected_kbs:
                            if k in sc.get('public_kbs', []): sc['public_kbs'].remove(k)
                            for r in sc.get('role_sharing', {}):
                                if k in sc['role_sharing'][r]: sc['role_sharing'][r].remove(k)
                        save_sharing_config(sc)
                        AuditLogger.log(st.session_state.get('user'), "KB_PRIV_BATCH", f"撤销分享状态", status="warning", ip=get_client_ip())
                        st.rerun()

                with op_tab2:
                    c_a1, c_a2 = st.columns([2, 1])
                    # 移交
                    target_owner = c_a1.selectbox("选择新拥有者", options=list(users.keys()), key="batch_transfer_owner_new")
                    if c_a2.button("👤 移交所有权", type="primary", use_container_width=True):
                        success_count = 0
                        for k in selected_kbs:
                            try:
                                kp = os.path.join(kb_storage_root, k)
                                manifest_path = os.path.join(kp, "manifest.json")
                                if os.path.exists(manifest_path):
                                    with open(manifest_path, 'r', encoding='utf-8') as f: mf = json.load(f)
                                    mf['owner'] = target_owner
                                    with open(manifest_path, 'w', encoding='utf-8') as f: json.dump(mf, f, indent=4, ensure_ascii=False)
                                    success_count += 1
                            except: pass
                        if success_count:
                            AuditLogger.log(st.session_state.get('user'), "BATCH_TRANSFER", f"移交 {success_count} 个资产给 {target_owner}", ip=get_client_ip())
                            st.success(f"已移交 {success_count} 个库"); time.sleep(1); st.rerun()
                    
                    st.divider()
                    # 删除
                    if st.button("🗑️ 物理删除选中资产 (不可逆)", type="secondary", use_container_width=True):
                        import shutil
                        for k in selected_kbs:
                            try:
                                shutil.rmtree(os.path.join(kb_storage_root, k))
                                if os.path.exists(f"chat_histories/{k}.json"): os.remove(f"chat_histories/{k}.json")
                            except: pass
                        AuditLogger.log(st.session_state.get('user'), "BATCH_DELETE", f"物理删除 {len(selected_kbs)} 个资产", status="warning", ip=get_client_ip())
                        st.rerun()

    # --- Tab 2: 用户与会话 ---
    with tab_users:
        st.caption("身份治理中心：管理用户生命周期、权限覆盖与活跃会话控制")
        
        u_mode = st.radio("功能模块", ["👤 用户管理", "🎫 会话控制"], horizontal=True, label_visibility="collapsed")
        
        if u_mode == "👤 用户管理":
            # 构建用户列表数据
            user_list_data = []
            for u, info in users.items():
                user_list_data.append({
                    "用户名": u,
                    "角色": info.get('role', 'standard_user'),
                    "状态": "✅ 激活" if info.get('is_active', True) else "🚫 禁用",
                    "创建时间": info.get('created_at', '未知')[:10],
                    "最后登录": info.get('last_login', '从未')[:16].replace('T', ' ')
                })
            
            df_users = pd.DataFrame(user_list_data)
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                with st.expander("➕ 新增用户"):
                    new_u = st.text_input("用户名", key="admin_add_u")
                    new_p = st.text_input("初始密码", type="password", key="admin_add_p")
                    new_r = st.selectbox("角色", list(roles_config.keys()), key="admin_add_r")
                    if st.button("立即创建用户", type="primary"):
                        from src.auth.user_auth import register_user
                        success, msg = register_user(new_u, new_p, new_r)
                        if success:
                            AuditLogger.log(st.session_state.get('user'), "USER_CREATE", f"创建用户 {new_u}", ip=get_client_ip())
                            st.success(msg); time.sleep(0.5); st.rerun()
                        else: st.error(msg)
            
            with c2:
                with st.expander("🛠️ 用户维护"):
                    target_u = st.selectbox("选择目标用户", list(users.keys()))
                    if target_u:
                        curr_u_info = users[target_u]
                        new_role = st.selectbox("调整角色", list(roles_config.keys()), index=list(roles_config.keys()).index(curr_u_info.get('role', 'standard_user')) if curr_u_info.get('role') in roles_config else 0)
                        is_active = st.toggle("账号激活状态", value=curr_u_info.get('is_active', True))
                        
                        col_save, col_reset = st.columns(2)
                        if col_save.button("保存修改", use_container_width=True):
                            users[target_u]['role'] = new_role
                            users[target_u]['is_active'] = is_active
                            save_users(users)
                            AuditLogger.log(st.session_state.get('user'), "USER_UPDATE", f"更新用户 {target_u} 配置", ip=get_client_ip())
                            st.success("已更新"); st.rerun()
                            
                        if col_reset.button("重置密码 (123456)", use_container_width=True):
                            from src.auth.user_auth import hash_password
                            users[target_u]['password_hash'] = hash_password("123456")
                            save_users(users)
                            AuditLogger.log(st.session_state.get('user'), "USER_PWD_RESET", f"重置用户 {target_u} 密码", status="warning", ip=get_client_ip())
                            st.toast(f"已将 {target_u} 的密码重置为 123456")

        else: # 会话控制
            from src.auth.session_manager import get_session_settings, set_session_setting, revoke_user_sessions
            
            st.markdown("##### ⏱️ 全局策略")
            s_settings = get_session_settings()
            g_default = s_settings.get("global_default", 7)
            
            sc1, sc2 = st.columns([3, 1])
            new_g_days = sc1.slider("默认会话有效期 (天)", 1, 30, int(g_default))
            if sc2.button("更新策略", use_container_width=True):
                set_session_setting("global_default", new_g_days)
                st.success("全局策略已更新")
            
            st.divider()
            st.markdown("##### 👤 强行下线/续期")
            target_su = st.selectbox("选择用户", list(users.keys()), key="session_target_u")
            
            sc3, sc4 = st.columns(2)
            with sc3:
                u_days = s_settings.get(target_su, g_default)
                new_u_days = st.number_input("专属有效期 (天)", 1, 365, int(u_days))
                if st.button("设置专属时长", use_container_width=True):
                    set_session_setting(target_su, new_u_days)
                    st.success(f"已为 {target_su} 设置专属有效期")
            
            with sc4:
                st.write("") # 对齐
                if st.button("🔴 强制该用户所有设备下线", type="secondary", use_container_width=True):
                    count = revoke_user_sessions(target_su)
                    AuditLogger.log(st.session_state.get('user'), "SESSION_REVOKE", f"强行注销 {target_su} 的 {count} 个会话", status="warning", ip=get_client_ip())
                    st.warning(f"已注销 {count} 个活跃会话")

    # --- Tab 3: 角色定义 ---
    with tab_roles:
        st.caption("角色权限中台：定义角色的底层功能矩阵与默认资源配额")
        role_col1, role_col2 = st.columns([1, 2])
        with role_col1:
            st.markdown("**现有角色**")
            selected_role_id = st.radio("选择角色", list(roles_config.keys()), format_func=lambda x: f"{roles_config[x]['name']} ({x})", label_visibility="collapsed")
            with st.expander("➕ 新增角色"):
                n_rid = st.text_input("角色ID", placeholder="auditor")
                n_rname = st.text_input("名称", placeholder="审计员")
                if st.button("立即创建", use_container_width=True):
                    roles_config[n_rid] = {"name": n_rname, "description": "自定义角色", "permissions": ["chat"], "default_quota_mb": 100}
                    with open(ROLE_TEMPLATE_PATH, 'w', encoding='utf-8') as f: json.dump(roles_config, f, indent=4, ensure_ascii=False)
                    AuditLogger.log(st.session_state.get('user'), "ROLE_CREATE", f"创建角色: {n_rname}", ip=get_client_ip())
                    st.rerun()

        with role_col2:
            target_role = roles_config[selected_role_id]
            st.markdown(f"#### 🛠️ 编辑角色: {target_role['name']}")
            with st.container(border=True):
                new_desc = st.text_input("描述", value=target_role.get('description', ''))
                new_def_quota = st.number_input("默认配额 (MB)", -1, 9999, int(target_role.get('default_quota_mb', 100)))
                st.markdown("**功能权限位:**")
                curr_perms = target_role.get("permissions", [])
                new_perms = []
                p_cols = st.columns(2)
                for i, (p_id, p_name) in enumerate(ALL_PERMISSIONS_MAP.items()):
                    with p_cols[i % 2]:
                        if st.checkbox(p_name, value=(p_id in curr_perms or "*" in curr_perms), key=f"p_{selected_role_id}_{p_id}", disabled=(selected_role_id=="admin")):
                            new_perms.append(p_id)
                if st.button("💾 保存角色配置", use_container_width=True, type="primary"):
                    roles_config[selected_role_id].update({"description": new_desc, "default_quota_mb": new_def_quota, "permissions": new_perms})
                    with open(ROLE_TEMPLATE_PATH, 'w', encoding='utf-8') as f: json.dump(roles_config, f, indent=4, ensure_ascii=False)
                    AuditLogger.log(st.session_state.get('user'), "ROLE_UPDATE", f"更新角色 {selected_role_id}", ip=get_client_ip())
                    st.rerun()

    # --- Tab 5: 行为审计 (企业级监控面板 v6.6.7) ---
    with tab_audit:
        st.caption("全量行为链路追踪：支持高性能分页查询与多维逻辑穿透")
        
        # 1. 行为风控看板
        raw_logs = AuditLogger.get_logs(limit=5000) 
        if not raw_logs:
            st.info("暂无审计记录")
        else:
            df_logs = pd.DataFrame(raw_logs)
            df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
            
            with st.container(border=True):
                st.markdown("🛡️ **实时行为风控大盘**")
                rc1, rc2, rc3 = st.columns(3)
                failed_logins = df_logs[(df_logs['action'] == 'LOGIN_FAILED') & (df_logs['timestamp'] > (datetime.datetime.now() - pd.Timedelta(hours=1)))]
                if len(failed_logins) > 5: rc1.error(f"🚨 暴力破解风险: 过去1小时 {len(failed_logins)} 次失败")
                else: rc1.success("✅ 认证状态稳定")
                
                mass_deletes = df_logs[(df_logs['action_type'] == 'KB_MGMT') & (df_logs['action'].str.contains('DELETE', na=False))]
                if len(mass_deletes) > 10: rc2.warning(f"⚠️ 资产流失风险: 检测到大规模物理删除")
                else: rc2.success("✅ 资产结构安全")
                
                query_ops = df_logs[df_logs['action_type'] == 'CHAT']
                rc3.info(f"🗨️ 活跃问答: 当前有 {len(query_ops)} 条问答流水")

            # 2. 高级筛选矩阵
            with st.container(border=True):
                st.markdown("**🔍 审计穿透过滤器**")
                c1, c2, c3 = st.columns([1.5, 1, 1])
                min_date = df_logs['timestamp'].min().date()
                max_date = df_logs['timestamp'].max().date()
                sel_range = c1.date_input("🕒 观察窗口", value=(min_date, max_date), key="aud_range_v4")
                all_users = sorted(df_logs['user'].unique().tolist())
                sel_users_f = c2.multiselect("👤 执行用户", all_users, key="aud_user_f4")
                all_types = sorted(df_logs['action_type'].unique().tolist())
                sel_t = c3.multiselect("📂 动作分类", all_types, key="aud_type_f4")
                
                c4, c5, c6 = st.columns([1, 1, 1.5])
                all_status = sorted(df_logs['status'].unique().tolist())
                sel_s = c4.multiselect("🚦 结果状态", all_status, key="aud_status_f4")
                all_ips = sorted(df_logs['ip'].unique().tolist())
                sel_ips = c5.multiselect("🌐 源 IP 过滤", all_ips, key="aud_ip_f4")
                search_det = c6.text_input("📝 关键字穿透", placeholder="搜索详情、Diff或设备号...", key="audit_search_v4")

            f_logs = df_logs.copy()
            if len(sel_range) == 2:
                f_logs = f_logs[(f_logs['timestamp'].dt.date >= sel_range[0]) & (f_logs['timestamp'].dt.date <= sel_range[1])]
            if sel_users_f: f_logs = f_logs[f_logs['user'].isin(sel_users_f)]
            if sel_t: f_logs = f_logs[f_logs['action_type'].isin(sel_t)]
            if sel_s: f_logs = f_logs[f_logs['status'].isin(sel_s)]
            if sel_ips: f_logs = f_logs[f_logs['ip'].isin(sel_ips)]
            if search_det: 
                mask = f_logs.apply(lambda row: search_det.lower() in str(row.values).lower(), axis=1)
                f_logs = f_logs[mask]

            # 3. 分页控制
            st.divider()
            p_col1, p_col2, p_col3 = st.columns([2, 3, 2])
            with p_col1:
                rows_per_page = st.selectbox("每页显示", [10, 20, 50, 100], index=1, key="aud_page_size")
            total_rows = len(f_logs)
            total_pages = max(1, (total_rows + rows_per_page - 1) // rows_per_page)
            with p_col2:
                curr_page = st.number_input(f"当前页码 (共 {total_pages} 页)", 1, total_pages, 1, key="aud_curr_page")
            with p_col3:
                st.write(""); st.write("")
                st.markdown(f"显示 { (curr_page-1)*rows_per_page + 1 } - { min(curr_page*rows_per_page, total_rows) } 条")

            start_idx = (curr_page - 1) * rows_per_page
            display_df = f_logs.iloc[start_idx : start_idx + rows_per_page]

            # 4. 企业级紧凑 HTML 流水表
            type_icons = {"AUTH": "认证", "KB_MGMT": "库管理", "DATA_PROCESS": "数据处理", "ADMIN": "配置", "SECURITY": "安全", "CRAWL": "爬虫", "PREVIEW": "预览", "CHAT": "对话"}
            status_colors = {"success": ("#f0fdf4", "#166534", "成功"), "failed": ("#fef2f2", "#991b1b", "失败"), "warning": ("#fffbeb", "#92400e", "警告"), "intercepted": ("#faf5ff", "#6b21a8", "拦截")}
            
            table_html = """
<style>
.audit-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 12px; table-layout: fixed; }
.audit-table th { background: #f8fafc; color: #64748b; padding: 10px; text-align: left; border-bottom: 2px solid #e2e8f0; }
.audit-table td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.cell-compact { max-height: 50px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; text-overflow: ellipsis; }
.cell-compact:hover { max-height: none; -webkit-line-clamp: unset; background: white; position: relative; z-index: 10; box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-radius: 4px; padding: 5px; }
.badge-type { padding: 2px 6px; border-radius: 4px; background: #f1f5f9; color: #475569; font-weight: 600; font-size: 10px; }
.badge-status { padding: 2px 8px; border-radius: 20px; font-weight: 600; font-size: 10px; }
.diff-tag { color: #2563eb; background: #eff6ff; padding: 1px 4px; border-radius: 3px; font-family: monospace; font-size: 10px; border: 1px solid #dbeafe; display: inline-block; margin-top: 4px; }
</style>
<table class='audit-table'>
<thead><tr><th style='width: 12%'>🕒 时间</th><th style='width: 10%'>👤 用户</th><th style='width: 12%'>分类/动作</th><th style='width: 48%'>📝 执行摘要与变更对比</th><th style='width: 8%'>🚦 状态</th><th style='width: 10%'>🌐 IP</th></tr></thead>
<tbody>
"""
            for _, row in display_df.iterrows():
                ts = row['timestamp'].strftime('%m-%d %H:%M:%S')
                t_label = type_icons.get(row.get('action_type'), row.get('action_type', 'GENERIC'))
                d_html = f"<br><span class='diff-tag'>Δ {row['diff'].get('item')}: {row['diff'].get('new_value')}</span>" if (row.get('diff') and isinstance(row.get('diff'), dict)) else ""
                bg, fg, s_lab = status_colors.get(row.get('status', 'success'), ("#f1f5f9", "#475569", "未知"))
                table_html += f"<tr><td>{ts}</td><td style='font-weight:700'>{row['user']}</td><td><span class='badge-type'>{t_label}</span><br><small>{row.get('action')}</small></td><td><div class='cell-compact'>{row['details']}{d_html}</div></td><td><span class='badge-status' style='background:{bg};color:{fg}'>{s_lab}</span></td><td>{row.get('ip', '...')}</td></tr>"
            
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)
            csv = f_logs.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出筛选结果 (CSV)", data=csv, file_name=f"audit_{datetime.datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)

    # --- Tab 6: 终端控制 (新增) ---
    with tab_term:
        # 修正: st.session_state.user 存储的是用户名字符串，role 单独存储
        if st.session_state.get('role') != 'admin':
            st.error("⛔ 权限不足：仅超级管理员可访问终端")
        else:
            st.caption("🚀 本地 SSH 终端 (WebSSH)")
            st.warning("⚠️ 注意：此功能将直接连接服务器终端，请谨慎操作。请使用本机 OS 用户名/密码登录。")
            
            col_svc, col_status = st.columns([1, 4])
            with col_svc:
                if st.button("启动终端服务 (8899)", key="btn_start_term_rg", use_container_width=True):
                    import subprocess
                    # 使用 wssh 启动服务，监听 8899 端口
                    try:
                        subprocess.Popen(["wssh", "--port=8899", "--fbidhttp=False"], 
                                       stdout=subprocess.DEVNULL, 
                                       stderr=subprocess.DEVNULL)
                        st.toast("终端服务正在启动...", icon="⏳")
                        time.sleep(2)
                        st.success("服务已发送启动指令")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"启动失败: {e}")

            # 嵌入 Iframe
            import streamlit.components.v1 as components
            terminal_url = "http://localhost:8899"
            
            # 始终尝试渲染 iframe，如果服务没启动会显示连接失败
            components.iframe(terminal_url, height=600, scrolling=True)

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def get_client_ip():
    from src.common.utils import get_client_ip
    try: return get_client_ip()
    except: return "127.0.0.1"