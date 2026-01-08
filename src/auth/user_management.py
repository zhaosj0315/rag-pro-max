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
    
    tab_batch, tab_users, tab_kbs, tab_roles, tab_audit = st.tabs(["⚡ 批量授权", "👤 用户台账", "📂 知识库分发", "🎭 角色定义", "📜 审计记录"])
    
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
        st.caption("控制知识库的可见性：谁能看，谁能用")
        kb_manager = KBManager()
        kb_base = os.path.join(os.getcwd(), "vector_db_storage")
        kb_manager.base_path = kb_base
        all_kbs = kb_manager.list_all()
        
        for kb in all_kbs:
            with st.expander(f"📂 {kb} {' (🌍公开)' if kb in public_kbs else ' (🔒私有)'}"):
                is_pub = st.toggle("全系统公开可见 (含访客)", value=(kb in public_kbs), key=f"pub_{kb}")
                if is_pub != (kb in public_kbs):
                    set_kb_public(kb, is_pub)
                    st.rerun()
                
                if not is_pub:
                    st.markdown("**定向授权用户:**")
                    for u, u_info in users.items():
                        if u_info.get('role') != 'admin':
                            u_whitelist = u_info.get('kb_whitelist', [])
                            if st.checkbox(f"授权给 {u}", value=(kb in u_whitelist), key=f"share_{kb}_{u}"):
                                if kb not in u_whitelist:
                                    users[u]['kb_whitelist'] = u_whitelist + [kb]
                                    save_users(users)
                                    st.toast(f"✅ 已授权给 {u}")
                            else:
                                if kb in u_whitelist:
                                    u_whitelist.remove(kb)
                                    users[u]['kb_whitelist'] = u_whitelist
                                    save_users(users)
                                    st.toast(f"已取消 {u} 的授权")

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