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

def render_resource_governance():
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
    
    # --- Tab 1: 资源治理 (资源矩阵) ---
    with tab_dist:
        st.caption("全域资源控制台：统一管理知识库的物理生命周期与访问权限")
        
        # 资源矩阵模式 (增强版)
        from src.config.manifest_manager import ManifestManager
        import datetime
        kb_storage_root = os.path.join(os.getcwd(), "vector_db_storage")
        
        # 1. 构建详细资产数据
        asset_data = []
        for kb in all_kbs:
            kb_path = os.path.join(kb_storage_root, kb)
            manifest = ManifestManager.load(kb_path)
            
            # 物理信息统计
            total_size = 0
                file_count = 0
                doc_count = 0
                last_modified = None
                
                try:
                    for root, _, files in os.walk(kb_path):
                        for f in files:
                            file_path = os.path.join(root, f)
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            file_count += 1
                            
                            # 统计文档数量（排除系统文件）
                            if not f.startswith('.') and f.endswith(('.txt', '.pdf', '.docx', '.md')):
                                doc_count += 1
                            
                            # 获取最后修改时间
                            mod_time = os.path.getmtime(file_path)
                            if not last_modified or mod_time > last_modified:
                                last_modified = mod_time
                except: 
                    pass
                
                # 创建时间和最后修改时间
                created_time = manifest.get('created_at', '未知')
                if created_time != '未知':
                    try:
                        created_time = datetime.datetime.fromisoformat(created_time.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                    except:
                        created_time = created_time[:16] if len(created_time) > 16 else created_time
                
                last_mod_str = '未知'
                if last_modified:
                    last_mod_str = datetime.datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M')
                
                # 权限信息
                is_public = kb in sharing_config.get("public_kbs", [])
                shared_roles = [r for r, kbs in sharing_config.get('role_sharing', {}).items() if kb in kbs]
                shared_users = [u for u, info in users.items() if kb in info.get('kb_whitelist', [])]
                
                # 状态标签
                status_tags = []
                if is_public: status_tags.append("🌐 公开")
                if shared_roles: status_tags.append(f"🎭 {len(shared_roles)}角色")
                if shared_users: status_tags.append(f"👤 {len(shared_users)}用户")
                if not status_tags: status_tags.append("🔒 私有")
                
                # 知识库类型判断
                kb_type = "📄 文档库"
                if "web" in kb.lower() or "crawl" in kb.lower():
                    kb_type = "🌐 网页库"
                elif "chat" in kb.lower():
                    kb_type = "💬 对话库"
                
                asset_data.append({
                    "☑️": False,
                    "知识库名称": kb,
                    "类型": kb_type,
                    "所有者": manifest.get('owner', 'admin'),
                    "创建时间": created_time,
                    "最后修改": last_mod_str,
                    "文档数": doc_count,
                    "总文件": file_count,
                    "占用空间": format_size(total_size),
                    "权限状态": " | ".join(status_tags),
                    "描述": manifest.get('description', '无描述')[:30] + ('...' if len(manifest.get('description', '')) > 30 else '')
                })

            # 2. 增强筛选器
            with st.container(border=True):
                st.markdown("**🔍 资源精准筛选与批量选择**")
                
                # 第一行：搜索和基础筛选
                fc1, fc2, fc3, fc4 = st.columns([2, 1, 1, 1])
                search_q = fc1.text_input("🔍 名称搜索", placeholder="输入关键词...", key="res_search_q")
                
                all_owners = sorted(list(set([d['所有者'] for d in asset_data]))) if asset_data else []
                owner_f = fc2.multiselect("👤 所有者", options=all_owners, key="res_owner_f")
                
                all_types = sorted(list(set([d['类型'] for d in asset_data]))) if asset_data else []
                type_f = fc3.multiselect("📂 类型", options=all_types, key="res_type_f")
                
                status_f = fc4.multiselect("🔐 权限", ["🌐 公开", "🔒 私有", "已分享"], key="res_status_f")
                
                # 第二行：批量选择操作
                st.markdown("**⚡ 快速批量选择**")
                
                # 基础全选操作
                bc1, bc2, bc3, bc4 = st.columns(4)
                if bc1.button("✅ 全选", use_container_width=True):
                    st.session_state.batch_select_all = True
                if bc2.button("❌ 全不选", use_container_width=True):
                    st.session_state.batch_select_none = True
                if bc3.button("🔍 高级全选", use_container_width=True):
                    st.session_state.show_advanced_select = True
                if bc4.button("📊 统计选择", use_container_width=True):
                    st.session_state.show_select_stats = True
                
                # 高级全选面板
                if st.session_state.get('show_advanced_select'):
                    with st.container(border=True):
                        st.markdown("**🎯 高级批量选择**")
                        
                        # 按所有者全选
                        st.markdown("**👤 按所有者全选**")
                        ac1, ac2, ac3 = st.columns(3)
                        all_owners = sorted(list(set([d['所有者'] for d in asset_data]))) if asset_data else []
                        
                        with ac1:
                            select_owner = st.selectbox("选择所有者", ["-- 请选择 --"] + all_owners, key="select_owner")
                            if st.button("✅ 全选该用户的库", use_container_width=True) and select_owner != "-- 请选择 --":
                                st.session_state.batch_select_by_owner = select_owner
                        
                        with ac2:
                            if st.button("👤 全选我的库", use_container_width=True):
                                st.session_state.batch_select_mine = True
                            if st.button("👥 全选他人的库", use_container_width=True):
                                st.session_state.batch_select_others = True
                        
                        with ac3:
                            if st.button("🔥 全选活跃库", use_container_width=True):
                                st.session_state.batch_select_active = True
                            if st.button("😴 全选冷门库", use_container_width=True):
                                st.session_state.batch_select_inactive = True
                        
                        st.divider()
                        
                        # 按时间段全选
                        st.markdown("**📅 按时间段全选**")
                        tc1, tc2, tc3 = st.columns(3)
                        
                        with tc1:
                            if st.button("🆕 全选今天创建", use_container_width=True):
                                st.session_state.batch_select_today = True
                            if st.button("📅 全选本周创建", use_container_width=True):
                                st.session_state.batch_select_week = True
                            if st.button("📆 全选本月创建", use_container_width=True):
                                st.session_state.batch_select_month = True
                        
                        with tc2:
                            # 自定义时间范围
                            st.markdown("**自定义时间范围**")
                            from datetime import datetime, date
                            start_date = st.date_input("开始日期", key="custom_start_date")
                            end_date = st.date_input("结束日期", key="custom_end_date")
                            if st.button("📅 全选时间段", use_container_width=True):
                                st.session_state.batch_select_custom_date = (start_date, end_date)
                        
                        with tc3:
                            if st.button("🔥 全选最近修改", use_container_width=True):
                                st.session_state.batch_select_recent_modified = True
                            if st.button("⏰ 全选很久未动", use_container_width=True):
                                st.session_state.batch_select_old_modified = True
                        
                        st.divider()
                        
                        # 按属性全选
                        st.markdown("**🏷️ 按属性全选**")
                        pc1, pc2, pc3 = st.columns(3)
                        
                        with pc1:
                            if st.button("🌐 全选公开库", use_container_width=True):
                                st.session_state.batch_select_public = True
                            if st.button("🔒 全选私有库", use_container_width=True):
                                st.session_state.batch_select_private = True
                        
                        with pc2:
                            if st.button("📄 全选文档库", use_container_width=True):
                                st.session_state.batch_select_doc = True
                            if st.button("🌐 全选网页库", use_container_width=True):
                                st.session_state.batch_select_web = True
                            if st.button("💬 全选对话库", use_container_width=True):
                                st.session_state.batch_select_chat = True
                        
                        with pc3:
                            if st.button("📊 全选大文件库", use_container_width=True):
                                st.session_state.batch_select_large = True
                            if st.button("📁 全选小文件库", use_container_width=True):
                                st.session_state.batch_select_small = True
                        
                        # 关闭按钮
                        if st.button("❌ 关闭高级选择", use_container_width=True):
                            st.session_state.show_advanced_select = False
            
            
            # 3. 执行筛选逻辑
            filtered_data = []
            current_user = st.session_state.get('user', 'admin')
            
            for item in asset_data:
                match = True
                if search_q and search_q.lower() not in item['知识库名称'].lower(): match = False
                if owner_f and item['所有者'] not in owner_f: match = False
                if type_f and item['类型'] not in type_f: match = False
                if status_f:
                    if "🌐 公开" in status_f and "🌐 公开" not in item['权限状态']: match = False
                    if "🔒 私有" in status_f and "🔒 私有" not in item['权限状态']: match = False
                    if "已分享" in status_f and "🔒 私有" in item['权限状态'] and "🌐 公开" not in item['权限状态']: match = False
                if match: filtered_data.append(item)
            
            # 4. 处理批量选择状态
            from datetime import datetime, timedelta
            
            if st.session_state.get('batch_select_all'):
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = True
                st.session_state.batch_select_all = False
                
            if st.session_state.get('batch_select_none'):
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = False
                st.session_state.batch_select_none = False
            
            # 按所有者选择
            if st.session_state.get('batch_select_by_owner'):
                owner = st.session_state.batch_select_by_owner
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = item['所有者'] == owner
                st.session_state.batch_select_by_owner = None
                
            if st.session_state.get('batch_select_mine'):
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = item['所有者'] == current_user
                st.session_state.batch_select_mine = False
                
            if st.session_state.get('batch_select_others'):
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = item['所有者'] != current_user
                st.session_state.batch_select_others = False
            
            # 按权限状态选择
            if st.session_state.get('batch_select_public'):
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = "🌐 公开" in item['权限状态']
                st.session_state.batch_select_public = False
                
            if st.session_state.get('batch_select_private'):
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = "🔒 私有" in item['权限状态']
                st.session_state.batch_select_private = False
            
            # 按类型选择
            if st.session_state.get('batch_select_doc'):
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = "📄 文档库" in item['类型']
                st.session_state.batch_select_doc = False
                
            if st.session_state.get('batch_select_web'):
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = "🌐 网页库" in item['类型']
                st.session_state.batch_select_web = False
                
            if st.session_state.get('batch_select_chat'):
                for i, item in enumerate(filtered_data):
                    filtered_data[i]['☑️'] = "💬 对话库" in item['类型']
                st.session_state.batch_select_chat = False
            
            # 按时间选择
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            month_ago = today - timedelta(days=30)
            
            if st.session_state.get('batch_select_today'):
                for i, item in enumerate(filtered_data):
                    try:
                        create_date = datetime.strptime(item['创建时间'][:10], '%Y-%m-%d').date()
                        filtered_data[i]['☑️'] = create_date == today
                    except:
                        filtered_data[i]['☑️'] = False
                st.session_state.batch_select_today = False
                
            if st.session_state.get('batch_select_week'):
                for i, item in enumerate(filtered_data):
                    try:
                        create_date = datetime.strptime(item['创建时间'][:10], '%Y-%m-%d').date()
                        filtered_data[i]['☑️'] = create_date >= week_ago
                    except:
                        filtered_data[i]['☑️'] = False
                st.session_state.batch_select_week = False
                
            if st.session_state.get('batch_select_month'):
                for i, item in enumerate(filtered_data):
                    try:
                        create_date = datetime.strptime(item['创建时间'][:10], '%Y-%m-%d').date()
                        filtered_data[i]['☑️'] = create_date >= month_ago
                    except:
                        filtered_data[i]['☑️'] = False
                st.session_state.batch_select_month = False
            
            # 自定义时间范围选择
            if st.session_state.get('batch_select_custom_date'):
                start_date, end_date = st.session_state.batch_select_custom_date
                for i, item in enumerate(filtered_data):
                    try:
                        create_date = datetime.strptime(item['创建时间'][:10], '%Y-%m-%d').date()
                        filtered_data[i]['☑️'] = start_date <= create_date <= end_date
                    except:
                        filtered_data[i]['☑️'] = False
                st.session_state.batch_select_custom_date = None
            
            # 按文件大小选择
            if st.session_state.get('batch_select_large'):
                for i, item in enumerate(filtered_data):
                    # 假设大于100MB为大文件库
                    size_str = item['占用空间']
                    is_large = 'GB' in size_str or ('MB' in size_str and float(size_str.split('MB')[0].strip()) > 100)
                    filtered_data[i]['☑️'] = is_large
                st.session_state.batch_select_large = False
                
            if st.session_state.get('batch_select_small'):
                for i, item in enumerate(filtered_data):
                    # 假设小于10MB为小文件库
                    size_str = item['占用空间']
                    is_small = 'KB' in size_str or ('MB' in size_str and float(size_str.split('MB')[0].strip()) < 10)
                    filtered_data[i]['☑️'] = is_small
                st.session_state.batch_select_small = False
            
            # 按活跃度选择
            if st.session_state.get('batch_select_active'):
                # 最近7天有修改的为活跃库
                for i, item in enumerate(filtered_data):
                    try:
                        mod_date = datetime.strptime(item['最后修改'][:10], '%Y-%m-%d').date()
                        filtered_data[i]['☑️'] = mod_date >= week_ago
                    except:
                        filtered_data[i]['☑️'] = False
                st.session_state.batch_select_active = False
                
            if st.session_state.get('batch_select_inactive'):
                # 超过30天未修改的为冷门库
                for i, item in enumerate(filtered_data):
                    try:
                        mod_date = datetime.strptime(item['最后修改'][:10], '%Y-%m-%d').date()
                        filtered_data[i]['☑️'] = mod_date < month_ago
                    except:
                        filtered_data[i]['☑️'] = item['最后修改'] == '未知'
                st.session_state.batch_select_inactive = False
            
            if st.session_state.get('batch_select_recent_modified'):
                # 最近3天修改的
                recent = today - timedelta(days=3)
                for i, item in enumerate(filtered_data):
                    try:
                        mod_date = datetime.strptime(item['最后修改'][:10], '%Y-%m-%d').date()
                        filtered_data[i]['☑️'] = mod_date >= recent
                    except:
                        filtered_data[i]['☑️'] = False
                st.session_state.batch_select_recent_modified = False
                
            if st.session_state.get('batch_select_old_modified'):
                # 超过60天未修改的
                old = today - timedelta(days=60)
                for i, item in enumerate(filtered_data):
                    try:
                        mod_date = datetime.strptime(item['最后修改'][:10], '%Y-%m-%d').date()
                        filtered_data[i]['☑️'] = mod_date < old
                    except:
                        filtered_data[i]['☑️'] = item['最后修改'] == '未知'
                st.session_state.batch_select_old_modified = False

            # 5. 显示增强数据表
            if not filtered_data:
                st.info("🔍 未找到匹配的知识库资源")
            else:
                st.markdown(f"**📊 资源总览** (共 {len(filtered_data)} 个知识库)")
                
                # 添加表格上方的全选控制
                col_info, col_select, col_master = st.columns([2, 1, 1])
                with col_info:
                    selected_count = sum(1 for item in filtered_data if item.get('☑️', False))
                    st.info(f"📋 当前已选择 {selected_count} / {len(filtered_data)} 个知识库")
                
                with col_select:
                    if st.button("🔄 刷新选择状态", use_container_width=True):
                        st.rerun()
                
                with col_master:
                    # 主控全选按钮
                    if selected_count == len(filtered_data) and len(filtered_data) > 0:
                        if st.button("❌ 取消全选", use_container_width=True, type="secondary"):
                            for i in range(len(filtered_data)):
                                filtered_data[i]['☑️'] = False
                            st.rerun()
                    else:
                        if st.button("✅ 全选当前页", use_container_width=True, type="primary"):
                            for i in range(len(filtered_data)):
                                filtered_data[i]['☑️'] = True
                            st.rerun()
                
                df_assets = pd.DataFrame(filtered_data)
                edited_df = st.data_editor(
                    df_assets, 
                    use_container_width=True, 
                    hide_index=True,
                    height=400,
                    column_config={
                        "☑️": st.column_config.CheckboxColumn("选择", width="small", default=False),
                        "知识库名称": st.column_config.TextColumn("知识库名称", width="medium"),
                        "类型": st.column_config.TextColumn("类型", width="small"),
                        "所有者": st.column_config.TextColumn("所有者", width="small"),
                        "创建时间": st.column_config.TextColumn("创建时间", width="medium"),
                        "最后修改": st.column_config.TextColumn("最后修改", width="medium"),
                        "文档数": st.column_config.NumberColumn("文档数", width="small"),
                        "总文件": st.column_config.NumberColumn("总文件", width="small"),
                        "占用空间": st.column_config.TextColumn("占用空间", width="small"),
                        "权限状态": st.column_config.TextColumn("权限状态", width="medium"),
                        "描述": st.column_config.TextColumn("描述", width="large")
                    },
                    key="enhanced_resource_editor"
                )
                
                # 获取选中项
                selected_kbs = edited_df[edited_df["☑️"] == True]["知识库名称"].tolist()
                
                if selected_kbs:
                    st.divider()
                    st.markdown(f"**⚡ 批量操作面板** ({len(selected_kbs)} 个已选中)")
                    
                    # 显示选中的知识库
                    with st.expander(f"📋 查看选中项 ({len(selected_kbs)}个)", expanded=False):
                        selected_info = edited_df[edited_df["☑️"] == True][["知识库名称", "所有者", "权限状态", "占用空间"]]
                        st.dataframe(selected_info, use_container_width=True, hide_index=True)
                    
                    # 操作区域分栏
                    op_tab1, op_tab2, op_tab3 = st.tabs(["🔐 权限管理", "👤 所有权转移", "🗑️ 资产处置"])
                    
                    with op_tab1:
                        st.markdown("**🔐 权限批量管理**")
                        c_p1, c_p2, c_p3 = st.columns(3)
                        
                        if c_p1.button("🌍 设为全站公开", use_container_width=True, type="primary"):
                            for k in selected_kbs: set_kb_public(k, True)
                            AuditLogger.log(st.session_state.get('user'), "KB_PUBLIC_BATCH", f"将 {len(selected_kbs)} 个库设为公开", ip=get_client_ip())
                            st.success(f"✅ 已将 {len(selected_kbs)} 个知识库设为公开")
                            time.sleep(1); st.rerun()
                            
                        if c_p2.button("🔒 撤销分享(变私有)", use_container_width=True):
                            sc = load_sharing_config()
                            for k in selected_kbs:
                                if k in sc.get('public_kbs', []): sc['public_kbs'].remove(k)
                                for r in sc.get('role_sharing', {}):
                                    if k in sc['role_sharing'][r]: sc['role_sharing'][r].remove(k)
                            save_sharing_config(sc)
                            AuditLogger.log(st.session_state.get('user'), "KB_PRIV_BATCH", f"撤销 {len(selected_kbs)} 个库的分享状态", status="warning", ip=get_client_ip())
                            st.success(f"✅ 已将 {len(selected_kbs)} 个知识库设为私有")
                            time.sleep(1); st.rerun()
                        
                        # 精准分发
                        with c_p3:
                            with st.popover("🤝 精准分发", use_container_width=True):
                                st.markdown("**🎯 选择分发目标**")
                                
                                # 按角色分发
                                st.markdown("**🎭 按角色分发**")
                                target_roles = st.multiselect("选择角色", options=list(roles_config.keys()), key="batch_roles")
                                
                                # 按用户类型分发
                                st.markdown("**👥 按用户类型分发**")
                                user_types = st.multiselect("选择用户类型", [
                                    "🆕 新注册用户", "🔥 活跃用户", "😴 非活跃用户", "🎯 特定角色用户"
                                ], key="batch_user_types")
                                
                                # 手动选择用户
                                st.markdown("**👤 手动选择用户**")
                                non_admin_users = [u for u in users.keys() if users[u].get('role') != 'admin']
                                target_users = st.multiselect("选择具体用户", options=non_admin_users, key="batch_users")
                                
                                # 一键选择所有用户
                                if st.checkbox("🌍 分发给所有用户", key="dist_all_users"):
                                    target_users = non_admin_users
                                
                                # 执行分发
                                if st.button("🚀 执行批量分发", type="primary"):
                                    # 收集所有目标用户
                                    all_target_users = set(target_users)
                                    
                                    # 按用户类型添加用户
                                    if "🆕 新注册用户" in user_types:
                                        # 最近7天注册的用户
                                        from datetime import datetime, timedelta
                                        week_ago = datetime.now() - timedelta(days=7)
                                        for u, info in users.items():
                                            if info.get('role') != 'admin':
                                                created_at = info.get('created_at', '')
                                                try:
                                                    if created_at and datetime.fromisoformat(created_at.replace('Z', '+00:00')) > week_ago:
                                                        all_target_users.add(u)
                                                except: pass
                                    
                                    if "🔥 活跃用户" in user_types:
                                        # 最近登录的用户
                                        for u, info in users.items():
                                            if info.get('role') != 'admin' and info.get('last_login'):
                                                all_target_users.add(u)
                                    
                                    if "😴 非活跃用户" in user_types:
                                        # 从未登录或很久没登录的用户
                                        for u, info in users.items():
                                            if info.get('role') != 'admin' and not info.get('last_login'):
                                                all_target_users.add(u)
                                    
                                    if "🎯 特定角色用户" in user_types and target_roles:
                                        # 特定角色的用户
                                        for u, info in users.items():
                                            if info.get('role') in target_roles:
                                                all_target_users.add(u)
                                    
                                    # 执行分发
                                    s_conf = load_sharing_config()
                                    
                                    # 角色分发
                                    for r in target_roles:
                                        if 'role_sharing' not in s_conf:
                                            s_conf['role_sharing'] = {}
                                        s_conf['role_sharing'][r] = list(set(s_conf.get('role_sharing',{}).get(r,[])).union(set(selected_kbs)))
                                    
                                    save_sharing_config(s_conf)
                                    
                                    # 用户分发
                                    for u in all_target_users:
                                        if u in users:
                                            users[u]['kb_whitelist'] = list(set(users[u].get('kb_whitelist',[])).union(set(selected_kbs)))
                                    
                                    save_users(users)
                                    
                                    # 记录审计日志
                                    dist_summary = f"角色:{len(target_roles)}个, 用户:{len(all_target_users)}个, 知识库:{len(selected_kbs)}个"
                                    AuditLogger.log(st.session_state.get('user'), "KB_MASS_DIST", f"大规模分发 - {dist_summary}", ip=get_client_ip())
                                    
                                    st.success(f"✅ 已将 {len(selected_kbs)} 个知识库分发给 {len(target_roles)} 个角色和 {len(all_target_users)} 个用户")
                                    time.sleep(1); st.rerun()
                                
                                # 分发预览
                                if target_roles or target_users or user_types:
                                    st.markdown("**📋 分发预览**")
                                    if target_roles:
                                        st.info(f"🎭 将分发给角色: {', '.join(target_roles)}")
                                    if target_users:
                                        st.info(f"👤 将分发给用户: {len(target_users)} 个")
                                    if user_types:
                                        st.info(f"👥 将分发给用户类型: {', '.join(user_types)}")
                                    st.warning(f"📦 共 {len(selected_kbs)} 个知识库将被分发")

                    with op_tab2:
                        st.markdown("**👤 所有权批量转移**")
                        c_o1, c_o2 = st.columns([3, 1])
                        
                        target_owner = c_o1.selectbox("选择新所有者", options=list(users.keys()), key="batch_transfer_owner")
                        if c_o2.button("🔄 执行转移", type="primary", use_container_width=True):
                            success_count = 0
                            for k in selected_kbs:
                                try:
                                    kp = os.path.join(kb_storage_root, k)
                                    manifest_path = os.path.join(kp, "manifest.json")
                                    if os.path.exists(manifest_path):
                                        with open(manifest_path, 'r', encoding='utf-8') as f: mf = json.load(f)
                                        old_owner = mf.get('owner', 'admin')
                                        mf['owner'] = target_owner
                                        mf['transferred_at'] = datetime.datetime.now().isoformat()
                                        mf['transferred_from'] = old_owner
                                        with open(manifest_path, 'w', encoding='utf-8') as f: json.dump(mf, f, indent=4, ensure_ascii=False)
                                        success_count += 1
                                except: pass
                            if success_count:
                                AuditLogger.log(st.session_state.get('user'), "BATCH_TRANSFER", f"转移 {success_count} 个资产给 {target_owner}", ip=get_client_ip())
                                st.success(f"✅ 已成功转移 {success_count} 个知识库给 {target_owner}")
                                time.sleep(1); st.rerun()
                        
                        # 显示转移预览
                        if target_owner:
                            st.info(f"📋 将转移 {len(selected_kbs)} 个知识库的所有权给用户: **{target_owner}**")

                    with op_tab3:
                        st.markdown("**🗑️ 危险操作区域**")
                        st.warning("⚠️ 以下操作不可逆，请谨慎操作！")
                        
                        # 备份选项
                        backup_before_delete = st.checkbox("🛡️ 删除前自动备份", value=True)
                        
                        c_d1, c_d2 = st.columns(2)
                        
                        # 清空知识库内容（保留结构）
                        if c_d1.button("🧹 清空内容(保留结构)", use_container_width=True, type="secondary"):
                            cleared_count = 0
                            for k in selected_kbs:
                                try:
                                    kb_path = os.path.join(kb_storage_root, k)
                                    if backup_before_delete:
                                        # 创建备份
                                        backup_path = f"backups/{k}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                        os.makedirs(backup_path, exist_ok=True)
                                        import shutil
                                        shutil.copytree(kb_path, backup_path, dirs_exist_ok=True)
                                    
                                    # 清空内容但保留manifest
                                    for item in os.listdir(kb_path):
                                        if item != 'manifest.json':
                                            item_path = os.path.join(kb_path, item)
                                            if os.path.isdir(item_path):
                                                shutil.rmtree(item_path)
                                            else:
                                                os.remove(item_path)
                                    cleared_count += 1
                                except: pass
                            
                            if cleared_count:
                                AuditLogger.log(st.session_state.get('user'), "BATCH_CLEAR", f"清空 {cleared_count} 个知识库内容", status="warning", ip=get_client_ip())
                                st.success(f"✅ 已清空 {cleared_count} 个知识库的内容")
                                time.sleep(1); st.rerun()
                        
                        # 完全删除
                        if c_d2.button("💥 完全删除(不可逆)", use_container_width=True, type="secondary"):
                            import shutil
                            deleted_count = 0
                            for k in selected_kbs:
                                try:
                                    kb_path = os.path.join(kb_storage_root, k)
                                    if backup_before_delete:
                                        # 创建备份
                                        backup_path = f"backups/{k}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                        os.makedirs(backup_path, exist_ok=True)
                                        shutil.copytree(kb_path, backup_path, dirs_exist_ok=True)
                                    
                                    # 删除知识库
                                    shutil.rmtree(kb_path)
                                    # 删除对话历史
                                    if os.path.exists(f"chat_histories/{k}.json"): 
                                        os.remove(f"chat_histories/{k}.json")
                                    deleted_count += 1
                                except: pass
                            
                            if deleted_count:
                                AuditLogger.log(st.session_state.get('user'), "BATCH_DELETE", f"物理删除 {deleted_count} 个资产", status="warning", ip=get_client_ip())
                                st.error(f"🗑️ 已删除 {deleted_count} 个知识库")
                                time.sleep(1); st.rerun()
                        
                        # 删除预览
                        st.error(f"⚠️ 将影响 {len(selected_kbs)} 个知识库")
                        with st.expander("🔍 查看将被删除的知识库"):
                            for kb in selected_kbs:
                                kb_info = next((item for item in filtered_data if item['知识库名称'] == kb), {})
                                st.text(f"• {kb} (所有者: {kb_info.get('所有者', '未知')}, 大小: {kb_info.get('占用空间', '未知')})")
                else:
                    st.info("💡 请先选择要操作的知识库")

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

    # --- Tab 6: 终端控制 (新增) ---
    with tab_term:
        # 多重权限验证：确保只有管理员可以访问
        current_user = st.session_state.get('user')
        current_role = st.session_state.get('role')
        
        if not current_user or current_role != 'admin':
            st.error("⛔ 权限不足：仅超级管理员可访问终端")
            st.warning("🔒 此功能仅限系统管理员使用，如需访问请联系管理员")
            return
        
        # 二次确认管理员身份
        if current_user != 'admin':
            st.error("⛔ 严格限制：终端控制仅限 admin 用户使用")
            st.warning("🚨 当前用户虽为管理员角色，但终端控制功能仅限 admin 账户")
            return
        
        # 隐藏激活机制 - 需要输入特定密码才能显示终端控制
        st.markdown("### 🔐 系统维护工具")
        
        # 使用隐藏的文本输入框
        secret_key = st.text_input("维护密钥", type="password", key="terminal_secret", 
                                  help="请输入系统维护密钥以访问高级功能")
        
        # 检查密钥（你可以修改这个密钥）
        TERMINAL_SECRET = "rag-pro-max-2026"  # 修改为你想要的密钥
        
        if secret_key != TERMINAL_SECRET:
            if secret_key:  # 如果输入了错误密钥
                st.error("❌ 维护密钥错误")
            st.info("💡 请输入正确的维护密钥以访问系统终端")
            return
        
        # 管理员身份确认通过，显示终端控制界面
        st.caption("🚀 本地 SSH 终端 (WebSSH)")
        st.error("⚠️ 危险区域：此功能提供完整系统访问权限，请谨慎操作！")
        st.warning("🔐 仅使用本机 macOS 用户名/密码登录")
        
        # 记录管理员访问终端控制的行为
        from src.auth.audit_logger import AuditLogger
        AuditLogger.log(current_user, "TERMINAL_ACCESS", "管理员访问终端控制功能", 
                       action_type="SECURITY", ip=get_client_ip())
            
            col_svc, col_status = st.columns([1, 4])
            with col_svc:
                if st.button("启动终端服务 (8899)", key="btn_start_term", use_container_width=True):
                    import subprocess
                    # 使用 wssh 启动服务，监听 8899 端口，--fbidhttp=False 允许非 HTTP 访问 (WS)
                    # 注意：在后台运行，不阻塞主进程
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

            # 检查服务状态
            import requests
            import streamlit.components.v1 as components
            terminal_url = "http://localhost:8899"
            
            try:
                # 检查服务是否响应
                response = requests.get(terminal_url, timeout=2)
                if response.status_code == 200:
                    st.success("✅ WebSSH 服务运行正常")
                    
                    # 提供两种访问方式
                    tab1, tab2 = st.tabs(["🖥️ 内嵌终端", "🔗 新窗口打开"])
                    
                    with tab1:
                        components.iframe(terminal_url, height=600, scrolling=True)
                    
                    with tab2:
                        st.markdown(f"**直接访问链接：** [{terminal_url}]({terminal_url})")
                        st.info("💡 如果内嵌终端无法正常显示，请点击上方链接在新窗口中打开")
                        
                else:
                    st.error(f"❌ WebSSH 服务响应异常 (状态码: {response.status_code})")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ 无法连接到 WebSSH 服务 (端口 8899)")
                st.info("请点击上方'启动终端服务'按钮启动服务")
            except Exception as e:
                st.error(f"❌ 连接检查失败: {e}")
                st.markdown(f"**备用访问：** [{terminal_url}]({terminal_url})")

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024: return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def get_client_ip():
    from src.common.utils import get_client_ip
    try: return get_client_ip()
    except: return "127.0.0.1"
