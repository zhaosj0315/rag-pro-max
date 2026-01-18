import streamlit as st
import streamlit.components.v1 as components
import os
import json
import time
import pandas as pd
import hashlib
import subprocess
from datetime import datetime, timedelta
from src.auth.user_auth import load_users, save_users
from src.auth.session_manager import load_sharing_config, save_sharing_config, set_kb_public, revoke_user_sessions
from src.kb.kb_manager import KBManager
from src.config.manifest_manager import ManifestManager

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

def render_resource_governance_v12():
    st.toast("🛡️ 审计大盘 v12 (全量功能融合版) 已上线", icon="🛰️")
    from src.auth.audit_logger import AuditLogger
    st.markdown("### 👥 系统用户与资源调度")
    
    users = load_users()
    sharing_config = load_sharing_config()
    
    if os.path.exists(ROLE_TEMPLATE_PATH):
        with open(ROLE_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            roles_config = json.load(f)
    else: roles_config = {}

    kb_manager = KBManager(); kb_manager.base_path = os.path.join(os.getcwd(), "vector_db_storage")
    all_kbs = kb_manager.list_all()
    
    s_col1, s_col2, s_col3, s_col4 = st.columns(4)
    s_col1.metric("总注册用户", len(users)); s_col2.metric("公开知识库", len(sharing_config.get("public_kbs", [])))
    s_col3.metric("总物理资产", len(all_kbs)); s_col4.metric("在线监控", "Active")
    st.divider()
    
    tab_dist, tab_users, tab_roles, tab_audit, tab_term = st.tabs([
        "🛡️ 资源治理", "👤 用户与会话", "🎭 角色定义", "📜 行为审计", "💻 终端控制"
    ])
    
    # --- Tab 1: 资源治理 (完全保全原始逻辑) ---
    with tab_dist:
        st.caption("全域资源物理生命周期管理")
        kb_storage_root = os.path.join(os.getcwd(), "vector_db_storage")
        asset_data = []
        for kb in all_kbs:
            kb_path = os.path.join(kb_storage_root, kb); manifest = ManifestManager.load(kb_path)
            t_size = 0; d_cnt = 0; last_modified = 0
            try:
                for root, _, files in os.walk(kb_path):
                    for f in files:
                        fp = os.path.join(root, f); t_size += os.path.getsize(fp)
                        mtime = os.path.getmtime(fp)
                        if mtime > last_modified: last_modified = mtime
                        if f.endswith(('.pdf', '.docx', '.txt', '.md', '.csv')): d_cnt += 1
            except: pass
            c_raw = manifest.get('created_at') or manifest.get('created_time')
            try: c_str = str(c_raw).replace('T', ' ')[:16] if c_raw else "未知"
            except: c_str = "未知"
            asset_data.append({
                "☑️": False, "知识库名称": kb, "所有人": manifest.get('owner', 'admin'),
                "创建时间": c_str, "占用空间": format_size(t_size), "文档数": d_cnt,
                "权限状态": "🌐 公开" if kb in sharing_config.get("public_kbs", []) else "🔒 私有"
            })
        fc1, fc2 = st.columns([3, 1])
        search_q = fc1.text_input("搜索知识库", key="rg_v12_s_q")
        f_owner = fc2.multiselect("所有人", sorted(list(set([d['所有人'] for d in asset_data]))))
        filtered = [d for d in asset_data if (not search_q or search_q.lower() in d['知识库名称'].lower()) and (not f_owner or d['所有人'] in f_owner)]
        sc1, sc2, _ = st.columns([1, 1, 6])
        if sc1.button("✅ 全选", key="rg_v12_all"): st.session_state.v12_trigger=True; st.rerun()
        if sc2.button("❌ 反选", key="rg_v12_none"): st.session_state.v12_trigger=False; st.rerun()
        if st.session_state.get('v12_trigger'):
            for i in filtered: i["☑️"] = True
        edited = st.data_editor(pd.DataFrame(filtered), use_container_width=True, hide_index=True, key="rg_v12_editor")
        selected_kbs = edited[edited["☑️"] == True]["知识库名称"].tolist()
        if selected_kbs:
            st.divider(); st.markdown(f"**⚡ 批量操作 ({len(selected_kbs)})**")
            if st.button("🌍 设为公开", use_container_width=True, type="primary"):
                for k in selected_kbs: set_kb_public(k, True); st.rerun()
            if st.button("粉碎资产", use_container_width=True):
                import shutil
                for k in selected_kbs: shutil.rmtree(os.path.join(kb_storage_root, k)); st.rerun()

    # --- Tab 2: 用户与会话 (完全恢复新建功能) ---
    with tab_users:
        u_mode = st.radio("模块", ["👤 用户管理", "🎫 会话控制"], horizontal=True, key="v12_um")
        if u_mode == "👤 用户管理":
            user_list = [{"用户名": u, "角色": info.get('role'), "状态": "✅" if info.get('is_active', True) else "🚫", "创建": info.get('created_at','未知')[:10]} for u, info in users.items()]
            st.dataframe(pd.DataFrame(user_list), use_container_width=True, hide_index=True)
            st.divider()
            c1, c2 = st.columns(2)
            with c1:
                with st.expander("➕ 新增用户", expanded=False):
                    nu = st.text_input("用户名", key="v12_nu")
                    np = st.text_input("密码", type="password", key="v12_np")
                    nr = st.selectbox("角色", list(roles_config.keys()), key="v12_nr")
                    if st.button("创建用户", key="v12_btn_nr"):
                        from src.auth.user_auth import register_user
                        success, msg = register_user(nu, np, nr)
                        if success: st.success(msg); time.sleep(0.5); st.rerun()
                        else: st.error(msg)
            with c2:
                tu = st.selectbox("目标用户", list(users.keys()), key="v12_tu")
                if st.button("重置密码 (123456)", key="v12_btn_reset"):
                    from src.auth.user_auth import hash_password
                    users[tu]['password_hash'] = hash_password("123456"); save_users(users); st.toast("已重置")
        else:
            from src.auth.session_manager import get_session_settings, set_session_setting
            s_s = get_session_settings()
            new_g = st.slider("有效期 (天)", 1, 30, int(s_s.get("global_default", 7)), key="v12_gs")
            if st.button("更新策略", key="v12_gs_btn"): set_session_setting("global_default", new_g); st.success("已更新")

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

    # --- Tab 4: 行为审计 (全功能回归融合版) ---
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

    # --- Tab 5: 终端控制 ---
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
