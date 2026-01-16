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
        "⚡ 资源分发", "👤 用户与会话", "🗄️ 资产全览", "🎭 角色定义", "📜 行为审计"
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
                            AuditLogger.log(st.session_state.get('user'), "BATCH_AUTH", f"批量授权给 {len(sel_users)} 名用户", ip=get_client_ip())
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
                            AuditLogger.log(st.session_state.get('user'), "KB_DIST_BATCH", f"分发了 {len(sel_dist_kbs)} 个库", ip=get_client_ip())
                            st.rerun()
                        if b3.button("🔒 设为私有", use_container_width=True, key="btn_dist_priv"):
                            sc = load_sharing_config()
                            for k in sel_dist_kbs:
                                if k in sc.get('public_kbs', []): sc['public_kbs'].remove(k)
                                for r in sc.get('role_sharing', {}):
                                    if k in sc['role_sharing'][r]: sc['role_sharing'][r].remove(k)
                            save_sharing_config(sc)
                            AuditLogger.log(st.session_state.get('user'), "KB_PRIV_BATCH", f"撤销分享状态", status="warning", ip=get_client_ip())
                            st.rerun()

    # --- Tab 2: 用户与会话 ---
    with tab_users:
        st.caption("账户全生命周期管理：从基本属性到登录会话安全")
        from src.auth.session_manager import get_session_settings, set_session_setting, revoke_user_sessions
        
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
                        revoke_user_sessions(uname)
                        AuditLogger.log(st.session_state.get('user'), "SESSION_REVOKE", f"注销用户 {uname} 会话", status="warning", ip=get_client_ip())
                        st.rerun()
        except Exception as e: st.error(f"渲染失败: {e}")

    # --- Tab 3: 资产全览 ---
    with tab_assets:
        st.caption("全量物理资产审计与治理：监控磁盘占用、所有权移交及深度清理")
        from src.config.manifest_manager import ManifestManager
        kb_storage_root = os.path.join(os.getcwd(), "vector_db_storage")
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
            asset_data.append({
                "☑️ 选择": st.session_state.get(f"asset_sel_{kb}", False),
                "知识库名称": kb, 
                "所有人": manifest.get('owner', 'admin'), 
                "文件数": file_count, 
                "格式化大小": format_size(total_size)
            })

        with st.container(border=True):
            st.markdown("**🔍 资产筛选**")
            f_col1, f_col2 = st.columns([1, 1.5])
            search_asset = f_col1.text_input("按名称搜索", placeholder="输入知识库名称...", key="search_asset_input")
            all_owners = sorted(list(set([d['所有人'] for d in asset_data]))) if asset_data else []
            filter_owners = f_col2.multiselect("按所有人筛选", options=all_owners, key="filter_asset_owner")

        filtered_data = [item for item in asset_data if (not filter_owners or item['所有人'] in filter_owners) and (not search_asset or search_asset.lower() in item['知识库名称'].lower())]

        if filtered_data:
            df_assets = pd.DataFrame(filtered_data)
            edited_df = st.data_editor(df_assets, use_container_width=True, hide_index=True, key="asset_manager_editor_v3")
            selected_kbs = edited_df[edited_df["☑️ 选择"] == True]["知识库名称"].tolist()
            
            if selected_kbs:
                st.divider()
                ac1, ac2 = st.columns([2, 1])
                target_owner = ac1.selectbox("选择接收者", options=list(users.keys()), key="batch_transfer_owner")
                if ac2.button("👤 批量移交所有权", type="primary", use_container_width=True):
                    success_count = 0
                    error_count = 0
                    for k in selected_kbs:
                        try:
                            kp = os.path.join(kb_storage_root, k)
                            manifest_path = os.path.join(kp, "manifest.json")
                            if os.path.exists(manifest_path):
                                # 直接读取并更新
                                with open(manifest_path, 'r', encoding='utf-8') as f:
                                    mf = json.load(f)
                                mf['owner'] = target_owner
                                # 物理固化写入
                                with open(manifest_path, 'w', encoding='utf-8') as f:
                                    json.dump(mf, f, indent=4, ensure_ascii=False)
                                success_count += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            st.error(f"移交 {k} 时出错: {e}")
                            error_count += 1
                    
                    if success_count > 0:
                        AuditLogger.log(st.session_state.get('user'), "BATCH_TRANSFER", f"成功将 {success_count} 个资产移交给 {target_owner}", ip=get_client_ip())
                        st.toast(f"✅ 成功移交 {success_count} 个资产", icon="👤")
                    if error_count > 0:
                        st.error(f"❌ {error_count} 个资产移交失败，请检查文件权限")
                    time.sleep(0.5)
                    st.rerun()
                
                if st.button("🗑️ 物理删除选中资产", type="secondary", use_container_width=True):
                    import shutil
                    for k in selected_kbs:
                        shutil.rmtree(os.path.join(kb_storage_root, k))
                        if os.path.exists(f"chat_histories/{k}.json"): os.remove(f"chat_histories/{k}.json")
                    AuditLogger.log(st.session_state.get('user'), "BATCH_DELETE", f"物理删除 {len(selected_kbs)} 个资产", status="warning", ip=get_client_ip())
                    st.rerun()

    # --- Tab 4: 角色定义 ---
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
                failed_logins = df_logs[(df_logs['action'] == 'LOGIN_FAILED') & (df_logs['timestamp'] > (datetime.now() - pd.Timedelta(hours=1)))]
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
            st.download_button("📥 导出筛选结果 (CSV)", data=csv, file_name=f"audit_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True)

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def get_client_ip():
    from src.common.utils import get_client_ip
    try: return get_client_ip()
    except: return "127.0.0.1"
