import streamlit as st
import streamlit.components.v1 as components
import os
import json
import time
import pandas as pd
import hashlib
import subprocess
import importlib # [Fix] Hot reload support
from datetime import datetime, timedelta
from src.auth.user_auth import load_users, save_users
from src.auth.session_manager import load_sharing_config, save_sharing_config, set_kb_public, revoke_user_sessions
from src.kb.kb_manager import KBManager
from src.config.manifest_manager import ManifestManager
import src.auth.connection_manager # [Fix] Import module for reloading
from src.auth.connection_manager import ConnectionManager

USER_CONFIG_PATH = "config/users.json"
ROLE_TEMPLATE_PATH = "config/role_templates.json"

ALL_PERMISSIONS_MAP = {
    "chat": "🗨️ 基础对话", "kb_create": "➕ 创建库", "kb_delete_own": "🗑️ 删除个人库",
    "kb_rename": "✏️ 重命名库", "kb_rebuild_index": "🔄 重建索引", "upload_files": "📤 上传文件", 
    "paste_text": "📝 粘贴文本", "use_crawler": "🌐 网页爬虫", "smart_search": "🔍 联网搜索", 
    "deep_research": "🧠 深度研究", "data_analysis": "📊 数据分析", "summary_gen": "✨ AI 摘要", 
    "download_knowledge_base": "📥 资产下载", "kb_export_report": "📝 导出报告",
    "kb_export_full": "🏗️ 全量镜像", "kb_filesystem_access": "📂 系统访问",
    "manage_system_config": "🛠️ 系统配置", "view_stats": "📊 查看监控"
}

def render_resource_governance_v19():
    # [Fix] 强制热重载连接管理器，防止 AttributeError
    importlib.reload(src.auth.connection_manager)
    from src.auth.connection_manager import ConnectionManager
    
    st.toast("💎 旗舰治理 v19 (深度资源 + 精准账户) 已上线", icon="🛡️")
    from src.auth.audit_logger import AuditLogger
    from src.auth.session_manager import get_session_settings, set_session_setting, revoke_user_sessions, load_session_store, save_session_store
    
    # 1. 样式定义
    st.markdown("""
        <style>
            .stMetric { background: #f8fafc; padding: 12px; border-radius: 10px; border: 1px solid #e2e8f0; }
            .individual-cabin { background: #f0f9ff; border: 1px solid #bae6fd; padding: 20px; border-radius: 12px; margin-top: 15px; }
            .expert-card { background: #ffffff; border: 1px solid #e2e8f0; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
        </style>
    """, unsafe_allow_html=True)

    # 数据加载
    users = load_users(); sharing_config = load_sharing_config()
    session_settings = get_session_settings()
    global_ttl = int(session_settings.get("global_default", 7))
    conn_manager = ConnectionManager() # [v8.3.0] 初始化连接管理器
    
    if os.path.exists(ROLE_TEMPLATE_PATH):
        with open(ROLE_TEMPLATE_PATH, 'r', encoding='utf-8') as f: roles_config = json.load(f)
    else: roles_config = {}
    
    projects_config = {}
    if os.path.exists("config/projects_config.json"):
        try:
            with open("config/projects_config.json", 'r', encoding='utf-8') as f: projects_config = json.load(f)
        except: pass

    kb_manager = KBManager(); kb_manager.base_path = os.path.join(os.getcwd(), "vector_db_storage")
    kb_storage_root = kb_manager.base_path
    all_kbs = kb_manager.list_all()
    project_db_paths = [p.get('db_path') for p in projects_config.values()]

    # 2. 旗舰扫描引擎 (回归 v15 核心能力)
    asset_data = []
    total_size = 0; zombie_count = 0; large_assets = 0; owner_map = {}
    
    for kb in all_kbs:
        kb_path = os.path.join(kb_storage_root, kb)
        manifest = ManifestManager.load(kb_path)
        is_healthy = os.path.exists(os.path.join(kb_path, "manifest.json"))
        t_size = 0; last_mod = 0
        try:
            for root, _, files in os.walk(kb_path):
                for f in files:
                    fp = os.path.join(root, f); f_s = os.path.getsize(fp)
                    t_size += f_s
                    m_t = os.path.getmtime(fp)
                    if m_t > last_mod: last_mod = m_t
        except: pass
        
        total_size += t_size
        owner = manifest.get('owner', 'admin')
        owner_map[owner] = owner_map.get(owner, 0) + t_size
        
        # 风险识别
        is_large = t_size > 500 * 1024 * 1024
        is_idle = (time.time() - last_mod) > (30 * 86400) if last_mod > 0 else True
        
        compliance = "✅ 合规"
        if not is_healthy: compliance = "🚨 索引损坏"; zombie_count += 1
        elif is_large: compliance = "⚠️ 容量预警"; large_assets += 1
        elif is_idle: compliance = "💤 长期闲置"

        is_proj = any(kb in p_path or p_path in kb_path for p_path in project_db_paths)
        
        asset_data.append({
            "☑️": False,
            "治理状态": compliance,
            "属性": "💎 核心项目" if is_proj else "📦 业务库",
            "资源标识": kb,
            "负责人": owner,
            "物理规模": t_size,
            "占用空间": format_size(t_size),
            "最后活跃": datetime.fromtimestamp(last_mod).strftime('%Y-%m-%d') if last_mod > 0 else "未知",
            "访问权限": "🌐 公开" if kb in sharing_config.get("public_kbs", []) else "🔒 私有"
        })

    st.markdown("### 💎 全域资源与账户访问安全治理 (旗舰版)")
    tab_dist, tab_users, tab_roles, tab_conns, tab_audit, tab_term = st.tabs([
        "🛡️ 资源深度治理", "👤 账户与访问安全", "🎭 权限矩阵定义", "🔌 数据源连接", "📜 系统行为审计", "💻 全能终端控制"
    ])

    # --- Tab 1: 资源深度治理 (功能完全找回版) ---
    with tab_dist:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("资产总数", len(all_kbs))
        m2.metric("物理总负载", format_size(total_size))
        m3.metric("预警项", zombie_count + large_assets, delta_color="inverse")
        m4.metric("合规率", f"{(len(all_kbs)-zombie_count)/max(1,len(all_kbs))*100:.1f}%")
        
        with st.expander("📊 资源占用分布透视", expanded=False):
            if owner_map:
                df_owner = pd.DataFrame([{"用户": u, "占用(MB)": s/1024/1024} for u, s in owner_map.items()])
                st.bar_chart(df_owner.set_index("用户"), height=150, color="#6366f1")

        st.divider()
        with st.container():
            f1, f2, f3 = st.columns([2, 1, 1])
            search_q = f1.text_input("🔍 搜索标识", key="v19_res_q")
            f_owner = f2.multiselect("👤 负责人", sorted(list(owner_map.keys())))
            f_status = f3.selectbox("🚦 治理状态", ["全部状态", "✅ 合规", "🚨 索引损坏", "⚠️ 容量预警", "💤 长期闲置"])
            filtered = [d for d in asset_data if 
                        (not search_q or search_q.lower() in d['资源标识'].lower()) and 
                        (not f_owner or d['负责人'] in f_owner) and
                        (f_status == "全部状态" or d['治理状态'] == f_status)]
        
        # 表格还原
        edited_res = st.data_editor(
            pd.DataFrame(filtered), 
            use_container_width=True, 
            hide_index=True, 
            column_config={
                "☑️": st.column_config.CheckboxColumn(label="", width="small"),
                "物理规模": None,
                "治理状态": st.column_config.TextColumn("状态", width="small"),
                "最后活跃": st.column_config.TextColumn("活跃日期", width="small")
            }, 
            key="rg_v19_res_editor"
        )
        
        selected_kbs = edited_res[edited_res["☑️"] == True]["资源标识"].tolist()
        if selected_kbs:
            with st.container(border=True):
                st.markdown(f"**⚡ 资产治理决策引擎 (已选 {len(selected_kbs)} 项)**")
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button("🌍 翻转公开属性", use_container_width=True, type="primary"):
                        for k in selected_kbs: set_kb_public(k, k not in sharing_config.get("public_kbs", []))
                        st.rerun()
                with b2:
                    target_u = st.selectbox("过户给负责人", [""] + list(users.keys()))
                    if st.button("确认过户", use_container_width=True, disabled=not target_u):
                        for k in selected_kbs:
                            k_p = os.path.join(kb_storage_root, k); m = ManifestManager.load(k_p); m['owner'] = target_u
                            with open(os.path.join(k_p, "manifest.json"), 'w', encoding='utf-8') as f: json.dump(m, f, ensure_ascii=False, indent=2)
                        st.rerun()
                with b3:
                    if st.button("🔥 物理彻底粉碎", use_container_width=True):
                        import shutil
                        for k in selected_kbs:
                            try: shutil.rmtree(os.path.join(kb_storage_root, k)); h_p = os.path.join("chat_histories", f"{k}.json"); os.remove(h_p) if os.path.exists(h_p) else None
                            except: pass
                        st.rerun()
                
                if len(selected_kbs) == 1:
                    st.markdown("---")
                    c1, c2 = st.columns([3, 1])
                    new_n = c1.text_input("重命名资源标识", value=selected_kbs[0], label_visibility="collapsed")
                    if c2.button("💾 提交更名", use_container_width=True):
                        s, m = kb_manager.rename(selected_kbs[0], new_n)
                        if s: st.success(m); time.sleep(0.5); st.rerun()
                        else: st.error(m)

    # --- Tab 2: 账户与访问安全 (个体化精准回归版) ---
    with tab_users:
        u_col1, u_col2 = st.columns([1, 1])
        u_col1.metric("总账户数", len(users))
        u_col2.metric("全局默认有效期", f"{global_ttl} 天")

        st.markdown("**👥 账户全景数据库 (勾选以开启单兵调节舱)**")
        user_list = []
        for u, info in users.items():
            user_ttl = session_settings.get(u)
            user_list.append({
                "☑️": False, "用户名": u, "角色": info.get('role'), 
                "状态": "✅ 活跃" if info.get('is_active', True) else "🚫 禁用",
                "独立策略": f"💎 {user_ttl} 天" if user_ttl else "🏠 遵循全局",
                "注册日期": info.get('created_at', '2026-01-01')[:10]
            })
        
        edited_user = st.data_editor(
            pd.DataFrame(user_list), 
            use_container_width=True, 
            hide_index=True, 
            column_config={"☑️": st.column_config.CheckboxColumn(label="", width="small")},
            key="v19_user_grid"
        )
        
        selected_users = edited_user[edited_user["☑️"] == True]["用户名"].tolist()

        if selected_users:
            if len(selected_users) == 1:
                target = selected_users[0]
                target_ttl = session_settings.get(target, global_ttl)
                st.markdown(f'<div class="individual-cabin">', unsafe_allow_html=True)
                st.markdown(f"**👤 个体安全调节舱：{target}**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_ttl = st.slider("专属有效期 (天)", 1, 30, int(target_ttl), key=f"v19_ttl_{target}")
                    if st.button("💾 保存专属策略", use_container_width=True, type="primary"):
                        set_session_setting(target, new_ttl); st.rerun()
                with c2:
                    st.write("")
                    if st.button("🔄 恢复全局策略", use_container_width=True):
                        store = load_session_store()
                        if target in store.get("user_settings", {}):
                            del store["user_settings"][target]; save_session_store(store); st.rerun()
                    if st.button("🔑 重置密码", use_container_width=True):
                        from src.auth.user_auth import hash_password
                        users[target]['password_hash'] = hash_password("123456"); save_users(users); st.toast("已重置为 123456")
                with c3:
                    st.write("")
                    if st.button("🚫 锁定/解冻", use_container_width=True):
                        users[target]['is_active'] = not users[target].get('is_active', True); save_users(users); st.rerun()
                    if st.button("⚡ 强制断开会话", use_container_width=True):
                        cnt = revoke_user_sessions(target); st.toast(f"已断开 {cnt} 个连接")
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                if st.button("🔥 批量注销选定用户会话", use_container_width=True):
                    for u in selected_users: revoke_user_sessions(u)
                    st.rerun()

        with st.expander("🛠️ 全局配置与账户注入", expanded=False):
            g_col, i_col = st.columns(2)
            with g_col:
                new_g = st.slider("默认有效期", 1, 30, global_ttl, key="v19_global_ttl")
                if st.button("应用全局策略", use_container_width=True):
                    set_session_setting("global_default", new_g); st.rerun()
            with i_col:
                nu = st.text_input("用户名", key="v19_nu")
                np = st.text_input("初始密码", key="v19_np", type="password")
                nr = st.selectbox("角色", list(roles_config.keys()), key="v19_nr")
                if st.button("确认注入账户", use_container_width=True):
                    from src.auth.user_auth import register_user
                    success, msg = register_user(nu, np, nr)
                    if success: st.success(msg); time.sleep(0.5); st.rerun()
                    else: st.error(msg)

    # --- Tab 3: 角色定义 ---
    with tab_roles:
        sel_rid = st.radio("选择角色", list(roles_config.keys()), horizontal=True, key="v12_rs")
        target_role = roles_config[sel_rid]; new_p = []
        p_cols = st.columns(2)
        for i, (p_id, p_name) in enumerate(ALL_PERMISSIONS_MAP.items()):
            with p_cols[i%2]:
                if st.checkbox(p_name, value=(p_id in target_role.get("permissions", [])), key=f"p_v12_{sel_rid}_{p_id}"): new_p.append(p_id)
        if st.button("💾 保存配置", key="v12_rs_btn"):
            roles_config[sel_rid]['permissions'] = new_p
            with open(ROLE_TEMPLATE_PATH, 'w') as f: json.dump(roles_config, f, indent=4); st.rerun()

    # --- Tab 4: 数据源连接 (New in v8.3.0) ---
    with tab_conns:
        st.markdown("**🔌 数据源连接管理** (支持多源异构数据库接入)")
        
        # 加载现有连接
        conns = conn_manager.load_connections()
        
        # 新增/编辑区域
        with st.expander("➕ 新增/编辑连接", expanded=True):
            c1, c2 = st.columns(2)
            alias = c1.text_input("连接名称 (Alias)", placeholder="e.g. 生产订单库")
            db_type = c2.selectbox("数据库类型", ["MySQL", "PostgreSQL"])
            
            c3, c4 = st.columns([3, 1])
            host = c3.text_input("主机地址 (Host)", value="localhost")
            port = c4.number_input("端口", value=3306 if db_type=="MySQL" else 5432)
            
            c5, c6, c7 = st.columns(3)
            user = c5.text_input("用户名")
            password = c6.text_input("密码", type="password")
            db_name = c7.text_input("数据库名")
            
            b1, b2 = st.columns([1, 1])
            if b1.button("📡 测试连通性", use_container_width=True):
                if not alias: st.error("请填写连接名称")
                else:
                    conf = {"type": db_type, "host": host, "port": port, "user": user, "password": password, "database": db_name}
                    s, m = conn_manager.test_connection(conf)
                    if s: st.success(f"✅ {m}")
                    else: st.error(f"❌ {m}")
            
            if b2.button("💾 保存连接", use_container_width=True, type="primary"):
                if not alias or not host or not user or not db_name:
                    st.error("请填写完整信息")
                else:
                    if conn_manager.save_connection(alias, db_type, host, port, user, password, db_name):
                        st.success(f"✅ 连接 '{alias}' 已保存"); time.sleep(0.5); st.rerun()
                    else:
                        st.error("保存失败")

        # 列表展示
        if conns:
            st.divider()
            st.caption("已保存的连接")
            for alias, info in conns.items():
                with st.container(border=True):
                    ic1, ic2, ic3 = st.columns([3, 2, 1])
                    ic1.markdown(f"**🔌 {alias}**")
                    ic1.caption(f"{info['type']}://{info['user']}@{info['host']}:{info['port']}/{info['database']}")
                    ic2.caption(f"更新时间: {datetime.fromtimestamp(float(info.get('updated_at', 0))).strftime('%Y-%m-%d %H:%M') if info.get('updated_at') else '-'}")
                    
                    ic_btn_col1, ic_btn_col2 = ic3.columns(2)
                    with ic_btn_col1:
                        show_struct = st.button("🔍 预览", key=f"preview_conn_{alias}", use_container_width=True)
                    with ic_btn_col2:
                        if st.button("🗑️", key=f"del_conn_{alias}", use_container_width=True, help="删除连接"):
                            if conn_manager.delete_connection(alias):
                                st.toast("已删除"); time.sleep(0.5); st.rerun()
                    
                    # 预览区域
                    if show_struct:
                        with st.container(border=True):
                            st.caption(f"🗄️ {alias} 数据透视")
                            
                            # Level 1: 数据库选择 (v8.3.1 新增)
                            dbs = conn_manager.get_database_list(alias)
                            current_db = info['database']
                            
                            # 尝试定位默认库的索引
                            default_idx = 0
                            if current_db in dbs:
                                default_idx = dbs.index(current_db)
                                
                            sel_db = st.selectbox("选择数据库 (Schema)", dbs, index=default_idx, key=f"sel_db_{alias}")
                            
                            if sel_db:
                                # Level 2: 表选择
                                tables = conn_manager.get_table_list(alias, db_override=sel_db)
                                if not tables:
                                    st.info(f"数据库 '{sel_db}' 中没有发现可读表")
                                else:
                                    sel_t = st.selectbox(f"选择表 ({len(tables)})", [""] + tables, key=f"sel_t_{alias}")
                                    
                                    # Level 3: 字段详情
                                    if sel_t:
                                        schema_data = conn_manager.get_table_schema(alias, sel_t, db_override=sel_db)
                                        if schema_data:
                                            st.dataframe(pd.DataFrame(schema_data), use_container_width=True, hide_index=True)
                                        else:
                                            st.info("无法获取表详情")

    # --- Tab 5: 行为审计 (全功能回归融合版) ---
    with tab_audit:
        st.caption("全量行为链路追踪：支持高性能分页查询与多维逻辑穿透")
        raw_logs = AuditLogger.get_logs(limit=5000)
        if not raw_logs: st.info("暂无审计记录")
        else:
            df_logs = pd.DataFrame(raw_logs); df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
            for col in ['level', 'resource_id', 'cost_ms']:
                if col not in df_logs.columns: df_logs[col] = (0 if col == 'cost_ms' else ('INFO' if col == 'level' else None))
            
            # 1. 战略可视化
            with st.container(border=True):
                v1, v2 = st.columns([3, 2])
                with v1:
                    df_logs['hour'] = df_logs['timestamp'].dt.floor('h')
                    df_logs['rw'] = df_logs['level'].map({"CRITICAL":50,"WARNING":10,"INFO":1}).fillna(1)
                    ts = df_logs.groupby('hour')['rw'].sum().reset_index()
                    st.area_chart(ts.set_index('hour'), color="#ff4b4b" if ts['rw'].max()>100 else "#29b5e8", height=150)
                with v2:
                    st.bar_chart(df_logs['action_type'].value_counts(), color="#6366f1", height=150)

            # 2. 全量回归过滤器
            st.divider()
            with st.container(border=True):
                st.markdown("**🔍 审计穿透过滤器 (全量恢复)**")
                c1, c2, c3 = st.columns([1.5, 1, 1])
                min_d, max_d = df_logs['timestamp'].min().date(), df_logs['timestamp'].max().date()
                sel_range = c1.date_input("🕒 观察窗口", value=(min_d, max_d), key="v12_aud_range")
                sel_u = c2.multiselect("👤 用户", sorted(df_logs['user'].unique().tolist()), key="v12_aud_u")
                sel_l = c3.multiselect("🚨 风险", ["INFO", "WARNING", "CRITICAL"], key="v12_aud_l")
                
                c4, c5, c6 = st.columns([1, 1, 1.5])
                sel_t = c4.multiselect("📂 分类", sorted(df_logs['action_type'].unique().tolist()), key="v12_aud_t")
                sel_s = c5.multiselect("🚦 状态", sorted(df_logs['status'].unique().tolist()), key="v12_aud_s")
                search_q = c6.text_input("📝 内容/IP/ID 穿透", key="v12_aud_q")

            f_df = df_logs.copy()
            if len(sel_range) == 2: f_df = f_df[(f_df['timestamp'].dt.date >= sel_range[0]) & (f_df['timestamp'].dt.date <= sel_range[1])]
            if sel_u: f_df = f_df[f_df['user'].isin(sel_u)]
            if sel_l: f_df = f_df[f_df['level'].isin(sel_l)]
            if sel_t: f_df = f_df[f_df['action_type'].isin(sel_t)]
            if sel_s: f_df = f_df[f_df['status'].isin(sel_s)]
            if search_q: f_df = f_df[f_df.apply(lambda row: search_q.lower() in str(row.values).lower(), axis=1)]

            # 3. 分页控制回归
            st.divider()
            p_col1, p_col2, p_col3 = st.columns([2, 3, 2])
            rpp = p_col1.selectbox("每页显示", [10, 20, 50, 100], index=1, key="v12_rpp")
            total_pages = max(1, (len(f_df)+rpp-1)//rpp)
            curr_p = p_col2.number_input(f"页码 (共 {total_pages} 页)", 1, total_pages, 1, key="v12_currp")
            with p_col3:
                st.write(""); st.write(""); st.markdown(f"共 {len(f_df)} 条记录")

            # 4. 流水表
            display_df = f_df.iloc[(curr_p-1)*rpp : curr_p*rpp]
            level_styles = {"INFO": ("#f8fafc", "#64748b", "🔵"), "WARNING": ("#fff7ed", "#9a3412", "🟠"), "CRITICAL": ("#fef2f2", "#991b1b", "🔴")}
            table_html = "<table style='width:100%; border-collapse:collapse; font-size:11px;'><thead><tr style='background:#f8fafc; text-align:left'><th>时间/风险</th><th>用户</th><th>详情</th><th>资源/IP</th></tr></thead><tbody>"
            for _, r in display_df.iterrows():
                bg, fg, icon = level_styles.get(r['level'], level_styles["INFO"])
                table_html += f"<tr style='background:{bg}; color:{fg}; border-bottom:1px solid #eee'><td>{r['timestamp'].strftime('%m-%d %H:%M')}<br>{icon} {r['level']}</td><td style='font-weight:700'>{r['user']}</td><td><b>{r['action']}</b><br>{r['details']}</td><td>{r['resource_id'] or '-'}<br><small>{r['ip']}</small></td></tr>"
            st.markdown(table_html + "</tbody></table>", unsafe_allow_html=True)
            
            # 5. CSV 导出回归
            csv = f_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 导出全量审计流水 (CSV)", data=csv, file_name=f"audit_{datetime.now().strftime('%Y%m%d')}.csv", key="v12_csv")

    # --- Tab 6: 终端控制 ---
    with tab_term:
        st.caption("🚀 本地 SSH 终端 (WebSSH) - 全能指挥通道")
        c_svc, c_h, c_ext = st.columns([1.5, 3, 1])
        with c_svc:
            if st.button("启动服务 (8899)", key="v12_term_start"):
                subprocess.Popen(["wssh", "--port=8899", "--fbidhttp=False"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2); st.rerun()
        with c_h: t_h = st.slider("窗口高度", 400, 2000, 600, 100, key="v12_term_h")
        with c_ext: st.markdown(f'<a href="http://localhost:8899" target="_blank" style="text-decoration:none;"><button style="width:100%; cursor:pointer; padding:8px; background:#2196f3; color:white; border:none; border-radius:6px; font-weight:600;">🚀 弹出窗口</button></a>', unsafe_allow_html=True)
        components.html(f'<iframe src="http://localhost:8899" style="width:100%; height:{t_h}px; border:1px solid #333; border-radius:8px; background:black;"></iframe>', height=t_h+20)

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def get_client_ip():
    from src.common.utils import get_client_ip
    try: return get_client_ip()
    except: return "127.0.0.1"
