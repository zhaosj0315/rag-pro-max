import streamlit as st
import os
import json
import time
from src.auth.user_auth import load_users, save_users
from src.auth.session_manager import load_sharing_config, save_sharing_config, set_kb_public
from src.kb.kb_manager import KBManager

def render_admin_management():
    st.markdown("### 👥 系统用户与资源调度")
    
    users = load_users()
    sharing_config = load_sharing_config()
    public_kbs = sharing_config.get("public_kbs", [])
    
    # 1. 顶部统计
    s_col1, s_col2, s_col3 = st.columns(3)
    s_col1.metric("总注册用户", len(users))
    s_col2.metric("公开知识库", len(public_kbs))
    s_col3.metric("管理员", len([u for u in users.values() if u.get('role')=='admin']))
    
    st.divider()
    
    tab_batch, tab_users, tab_kbs, tab_audit = st.tabs(["⚡ 批量授权", "👤 用户台账", "📂 知识库分发", "📜 审计记录"])
    
    with tab_batch:
        # ... (原有代码保持不变)

        st.caption("一键管理多名用户的权限与访问权")
        
        # 批量操作逻辑
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
                            AuditLogger.log(st.session_state.get('user'), "BATCH_LOCK", f"批量封禁了 {len(selected_batch_users)} 名用户: {', '.join(selected_batch_users)}")
                            st.toast("账号已批量封禁")
                            time.sleep(1); st.rerun()

                    elif batch_action == "批量解封账号":
                        if st.button("🔓 立即执行解封"):
                            from src.auth.audit_logger import AuditLogger
                            for u in selected_batch_users:
                                users[u]['is_active'] = True
                            save_users(users)
                            AuditLogger.log(st.session_state.get('user'), "BATCH_UNLOCK", f"批量解封了 {len(selected_batch_users)} 名用户: {', '.join(selected_batch_users)}")
                            st.toast("账号已批量解封")
                            time.sleep(1); st.rerun()

    with tab_users:
        st.caption("管理账号生命周期、角色及禁用状态")
        for username, info in users.items():
            with st.expander(f"{'🟢' if info.get('is_active', True) else '🔴'} {username} - {info.get('role')}"):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    new_role = st.selectbox("角色修改", ["admin", "standard_user", "guest"], 
                                            index=["admin", "standard_user", "guest"].index(info.get('role', 'standard_user')),
                                            key=f"role_{username}")
                with c2:
                    is_active = st.toggle("允许登录", value=info.get('is_active', True), key=f"active_{username}")
                
                # 更新逻辑
                if new_role != info.get('role') or is_active != info.get('is_active'):
                    users[username]['role'] = new_role
                    users[username]['is_active'] = is_active
                    save_users(users)
                    st.toast(f"✅ {username} 的权限已更新")
                    st.rerun()

    with tab_kbs:
        st.caption("控制知识库的可见性：谁能看，谁能用")
        
        # 获取所有物理存在的库
        kb_manager = KBManager()
        # 假设 output_base 在 session_state 或全局
        kb_base = os.path.join(os.getcwd(), "vector_db_storage")
        kb_manager.base_path = kb_base
        all_kbs = kb_manager.list_all()
        
        for kb in all_kbs:
            with st.expander(f"📂 {kb} {' (🌍公开)' if kb in public_kbs else ' (🔒私有)'}"):
                # 共享开关
                is_pub = st.toggle("全系统公开可见 (含访客)", value=(kb in public_kbs), key=f"pub_{kb}")
                if is_pub != (kb in public_kbs):
                    set_kb_public(kb, is_pub)
                    st.rerun()
                
                if not is_pub:
                    st.markdown("**定向授权用户:**")
                    # 显示非管理员用户列表进行勾选
                    non_admins = [u for u in users.keys() if users[u].get('role') != 'admin']
                    current_whitelist = users.get('some_user', {}).get('kb_whitelist', []) # 此处逻辑需精细化
                    
                    # 针对每个用户更新其白名单
                    selected_users = []
                    for u in non_admins:
                        u_whitelist = users[u].get('kb_whitelist', [])
                        if st.checkbox(f"授权给 {u}", value=(kb in u_whitelist), key=f"share_{kb}_{u}"):
                            if kb not in u_whitelist:
                                users[u]['kb_whitelist'] = u_whitelist + [kb]
                                save_users(users)
                                st.toast(f"✅ 已授权给 {u}")
                        else:
                            if kb in u_whitelist:
                                u_whitelist.remove(kb)
                                users[u]['kb_whitelist'] = u_whitelist
                                users[u]['kb_whitelist'] = u_whitelist
                                save_users(users)
                                st.toast(f"已取消 {u} 的授权")

    with tab_audit:
        from src.auth.audit_logger import AuditLogger
        st.caption("记录全系统的关键安全事件与资产操作轨迹")
        
        logs = AuditLogger.get_logs()
        if not logs:
            st.info("暂无审计记录")
        else:
            # 日志过滤工具栏
            f_col1, f_col2 = st.columns([1, 1])
            with f_col1:
                filter_user = st.selectbox("按用户筛选", ["全部"] + sorted(list(set(l['user'] for l in logs))))
            with f_col2:
                filter_action = st.selectbox("按动作筛选", ["全部"] + sorted(list(set(l['action'] for l in logs))))
            
            # 执行过滤
            display_logs = logs
            if filter_user != "全部":
                display_logs = [l for l in display_logs if l['user'] == filter_user]
            if filter_action != "全部":
                display_logs = [l for l in display_logs if l['action'] == filter_action]
            
            # 渲染日志时间轴/表格
            for l in display_logs[:100]: # 仅显示最近100条
                status_color = "🔴" if l['status'] == 'failed' else "🟡" if l['status'] == 'warning' else "🟢"
                timestamp = l['timestamp'].split('T')[1].split('.')[0] # 仅显示时间
                date = l['timestamp'].split('T')[0]
                
                with st.container(border=True):
                    st.markdown(f"{status_color} **{l['action']}** | `{l['user']}` | {date} {timestamp}")
                    st.caption(f"📝 {l['details']}")

