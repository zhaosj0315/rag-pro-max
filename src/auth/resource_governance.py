import streamlit as st
import streamlit.components.v1 as components
import os
import json
import time
import pandas as pd
import subprocess
import importlib # [Fix] Hot reload support
from datetime import datetime
from src.auth.user_auth import load_users, save_users
from src.auth.session_manager import load_sharing_config, set_kb_public
from src.kb.kb_manager import KBManager
from src.config.manifest_manager import ManifestManager
import src.auth.connection_manager # [Fix] Import module for reloading

USER_CONFIG_PATH = "config/users.json"
ROLE_TEMPLATE_PATH = "config/role_templates.json"

ALL_PERMISSIONS_MAP = {
    "chat": "🗨️ 基础对话", "kb_create": "➕ 创建库", "kb_append": "📥 追加知识", "kb_delete_own": "🗑️ 删除个人库",
    "kb_rename": "✏️ 重命名库", "kb_rebuild_index": "🔄 重建索引", "upload_files": "📤 上传文件", 
    "paste_text": "📝 粘贴文本", "use_crawler": "🌐 网页爬虫", "smart_search": "🔍 联网搜索", 
    "precise_query": "🎯 精准提问", "deep_research": "🧠 深度研究", "data_analysis": "📊 数据分析", "summary_gen": "✨ AI 摘要", 
    "download_knowledge_base": "📥 资产下载", "kb_export_report": "📝 导出报告",
    "kb_export_full": "🏗️ 全量镜像", "kb_filesystem_access": "📂 系统访问",
    "manage_system_config": "🛠️ 系统配置", "view_stats": "📊 查看监控"
}

def render_resource_governance_v19():
    # [Fix] 强制热重载连接管理器，防止 AttributeError
    from src.auth import connection_manager
    importlib.reload(connection_manager)
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
    tab_dist, tab_users, tab_roles, tab_conns, tab_db_users, tab_sys_logs, tab_term, tab_monitor, tab_sched, tab_progress, tab_tactical = st.tabs([
        "🛡️ 资源深度治理", "👤 账户与访问安全", "🎭 权限矩阵定义", "🔌 数据源连接", "🗄️ 数据库用户", "📜 系统全景日志", "💻 全能终端控制", "📊 实时系统监控", "⚙️ 智能调度", "📈 进度追踪", "🐾 战术指挥中心"
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
        df_filtered = pd.DataFrame(filtered)
        if df_filtered.empty:
            st.info("ℹ️ 系统中暂无符合条件的资源资产。")
            selected_kbs = []
        else:
            edited_res = st.data_editor(
                df_filtered, 
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
            
            # 确保列存在再过滤
            if "☑️" in edited_res.columns:
                selected_kbs = edited_res[edited_res["☑️"] == True]["资源标识"].tolist()
            else:
                selected_kbs = []
        
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
                target_quota = users[target].get('storage_quota_mb', 100)
                
                st.markdown(f'<div class="individual-cabin">', unsafe_allow_html=True)
                st.markdown(f"**👤 个体安全调节舱：{target}**")
                c1, c2, c3 = st.columns(3)
                with c1:
                    new_ttl = st.slider("专属有效期 (天)", 1, 30, int(target_ttl), key=f"v19_ttl_{target}")
                    new_quota = st.number_input("存储配额 (MB, -1为无限)", value=int(target_quota), key=f"v19_quota_{target}")
                    
                    if st.button("💾 保存专属策略", use_container_width=True, type="primary"):
                        set_session_setting(target, new_ttl)
                        users[target]['storage_quota_mb'] = new_quota
                        save_users(users)
                        st.toast("✅ 策略与配额已保存")
                        st.rerun()
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
        with st.expander("➕ 新增/编辑连接", expanded=not bool(conns)):
            c1, c2 = st.columns(2)
            alias = c1.text_input("连接名称 (Alias)", placeholder="e.g. 生产订单库")
            db_type = c2.selectbox("数据库类型", ["MySQL", "PostgreSQL", "SQLite", "DuckDB", "ClickHouse", "SQL Server", "Oracle", "MaxCompute", "Snowflake"])
            
            c3, c4 = st.columns([3, 1])
            if db_type in ["SQLite", "DuckDB"]:
                host = c3.text_input("本地文件路径", placeholder="e.g. /Users/data/mydb.db")
                port = 0
            elif db_type == "MaxCompute":
                host = c3.text_input("Endpoint", placeholder="e.g. http://service.cn-shanghai.maxcompute.aliyun.com/api")
                port = 0
            elif db_type == "Snowflake":
                host = c3.text_input("Account Identifier", placeholder="e.g. xy12345.east-us-2.azure")
                port = 0
            else:
                host = c3.text_input("主机地址 (Host)", value="localhost")
                port = c4.number_input("端口", value={"MySQL": 3306, "PostgreSQL": 5432, "ClickHouse": 8123, "SQL Server": 1433, "Oracle": 1521}.get(db_type, 3306))
            
            c5, c6, c7 = st.columns(3)
            # 动态标签逻辑
            no_auth = db_type in ["SQLite", "DuckDB"]
            user_label = "AccessKey ID" if db_type == "MaxCompute" else "用户名"
            pass_label = "AccessKey Secret" if db_type == "MaxCompute" else "密码"
            
            db_placeholder = "数据库/Schema"
            if db_type == "MaxCompute": db_placeholder = "Project Name"
            elif db_type == "Oracle": db_placeholder = "Service Name"
            
            user = c5.text_input(user_label, disabled=no_auth)
            password = c6.text_input(pass_label, type="password", disabled=no_auth)
            db_name = c7.text_input("目标库名", placeholder=db_placeholder, value="default" if db_type=="ClickHouse" else "", disabled=no_auth)
            
            b1, b2 = st.columns([1, 1])
            if b1.button("📡 测试连通性", use_container_width=True):
                if not alias: st.error("请填写连接名称")
                else:
                    conf = {"type": db_type.lower().replace(" ",""), "host": host, "port": port, "user": user, "password": password, "database": db_name}
                    s, m = conn_manager.test_connection(conf)
                    if s: st.success(f"✅ {m}")
                    else: st.error(f"❌ {m}")
            
            if b2.button("💾 保存连接", use_container_width=True, type="primary"):
                if not alias or not host:
                    st.error("请填写完整信息")
                else:
                    if conn_manager.save_connection(alias, db_type, host, port, user, password, db_name):
                        st.success(f"✅ 连接 '{alias}' 已保存"); time.sleep(0.5); st.rerun()
                    else:
                        st.error("保存失败")

        # 列表展示
        if conns:
            st.divider()
            st.caption("已保存的连接清单")
            for alias, info in conns.items():
                with st.container(border=True):
                    ic1, ic2, ic3 = st.columns([3, 2, 1.5])
                    ic1.markdown(f"**🔌 {alias}** ({info['type']})")
                    if info['type'] == 'SQLite':
                        ic1.caption(f"路径: {info['host']}")
                    else:
                        ic1.caption(f"{info['user']}@{info['host']}:{info['port']}/{info['database']}")
                    
                    ic2.caption(f"更新: {datetime.fromtimestamp(float(info.get('updated_at', 0))).strftime('%m-%d %H:%M') if info.get('updated_at') else '-'}")
                    
                    ic_btn_col1, ic_btn_col2 = ic3.columns(2)
                    with ic_btn_col1:
                        # [Fix] 使用 Session State 持久化预览状态
                        if st.button("🔍 预览", key=f"preview_conn_{alias}", use_container_width=True):
                            st.session_state.active_preview_alias = alias
                            st.rerun()
                    with ic_btn_col2:
                        if st.button("🗑️", key=f"del_conn_{alias}", use_container_width=True, help="删除连接"):
                            if conn_manager.delete_connection(alias):
                                st.toast("已删除"); time.sleep(0.5); st.rerun()
                    
                    # 预览区域 (v9.4.0 全新分栏布局 - 数据库全景透视)
                    # [Fix] 检查 Session State 状态
                    if st.session_state.get('active_preview_alias') == alias:
                        with st.container(border=True):
                            # [Fix] 头部添加关闭按钮
                            col_head, col_close = st.columns([20, 1])
                            with col_head:
                                st.caption(f"🌐 数据库透视看板: {alias}")
                            with col_close:
                                if st.button("✖️", key=f"close_prev_{alias}", help="关闭预览"):
                                    st.session_state.active_preview_alias = None
                                    st.rerun()
                            
                            # Level 1: 数据库选择 (顶部导航第一级)
                            dbs = conn_manager.get_database_list(alias)
                            current_db = info.get('database', '')
                            default_idx = dbs.index(current_db) if current_db in dbs else 0
                            
                            # 布局优化：将数据库和表选择放在顶部两列
                            nav_c1, nav_c2 = st.columns([1, 2])
                            with nav_c1:
                                sel_db = st.selectbox("切换数据库 Schema", dbs, index=default_idx, key=f"sel_db_{alias}")
                            
                            if sel_db:
                                tables = conn_manager.get_table_list(alias, db_override=sel_db)
                                if not tables:
                                    st.warning(f"数据库 '{sel_db}' 中没有发现可读表")
                                else:
                                    with nav_c2:
                                        # Level 2: 表选择 (顶部导航第二级 - 支持搜索)
                                        table_options = ["🏠 数据库概览"] + sorted(tables)
                                        selection = st.selectbox("定位数据表 (支持搜索)", table_options, key=f"nav_{alias}")
                                    
                                    st.divider()
                                    
                                    # 内容展示区 (100% 宽度自适应)
                                    if selection == "🏠 数据库概览":
                                        # --- 数据库级信息预览 ---
                                        db_info = conn_manager.get_database_info(alias, db_override=sel_db)
                                        
                                        st.markdown(f"#### 🌐 数据库全景: {sel_db}")
                                        
                                        # 分类卡片展示
                                        dt1, dt2 = st.columns(2)
                                        with dt1:
                                            with st.container(border=True):
                                                st.caption("📝 基础属性")
                                                c1, c2 = st.columns(2)
                                                c1.metric("数据库类型", db_info['type'])
                                                c2.metric("字符集", db_info['charset'])
                                                st.caption(f"版本: {db_info['version']}")
                                        
                                        with dt2:
                                            with st.container(border=True):
                                                st.caption("📊 规模统计")
                                                c1, c2 = st.columns(2)
                                                c1.metric("表数量", db_info['table_count'])
                                                c2.metric("索引总数", db_info['index_count'])
                                                st.caption(f"主机: {info.get('host')}:{info.get('port')}")

                                    else:
                                        # --- 表级信息预览 ---
                                        table_name = selection # No prefix
                                        st.markdown(f"#### 📄 数据表: `{table_name}`")
                                        
                                        t_tab1, t_tab2, t_tab3 = st.tabs(["📋 结构定义", "💾 数据预览 (100行+)", "🕸️ 关联与洞察"])
                                        
                                        with t_tab1:
                                            # 表结构
                                            schema_data = conn_manager.get_table_schema(alias, table_name, db_override=sel_db)
                                            if schema_data:
                                                df_schema = pd.DataFrame(schema_data)
                                                st.dataframe(
                                                    df_schema, 
                                                    use_container_width=True, 
                                                    hide_index=True,
                                                    column_config={
                                                        "主键": st.column_config.TextColumn("PK", width="small"),
                                                        "允许为空": st.column_config.TextColumn("Null", width="small"),
                                                        "类型": st.column_config.TextColumn("Type", width="medium"),
                                                    }
                                                )
                                            else:
                                                st.warning("无法获取表结构")
                                        
                                        with t_tab2:
                                            # 数据采样 (Lazy Load + Pagination)
                                            limit = 100
                                            # 获取总行数用于分页
                                            insights = conn_manager.get_table_insights(alias, table_name, db_override=sel_db)
                                            total_rows = insights.get('row_count', 0)
                                            
                                            # 分页状态管理
                                            page_key = f"page_{alias}_{table_name}"
                                            if page_key not in st.session_state:
                                                st.session_state[page_key] = 1
                                            
                                            current_page = st.session_state[page_key]
                                            total_pages = max(1, (total_rows + limit - 1) // limit)
                                            offset = (current_page - 1) * limit
                                            
                                            # 分页控件栏
                                            c_prev, c_info, c_next = st.columns([1, 2, 1])
                                            with c_prev:
                                                if st.button("⬅️ 上一页", key=f"prev_{page_key}", disabled=current_page <= 1):
                                                    st.session_state[page_key] -= 1
                                                    st.rerun()
                                            with c_info:
                                                st.markdown(f"<div style='text-align:center; padding-top:5px'>第 <b>{current_page}</b> / {total_pages} 页 (共 {total_rows} 行)</div>", unsafe_allow_html=True)
                                            with c_next:
                                                if st.button("下一页 ➡️", key=f"next_{page_key}", disabled=current_page >= total_pages):
                                                    st.session_state[page_key] += 1
                                                    st.rerun()

                                            # 获取分页数据
                                            sample_data = conn_manager.get_table_sample(alias, table_name, db_override=sel_db, limit=limit, offset=offset)
                                            if sample_data:
                                                st.dataframe(pd.DataFrame(sample_data), use_container_width=True, height=400)
                                            else:
                                                st.info("当前页无数据")
                                        
                                        with t_tab3:
                                            # 业务洞察 (复用已获取的 insights)
                                            stats = conn_manager.get_table_stats(alias, table_name, db_override=sel_db)
                                            
                                            c1, c2, c3 = st.columns(3)
                                            c1.metric("预估行数", f"{insights.get('row_count', 0):,}")
                                            c2.metric("物理大小", stats.get('size_mb', 'Unknown'))
                                            c3.metric("存储引擎", insights.get('engine', 'unknown').upper())
                                            
                                            if stats.get('create_time') != 'Unknown':
                                                st.caption(f"🕒 创建时间: {stats['create_time']}")
                                            
                                            fks = insights.get('foreign_keys', [])
                                            if fks:
                                                st.divider()
                                                st.markdown("**🔗 外键拓扑**")
                                                st.dataframe(pd.DataFrame(fks), use_container_width=True, hide_index=True)
                                            else:
                                                st.caption("未检测到显式外键约束")

    # --- Tab 5: 数据库用户管理 (New) ---
    with tab_db_users:
        from src.ui.db_admin_ui import DBAdminUI
        DBAdminUI.render()

    # --- Tab 6: 系统全景日志 (Fused: Audit + Logs) ---
    with tab_sys_logs:
        st.caption("🛡️ 全局审计与监控仪表盘：融合行为追踪与系统运行日志，提供一站式可观测性。")
        
        # 加载审计数据
        raw_logs = AuditLogger.get_logs(limit=5000)
        df_logs = pd.DataFrame(raw_logs) if raw_logs else pd.DataFrame()
        if not df_logs.empty:
            df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
            for col in ['level', 'resource_id', 'cost_ms']:
                if col not in df_logs.columns: df_logs[col] = (0 if col == 'cost_ms' else ('INFO' if col == 'level' else None))

        # 1. 顶层战略概览 (Top Dashboard)
        with st.container(border=True):
            dash_c1, dash_c2 = st.columns([1.5, 1])
            with dash_c1:
                st.markdown("**📈 行为流量趋势**")
                if not df_logs.empty:
                    df_logs['hour'] = df_logs['timestamp'].dt.floor('h')
                    df_logs['rw'] = df_logs['level'].map({"CRITICAL":50,"WARNING":10,"INFO":1}).fillna(1)
                    ts = df_logs.groupby('hour')['rw'].sum().reset_index()
                    st.area_chart(ts.set_index('hour'), color="#ff4b4b" if ts['rw'].max()>100 else "#29b5e8", height=180)
                else:
                    st.info("暂无流量数据")
            
            with dash_c2:
                st.markdown("**📂 日志资产概况**")
                # 调用日志统计 (轻量级)
                from src.utils.compact_log_display import CompactLogDisplay
                log_display = CompactLogDisplay()
                log_files = log_display._get_log_files()
                l_c1, l_c2 = st.columns(2)
                l_c1.metric("系统日志文件", len(log_files))
                total_size = sum(f.stat().st_size for f in log_files if f.exists())
                l_c2.metric("物理占用", format_size(total_size))
                
                if not df_logs.empty:
                    st.divider()
                    st.caption(f"👥 审计记录: {len(df_logs)} 条 | 👤 活跃用户: {len(df_logs['user'].unique())}")

        st.divider()

        # 2. 双视图切换 (Dual View)
        sub_t1, sub_t2 = st.tabs(["👤 用户行为审计", "🖥️ 系统终端日志"])

        # --- Sub 1: 行为审计 (原 tab_audit 逻辑) ---
        with sub_t1:
            if df_logs.empty:
                st.info("暂无审计记录")
            else:
                # 过滤器
                with st.expander("🔍 深度穿透过滤器", expanded=False):
                    c1, c2, c3 = st.columns([1.5, 1, 1])
                    min_d, max_d = df_logs['timestamp'].min().date(), df_logs['timestamp'].max().date()
                    sel_range = c1.date_input("🕒 观察窗口", value=(min_d, max_d), key="v19_aud_range")
                    sel_u = c2.multiselect("👤 用户", sorted(df_logs['user'].unique().tolist()), key="v19_aud_u")
                    sel_l = c3.multiselect("🚨 风险", ["INFO", "WARNING", "CRITICAL"], key="v19_aud_l")
                    
                    c4, c5, c6 = st.columns([1, 1, 1.5])
                    sel_t = c4.multiselect("📂 分类", sorted(df_logs['action_type'].unique().tolist()), key="v19_aud_t")
                    sel_s = c5.multiselect("🚦 状态", sorted(df_logs['status'].unique().tolist()), key="v19_aud_s")
                    search_q = c6.text_input("📝 内容/IP/ID 穿透", key="v19_aud_q")

                f_df = df_logs.copy()
                if len(sel_range) == 2: f_df = f_df[(f_df['timestamp'].dt.date >= sel_range[0]) & (f_df['timestamp'].dt.date <= sel_range[1])]
                if sel_u: f_df = f_df[f_df['user'].isin(sel_u)]
                if sel_l: f_df = f_df[f_df['level'].isin(sel_l)]
                if sel_t: f_df = f_df[f_df['action_type'].isin(sel_t)]
                if sel_s: f_df = f_df[f_df['status'].isin(sel_s)]
                if search_q: f_df = f_df[f_df.apply(lambda row: search_q.lower() in str(row.values).lower(), axis=1)]

                # 流水表
                st.dataframe(
                    f_df[['timestamp', 'level', 'user', 'action', 'details', 'resource_id', 'ip']], 
                    use_container_width=True, 
                    hide_index=True,
                    column_config={
                        "timestamp": st.column_config.DatetimeColumn("时间", format="MM-DD HH:mm:ss", width="small"),
                        "level": st.column_config.TextColumn("风险", width="small"),
                        "user": st.column_config.TextColumn("用户", width="small"),
                        "action": "操作动作",
                        "details": "详情",
                        "ip": "来源IP"
                    }
                )
                
                # CSV 导出
                csv = f_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("📥 导出审计流水 (CSV)", data=csv, file_name=f"audit_{datetime.now().strftime('%Y%m%d')}.csv", key="v19_csv")

        # --- Sub 2: 终端日志 (原 tab_logs 逻辑) ---
        with sub_t2:
            from src.utils.compact_log_display import render_compact_log_management
            # 复用现有的日志渲染逻辑
            render_compact_log_management(key_prefix="admin_sys_logs")

    # --- Tab 7: 终端控制 ---
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

    # --- Tab 8: 实时系统监控 (Moved from Main Sidebar) ---
    with tab_monitor:
        try:
            from src.utils.realtime_monitor import RealtimeMonitor
            monitor = RealtimeMonitor()
            monitor.render_realtime_monitor()
        except ImportError:
            st.error("❌ 无法加载实时监控模块")
        except Exception as e:
            st.error(f"❌ 监控面板加载失败: {e}")

    # --- Tab 9: 智能调度 (Moved from Monitor) ---
    with tab_sched:
        try:
            from src.core.v23_integration import get_v23_integration
            v23 = get_v23_integration()
            v23.render_scheduler_panel()
        except ImportError:
            st.error("❌ 无法加载智能调度模块")
        except Exception as e:
            st.error(f"❌ 调度面板加载失败: {e}")

    # --- Tab 10: 进度追踪 (New) ---
    with tab_progress:
        from src.ui.progress_tracker import render_progress_panel
        render_progress_panel(key_prefix="admin_prog")

    # --- Tab 11: 战术指挥中心 (Integrated External Dashboard) ---
    with tab_tactical:
        from src.ui.tactical_dashboard_adapter import TacticalDashboardAdapter
        TacticalDashboardAdapter.render()

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def get_client_ip():
    from src.common.utils import get_client_ip
    try: return get_client_ip()
    except: return "127.0.0.1"
