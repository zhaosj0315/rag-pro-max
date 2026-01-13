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
                with st.expander(f"{'🟢' if info.get('is_active', True) else '🔴'} {uname} | 角色: {info.get('role')}"):
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
                "☑️ 选择": False,
                "知识库名称": kb, 
                "所有人": manifest.get('owner', 'admin'), 
                "文件数": file_count, 
                "格式化大小": format_size(total_size), 
                "raw_size": total_size
            })

        if asset_data:
            df_assets = pd.DataFrame(asset_data)
            edited_df = st.data_editor(df_assets[["☑️ 选择", "知识库名称", "所有人", "文件数", "格式化大小"]], use_container_width=True, hide_index=True, key="asset_manager_editor")
            
            selected_kbs = edited_df[edited_df["☑️ 选择"] == True]["知识库名称"].tolist()
            if selected_kbs:
                st.write(f"**⚡ 批量治理 ({len(selected_kbs)} 项)**")
                ac1, ac2 = st.columns([2, 1])
                target_owner = ac1.selectbox("选择接收者", options=list(users.keys()))
                if ac2.button("👤 移交所有权", type="primary", use_container_width=True):
                    for k in selected_kbs:
                        kp = os.path.join(kb_storage_root, k)
                        mf = ManifestManager.load(kp); mf['owner'] = target_owner
                        with open(os.path.join(kp, "manifest.json"), 'w', encoding='utf-8') as f: json.dump(mf, f, indent=4, ensure_ascii=False)
                    AuditLogger.log(st.session_state.get('user'), "BATCH_TRANSFER", f"将 {len(selected_kbs)} 个库移交给 {target_owner}", ip=get_client_ip())
                    st.success("移交成功"); st.rerun()
                
                if st.button("🚨 物理删除资产包 (危险)", use_container_width=True):
                    import shutil
                    for k in selected_kbs: 
                        shutil.rmtree(os.path.join(kb_storage_root, k))
                        if os.path.exists(f"chat_histories/{k}.json"): os.remove(f"chat_histories/{k}.json")
                    AuditLogger.log(st.session_state.get('user'), "BATCH_DELETE", f"物理删除了 {len(selected_kbs)} 个知识库资产", status="failed", ip=get_client_ip())
                    st.rerun()
        else: st.info("暂无物理资产数据")

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

    # --- Tab 5: 审计记录 (修复渲染版) ---
    with tab_audit:
        st.caption("系统全行为追踪：从管理指令到用户提问的深度审计流水")
        raw_logs = AuditLogger.get_logs()
        if not raw_logs:
            st.info("暂无审计记录")
        else:
            df_logs = pd.DataFrame(raw_logs)
            df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
            df_logs = df_logs.sort_values('timestamp', ascending=False)
            
            # 1. 筛选矩阵
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1.8])
                # 时间范围筛选
                min_date = df_logs['timestamp'].min().date()
                max_date = df_logs['timestamp'].max().date()
                sel_range = c1.date_input("🕒 时间范围", value=(min_date, max_date), min_value=min_date, max_value=max_date, key="aud_range")
                
                sel_u = c2.multiselect("👤 用户", sorted(df_logs['user'].unique()), key="aud_u")
                sel_a = c3.multiselect("⚡ 动作", sorted(df_logs['action'].unique()), key="aud_a")
                search_det = c4.text_input("🔍 详情检索", placeholder="搜索详情内容...", key="audit_detail_search")

            # 过滤逻辑
            f_logs = df_logs.copy()
            if len(sel_range) == 2:
                f_logs = f_logs[(f_logs['timestamp'].dt.date >= sel_range[0]) & (f_logs['timestamp'].dt.date <= sel_range[1])]
            if sel_u: f_logs = f_logs[f_logs['user'].isin(sel_u)]
            if sel_a: f_logs = f_logs[f_logs['action'].isin(sel_a)]
            if search_det: f_logs = f_logs[f_logs['details'].str.contains(search_det, case=False, na=False)]

            # 2. 顶部看板 (随筛选联动)
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("匹配操作数", len(f_logs))
            k2.metric("异常预警", len(f_logs[f_logs['status'] == 'failed']))
            k3.metric("活跃IP", f_logs['ip'].nunique() if 'ip' in f_logs else 0)
            csv = f_logs.to_csv(index=False).encode('utf-8-sig')
            k4.download_button("📥 导出筛选结果", data=csv, file_name=f"audit_export.csv", use_container_width=True)

            st.write("")
            
            # 构建极致紧凑的 HTML
            th = "<style>.at{width:100%;border-collapse:collapse;font-size:11px;color:#334;line-height:1.1}.at th{text-align:left;padding:4px 10px;background:#f8fafc;color:#64748b;border-bottom:1px solid #e2e8f0}.at td{padding:2px 10px;border-bottom:1px solid #f1f5f9;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:300px}.at tr:hover{background:#f1f5f9}</style><table class='at'><thead><tr><th style='width:14%'>🕒 时间</th><th style='width:10%'>👤 用户</th><th style='width:12%'>⚡ 动作</th><th style='width:46%'>📝 详情摘要</th><th style='width:8%'>🚦 状态</th><th style='width:10%'>🌐 IP</th></tr></thead><tbody>"
            rows = ""
            for _, row in f_logs.head(200).iterrows():
                status = row.get('status', 'success')
                icon = "🟢" if status == 'success' else "🔴" if status == 'failed' else "🟡"
                ts_str = row['timestamp'].strftime('%m-%d %H:%M:%S')
                raw_det = str(row['details']).replace("'", "&#39;").replace('"', "&quot;")
                disp_det = (raw_det[:80] + '...') if len(raw_det) > 80 else raw_det
                rows += f"<tr><td style='color:#94a3b8'>{ts_str}</td><td style='font-weight:600'>{row['user']}</td><td><span style='background:#f1f5f9;color:#475569;padding:1px 4px;border-radius:3px;font-size:9px;font-family:sans-serif;font-weight:600;'>{row['action']}</span></td><td title='{raw_det}'>{disp_det}</td><td>{icon} {status[:1].upper()}</td><td style='color:#94a3b8'>{row.get('ip','-.--')}</td></tr>"
            
            st.markdown(th + rows + "</tbody></table>", unsafe_allow_html=True)

def get_client_ip():
    from src.common.utils import get_client_ip
    try: return get_client_ip()
    except: return "127.0.0.1"