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

def render_admin_management():
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
    
    tab_dist, tab_users, tab_assets, tab_roles, tab_audit = st.tabs([
        "⚡ 资源分发", "👤 用户与会话", "🗄️ 资产全览", "🎭 角色定义", "📜 审计记录"
    ])
    
    # --- Tab 1: 资源分发 ---
    with tab_dist:
        st.caption("统一权限调度中心：支持按用户或按资源视角进行批量授权")
        dist_mode = st.radio("操作视角", ["👤 用户视角", "📂 资源视角"], horizontal=True, label_visibility="collapsed")
        
        if dist_mode == "👤 用户视角":
            non_admin_users = [u for u in users.keys() if users[u].get('role') != 'admin']
            if not non_admin_users:
                st.info("暂无可管理的非管理员用户")
            else:
                c1, c2 = st.columns([2, 3])
                with c1:
                    sel_users = st.multiselect("第一步：选择用户", options=non_admin_users)
                    if st.checkbox("全选所有用户"): sel_users = non_admin_users
                with c2:
                    action = st.selectbox("第二步：选择操作", ["--- 请选择 ---", "批量赋予访问权", "批量封禁账户"])
                    if action == "批量赋予访问权" and sel_users:
                        target_kbs = st.multiselect("第三步：选择知识库", options=all_kbs)
                        if st.button("🔥 立即执行授权", type="primary", key="btn_dist_u"):
                            for u in sel_users:
                                users[u]['kb_whitelist'] = list(set(users[u].get('kb_whitelist', [])).union(set(target_kbs)))
                            save_users(users)
                            AuditLogger.log(st.session_state.get('user'), "BATCH_AUTH", f"批量授权给 {len(sel_users)} 名用户: {', '.join(target_kbs)}", ip=get_client_ip())
                            st.success("授权完成"); time.sleep(0.5); st.rerun()
                    elif action == "批量封禁账户" and sel_users:
                        if st.button("🔒 执行批量封禁", type="secondary", key="btn_lock_u"):
                            for u in sel_users: users[u]['is_active'] = False
                            save_users(users)
                            AuditLogger.log(st.session_state.get('user'), "BATCH_LOCK", f"批量封禁了 {len(sel_users)} 名用户", status="warning", ip=get_client_ip())
                            st.rerun()
        else:
            with st.container(border=True):
                st.markdown("**🔍 资源精准筛选**")
                fc1, fc2 = st.columns([2, 1])
                search_q = fc1.text_input("按名称搜索知识库", placeholder="输入关键词...", key="res_search_q")
                owner_f = fc2.multiselect("按所有人过滤", options=list(users.keys()), key="res_owner_f")
            
            f_kbs = all_kbs
            if search_q: f_kbs = [k for k in f_kbs if search_q.lower() in k.lower()]
            if owner_f: f_kbs = [k for k in f_kbs if any(k.startswith(f"{o}_") for o in owner_f) or ("admin" in owner_f and not "_" in k)]
            
            if not f_kbs:
                st.info("未找到匹配库")
            else:
                with st.container(border=True):
                    st.markdown(f"**⚡ 批量分发 ({len(f_kbs)} 个库)**")
                    ck, cr, cu = st.columns([2, 1.5, 1.5])
                    with ck: sel_dist_kbs = st.multiselect("1. 目标库", options=f_kbs, default=f_kbs[:10] if len(f_kbs)>10 else f_kbs)
                    with cr: target_roles = st.multiselect("2. 角色", options=list(roles_config.keys()))
                    with cu: target_users = st.multiselect("3. 用户", options=[u for u in users.keys() if users[u].get('role')!='admin'])
                    
                    if sel_dist_kbs:
                        b1, b2, b3 = st.columns(3)
                        if b1.button("🌍 全系统公开", use_container_width=True, type="primary", key="btn_dist_pub"):
                            for k in sel_dist_kbs: set_kb_public(k, True)
                            AuditLogger.log(st.session_state.get('user'), "KB_PUBLIC_BATCH", f"将 {len(sel_dist_kbs)} 个库设为公开", ip=get_client_ip())
                            st.rerun()
                        if b2.button("🤝 精准分发", use_container_width=True, key="btn_dist_precise"):
                            s_conf = load_sharing_config()
                            for r in target_roles:
                                s_conf['role_sharing'][r] = list(set(s_conf.get('role_sharing',{}).get(r,[])).union(set(sel_dist_kbs)))
                            save_sharing_config(s_conf)
                            for u in target_users:
                                users[u]['kb_whitelist'] = list(set(users[u].get('kb_whitelist',[])).union(set(sel_dist_kbs)))
                            save_users(users)
                            AuditLogger.log(st.session_state.get('user'), "KB_DIST_BATCH", f"分发了 {len(sel_dist_kbs)} 个库给指定角色/用户", ip=get_client_ip())
                            st.rerun()
                        if b3.button("🔒 设为私有", use_container_width=True, key="btn_dist_priv"):
                            sc = load_sharing_config()
                            for k in sel_dist_kbs:
                                if k in sc.get('public_kbs', []): sc['public_kbs'].remove(k)
                                for r in sc.get('role_sharing', {}):
                                    if k in sc['role_sharing'][r]: sc['role_sharing'][r].remove(k)
                            save_sharing_config(sc)
                            AuditLogger.log(st.session_state.get('user'), "KB_PRIV_BATCH", f"撤销了 {len(sel_dist_kbs)} 个库的分享状态", status="warning", ip=get_client_ip())
                            st.rerun()

    # --- Tab 2: 用户与会话 ---
    with tab_users:
        st.caption("账户全生命周期管理：从基本属性到登录会话安全")
        from src.auth.session_manager import get_user_storage_usage, format_size, get_session_settings, set_session_setting, revoke_user_sessions
        
        try:
            settings = get_session_settings()
            g_days = settings.get("global_default", 7)
            with st.expander("🌍 全局会话安全策略", expanded=False):
                col_g1, col_g2 = st.columns([3, 1])
                new_g = col_g1.slider("系统默认登录保持天数", 1, 365, g_days)
                if col_g2.button("更新全局", key="btn_g_sess"):
                    set_session_setting("global_default", new_g)
                    AuditLogger.log(st.session_state.get('user'), "CONFIG_CHANGE", f"修改全局会话时长为 {new_g} 天", ip=get_client_ip())
                    st.rerun()

            st.divider()
            for uname, info in users.items():
                u_days = settings.get(uname, g_days)
                role_id = info.get('role', 'standard_user')
                role_name = roles_config.get(role_id, {}).get('name', role_id)
                with st.expander(f"{'🟢' if info.get('is_active', True) else '🔴'} {uname} | 角色: {role_name}"):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1:
                        r_list = list(roles_config.keys())
                        try: ridx = r_list.index(info.get('role', 'standard_user'))
                        except: ridx = 0
                        n_role = st.selectbox("修改角色", r_list, index=ridx, format_func=lambda x: roles_config[x]['name'], key=f"r_{uname}")
                    with c2:
                        n_quota = st.number_input("空间配额(MB)", -1, 999999, int(info.get("storage_quota_mb", 100)), key=f"q_{uname}")
                    with c3:
                        n_active = st.toggle("激活状态", info.get('is_active', True), key=f"a_{uname}")
                    
                    sc1, sc2, sc3 = st.columns([2, 1, 1])
                    n_u_days = sc1.number_input("个性化有效期(天)", 1, 365, u_days, key=f"sd_{uname}")
                    if sc2.button("💾 保存配置", key=f"sv_{uname}", use_container_width=True):
                        users[uname].update({'role': n_role, 'is_active': n_active, 'storage_quota_mb': n_quota})
                        save_users(users); set_session_setting(uname, n_u_days)
                        AuditLogger.log(st.session_state.get('user'), "USER_UPDATE", f"更新用户 {uname} 属性", ip=get_client_ip())
                        st.toast("配置已保存"); st.rerun()
                    if sc3.button("🚨 强制下线", key=f"rv_{uname}", use_container_width=True, type="secondary"):
                        count = revoke_user_sessions(uname)
                        AuditLogger.log(st.session_state.get('user'), "SESSION_REVOKE", f"注销了用户 {uname} 的所有会话", status="warning", ip=get_client_ip())
                        st.rerun()
        except Exception as e: st.error(f"渲染失败: {e}")

    # --- Tab 3: 资产全览 (恢复治理能力) ---
    with tab_assets:
        st.caption("全量物理资产审计与治理：监控磁盘占用、所有权移交及深度清理")
        from src.config.manifest_manager import ManifestManager
        kb_storage_root = os.path.join(os.getcwd(), "vector_db_storage")
        
        # 1. 数据采集与状态同步
        asset_data = []
        for kb in all_kbs:
            kb_path = os.path.join(kb_storage_root, kb)
            manifest = ManifestManager.load(kb_path)
            total_size = 0
            file_count = 0
            try:
                for root, _, files in os.walk(kb_path):
                    for f in files:
                        total_size += os.path.getsize(os.path.join(root, f))
                        file_count += 1
            except: pass
            
            # 使用 session_state 维持选中状态 (支持跨筛选保留)
            is_selected = st.session_state.get(f"asset_sel_{kb}", False)
            
            raw_owner = manifest.get('owner', 'admin')
            display_owner = "系统管理员" if raw_owner == "admin" else raw_owner
            
            asset_data.append({
                "☑️ 选择": is_selected,
                "知识库名称": kb, 
                "所有人": display_owner, 
                "文件数": file_count, 
                "格式化大小": format_size(total_size), 
                "raw_size": total_size
            })

        # 2. 筛选区域
        with st.container(border=True):
            st.markdown("**🔍 资产筛选**")
            f_col1, f_col2 = st.columns([1, 1.5])
            with f_col1:
                search_asset = st.text_input("按名称搜索", placeholder="输入知识库名称...", key="search_asset_input")
            with f_col2:
                all_owners = sorted(list(set([d['所有人'] for d in asset_data]))) if asset_data else []
                filter_owners = st.multiselect("按所有人筛选", options=all_owners, key="filter_asset_owner")

        # 3. 执行筛选
        filtered_data = []
        for item in asset_data:
            if filter_owners and item['所有人'] not in filter_owners:
                continue
            if search_asset and search_asset.lower() not in item['知识库名称'].lower():
                continue
            filtered_data.append(item)

        # 4. 批量操作工具栏
        if filtered_data:
            st.markdown(f"📊 **共找到 {len(filtered_data)} 个资产**")
            
            # 全选/反选逻辑
            sel_col1, sel_col2, sel_col3 = st.columns([1, 1, 4])
            with sel_col1:
                if st.button("✅ 全选列表", use_container_width=True, help="选中下方列表中的所有知识库"):
                    for item in filtered_data:
                         st.session_state[f"asset_sel_{item['知识库名称']}"] = True
                    st.rerun()
            with sel_col2:
                if st.button("❌ 取消选择", use_container_width=True):
                    for item in asset_data: # 清除所有，不仅仅是筛选后的
                         st.session_state[f"asset_sel_{item['知识库名称']}"] = False
                    st.rerun()
            
            # 更新数据源的选中状态 (确保 DataEditor 显示最新状态)
            for item in filtered_data:
                item['☑️ 选择'] = st.session_state.get(f"asset_sel_{item['知识库名称']}", False)

            # 5. 数据表格
            df_assets = pd.DataFrame(filtered_data)
            
            # 使用 key 确保 data_editor 更新时能回写
            edited_df = st.data_editor(
                df_assets[["☑️ 选择", "知识库名称", "所有人", "文件数", "格式化大小"]], 
                use_container_width=True, 
                hide_index=True, 
                key="asset_manager_editor_v2",
                disabled=["知识库名称", "所有人", "文件数", "格式化大小"]
            )
            
            # 获取选中的项 (合并 session_state 和 手动编辑的结果)
            # 注意：此处优先信任 edited_df，因为它是用户当前看到的最终状态
            selected_rows = edited_df[edited_df["☑️ 选择"] == True]
            selected_kbs = selected_rows["知识库名称"].tolist()
            
            # 6. 批量动作区域
            if selected_kbs:
                st.divider()
                st.write(f"**⚡ 已选择 {len(selected_kbs)} 项进行操作**")
                
                ac1, ac2 = st.columns([2, 1])
                target_owner = ac1.selectbox("选择接收者", options=list(users.keys()), key="batch_asset_transfer_owner")
                
                if ac2.button("👤 批量移交所有权", type="primary", use_container_width=True):
                    for k in selected_kbs:
                        kp = os.path.join(kb_storage_root, k)
                        mf = ManifestManager.load(kp); mf['owner'] = target_owner
                        with open(os.path.join(kp, "manifest.json"), 'w', encoding='utf-8') as f: json.dump(mf, f, indent=4, ensure_ascii=False)
                    AuditLogger.log(st.session_state.get('user'), "BATCH_TRANSFER", f"将 {len(selected_kbs)} 个库移交给 {target_owner}", ip=get_client_ip())
                    st.success("移交成功"); st.rerun()
                
                # 危险操作区
                with st.expander("🚨 危险操作区域 (物理删除)", expanded=False):
                    st.warning("⚠️ 注意：物理删除操作不可恢复！将永久删除知识库文件和聊天记录。")
                    if st.button("🗑️ 物理删除选中资产", use_container_width=True, type="secondary"):
                         st.session_state.confirm_batch_delete = True
                    
                    if st.session_state.get("confirm_batch_delete"):
                        st.error(f"❌ 确定要永久删除这 {len(selected_kbs)} 个知识库吗？")
                        col_d1, col_d2 = st.columns(2)
                        if col_d1.button("🔥 确认删除", type="primary", use_container_width=True):
                            import shutil
                            success_count = 0
                            for k in selected_kbs: 
                                try:
                                    shutil.rmtree(os.path.join(kb_storage_root, k))
                                    if os.path.exists(f"chat_histories/{k}.json"): os.remove(f"chat_histories/{k}.json")
                                    # 清除选中状态
                                    st.session_state[f"asset_sel_{k}"] = False
                                    success_count += 1
                                except Exception as e:
                                    st.error(f"删除 {k} 失败: {e}")
                            
                            AuditLogger.log(st.session_state.get('user'), "BATCH_DELETE", f"物理删除了 {success_count} 个知识库资产", status="warning", ip=get_client_ip())
                            del st.session_state.confirm_batch_delete
                            st.rerun()
                        
                        if col_d2.button("取消", use_container_width=True):
                            del st.session_state.confirm_batch_delete
                            st.rerun()

        else:
            if asset_data:
                st.info("🔍 未找到匹配的资产，请调整筛选条件")
            else:
                st.info("暂无物理资产数据")

    # --- Tab 4: 角色定义 ---
    with tab_roles:
        st.caption("角色权限中台：定义角色的底层功能矩阵与默认资源配额")
        role_col1, role_col2 = st.columns([1, 2])
        with role_col1:
            st.markdown("**现有角色**")
            selected_role_id = st.radio("选择角色", list(roles_config.keys()), format_func=lambda x: f"{roles_config[x]['name']} ({x})", label_visibility="collapsed")
            st.divider()
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
                        is_checked = (p_id in curr_perms or "*" in curr_perms)
                        if st.checkbox(p_name, value=is_checked, key=f"perm_{selected_role_id}_{p_id}", disabled=(selected_role_id=="admin")):
                            new_perms.append(p_id)
                if st.button("💾 保存角色配置", use_container_width=True, type="primary"):
                    roles_config[selected_role_id].update({"description": new_desc, "default_quota_mb": new_def_quota, "permissions": new_perms})
                    with open(ROLE_TEMPLATE_PATH, 'w', encoding='utf-8') as f: json.dump(roles_config, f, indent=4, ensure_ascii=False)
                    AuditLogger.log(st.session_state.get('user'), "ROLE_UPDATE", f"更新角色 {selected_role_id} 权限", ip=get_client_ip())
                    st.success("已保存"); st.rerun()

    # --- Tab 5: 审计记录 (企业级监控面板) ---
    with tab_audit:
        st.caption("系统全行为追踪：从管理指令到 AI 推演的深度审计流水")
        raw_logs = AuditLogger.get_logs()
        if not raw_logs:
            st.info("暂无审计记录")
        else:
            df_logs = pd.DataFrame(raw_logs)
            df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
            df_logs = df_logs.sort_values('timestamp', ascending=False)
            
            # 1. 筛选矩阵 (多维增强)
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1.8])
                # 时间范围
                min_date = df_logs['timestamp'].min().date()
                max_date = df_logs['timestamp'].max().date()
                sel_range = c1.date_input("🕒 观察窗口", value=(min_date, max_date), key="aud_range_v2")
                
                # 分类筛选 [v6.4.1] 修复旧日志无分类导致的 TypeError
                if 'action_type' in df_logs:
                    df_logs['action_type'] = df_logs['action_type'].fillna('GENERIC').astype(str)
                    all_types = sorted([t for t in df_logs['action_type'].unique() if t])
                else:
                    all_types = []
                sel_t = c2.multiselect("📂 动作分类", all_types, key="aud_type_f")
                
                # 状态筛选 [v6.4.1] 增加鲁棒性
                df_logs['status'] = df_logs['status'].fillna('success').astype(str)
                all_status = sorted([s for s in df_logs['status'].unique() if s])
                sel_s = c3.multiselect("🚦 结果状态", all_status, key="aud_status_f")
                
                # [v6.4.2] 补齐丢失的搜索框逻辑
                search_det = c4.text_input("🔍 详情穿透", placeholder="搜索用户、IP或动作详情...", key="audit_search_v2")

            # 过滤逻辑
            f_logs = df_logs.copy()
            if len(sel_range) == 2:
                f_logs = f_logs[(f_logs['timestamp'].dt.date >= sel_range[0]) & (f_logs['timestamp'].dt.date <= sel_range[1])]
            if sel_t: f_logs = f_logs[f_logs['action_type'].isin(sel_t)]
            if sel_s: f_logs = f_logs[f_logs['status'].isin(sel_s)]
            if search_det: 
                mask = f_logs.apply(lambda row: search_det.lower() in str(row.values).lower(), axis=1)
                f_logs = f_logs[mask]

            # 2. 动态监控看板
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("匹配记录数", len(f_logs))
            
            failed_count = len(f_logs[f_logs['status'].isin(['failed', 'intercepted', 'warning'])])
            k2.metric("异常/拦截告警", failed_count, delta=f"{failed_count}" if failed_count > 0 else "0", delta_color="inverse")
            
            active_users = f_logs['user'].nunique()
            k3.metric("活跃执行者", active_users)
            
            csv = f_logs.to_csv(index=False).encode('utf-8-sig')
            k4.download_button("📥 导出审计报表", data=csv, file_name=f"audit_report_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)

            st.write("")
            
            # 3. 企业级 HTML 流水表 [v6.4.3] 修复缩进导致的源码显露问题
            type_icons = {
                "AUTH": "认证", "KB_MGMT": "库管理", "DATA_PROCESS": "数据处理", 
                "ADMIN": "系统管理", "SECURITY": "安全审计", "GENERIC": "通用动作"
            }
            status_colors = {
                "success": ("#f0fdf4", "#166534", "成功"), 
                "failed": ("#fef2f2", "#991b1b", "失败"),
                "warning": ("#fffbeb", "#92400e", "警告"),
                "intercepted": ("#faf5ff", "#6b21a8", "拦截")
            }
            # 动作名称汉化映射 [v6.6.1]
            action_map = {
                "LOGIN": "账户登录", "AUTO_LOGIN": "自动登录", "LOGOUT": "注销退出",
                "REGISTER": "账号注册", "DELETE_KB": "物理删除库", "CREATE_KB": "创建知识库",
                "RENAME_KB": "重命名库", "REBUILD_INDEX": "重建索引", "UPLOAD_FILE": "上传文件",
                "BATCH_AUTH": "批量授权", "BATCH_LOCK": "批量封禁", "USER_UPDATE": "更新用户属性",
                "SESSION_REVOKE": "注销用户会话", "CONFIG_CHANGE": "全局配置变更",
                "KB_PUBLIC_BATCH": "批量公开资产", "KB_DIST_BATCH": "批量分发资产",
                "KB_PRIV_BATCH": "批量设为私有", "BATCH_TRANSFER": "批量所有权移交",
                "BATCH_DELETE": "批量物理删除", "DATA_ANALYSIS_EXEC": "执行数据推演"
            }

            # 关键修复：HTML 字符串行首绝对不能有空格，物理对齐到最左侧
            table_html = """
<style>
.audit-table { width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 12px; color: #1e293b; }
.audit-table th { background: #f8fafc; color: #64748b; padding: 12px 10px; text-align: left; border-bottom: 2px solid #e2e8f0; }
.audit-table td { padding: 10px; border-bottom: 1px solid #f1f5f9; vertical-align: middle; }
.badge-type { padding: 2px 6px; border-radius: 4px; background: #f1f5f9; color: #475569; font-weight: 600; font-size: 10px; display: inline-block; }
.badge-status { padding: 2px 10px; border-radius: 20px; font-weight: 600; font-size: 11px; text-transform: uppercase; }
.details-cell { max-width: 350px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #475569; }
.audit-table tr:hover { background: #f8fafc; }
.ip-text { font-family: monospace; color: #94a3b8; font-size: 11px; }
</style>
<table class='audit-table'>
<thead>
<tr>
<th style='width: 15%'>🕒 发生时间</th>
<th style='width: 10%'>👤 执行者</th>
<th style='width: 15%'>分类 / 动作</th>
<th style='width: 40%'>📝 业务执行详情</th>
<th style='width: 10%'>🚦 状态</th>
<th style='width: 10%'>🌐 IP</th>
</tr>
</thead>
<tbody>
"""
            
            for _, row in f_logs.head(200).iterrows():
                ts = row['timestamp'].strftime('%m-%d %H:%M:%S')
                a_type = row.get('action_type', 'GENERIC')
                type_label = type_icons.get(a_type, "通用")
                
                # 执行者汉化
                raw_user = row['user']
                display_user = "系统管理员" if raw_user == "admin" else raw_user
                
                # 动作名称汉化
                raw_action = row.get('action', 'Unknown')
                action_label = action_map.get(raw_action, raw_action)
                
                s_val = row.get('status', 'success')
                bg, fg, s_label = status_colors.get(s_val, ("#f1f5f9", "#475569", "未知"))
                
                details_raw = str(row['details']).replace('"', '&quot;')
                
                # 每一行都必须紧贴左侧
                table_html += f"<tr>"
                table_html += f"<td style='color: #64748b'>{ts}</td>"
                table_html += f"<td style='font-weight: 700;'>{display_user}</td>"
                table_html += f"<td><span class='badge-type'>{type_label}</span><br><small style='color: #94a3b8;'>{action_label}</small></td>"
                table_html += f"<td class='details-cell' title='{details_raw}'>{details_raw}</td>"
                table_html += f"<td><span class='badge-status' style='background: {bg}; color: {fg};'>{s_label}</span></td>"
                table_html += f"<td class='ip-text'>{row.get('ip', '...')}</td>"
                table_html += f"</tr>"
            
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)

def get_client_ip():
    from src.common.utils import get_client_ip
    try: return get_client_ip()
    except: return "127.0.0.1"