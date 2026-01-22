import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
from src.auth.connection_manager import ConnectionManager
from src.kb.kb_manager import KBManager
from src.config.manifest_manager import ManifestManager

class UserProfileUI:
    """
    [v8.7.0] 统一用户中心 UI
    根据角色分发视图：
    - Admin: 进入全量资源治理工作台
    - User:  进入个人资产与连接管理中心
    """

    @staticmethod
    def render():
        current_role = st.session_state.get('role', 'guest')
        current_user = st.session_state.get('user', 'unknown')

        # === 管理员视图 ===
        if current_role == 'admin':
            UserProfileUI._render_admin_dashboard()
        else:
            # === 普通用户视图 ===
            UserProfileUI._render_user_dashboard(current_user)

    @staticmethod
    def _render_admin_dashboard():
        """渲染管理员治理台"""
        # 动态导入以支持热重载
        try:
            import src.auth.resource_governance as rg_mod
            import importlib
            importlib.reload(rg_mod)
            rg_mod.render_resource_governance_v19()
        except ImportError:
            st.error("❌ 无法加载管理员资源治理模块 (src.auth.resource_governance)")
        except Exception as e:
            st.error(f"❌ 加载管理视图失败: {e}")

    @staticmethod
    def _render_user_dashboard(username):
        """渲染个人用户中心"""
        st.header(f"👤 个人中心 - {username}")
        
        tab1, tab2 = st.tabs(["📦 我的资产", "🔌 数据连接"])
        
        # --- Tab 1: 我的知识库 ---
        with tab1:
            UserProfileUI._render_my_assets(username)
            
        # --- Tab 2: 个人数据库连接 ---
        with tab2:
            UserProfileUI._render_my_connections(username)

    @staticmethod
    def _render_my_assets(username):
        """渲染我的知识库资产"""
        kb_manager = KBManager()
        all_kbs = kb_manager.list_all()
        
        # 筛选属于当前用户的知识库
        # 规则1: 名称以 username_ 开头
        # 规则2: manifest 中 owner 字段匹配 (需要读取文件，稍慢但准确)
        my_kbs = []
        for kb in all_kbs:
            is_mine = False
            # 快速前缀检查
            if kb.startswith(f"{username}_"):
                is_mine = True
            else:
                # 深度元数据检查
                try:
                    kb_path = os.path.join(kb_manager.base_path, kb)
                    manifest_path = ManifestManager.get_path(kb_path)
                    if os.path.exists(manifest_path):
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                            if meta.get('owner') == username:
                                is_mine = True
                except: pass
            
            if is_mine:
                stats = kb_manager.get_stats(kb)
                my_kbs.append({
                    "名称": kb,
                    "文档数": stats.get('file_count', 0),
                    "大小": kb_manager.format_size(stats.get('size', 0)),
                    "创建时间": stats.get('created_time', 'N/A')
                })
        
        if my_kbs:
            st.info(f"📊 您共有 {len(my_kbs)} 个知识库")
            st.dataframe(
                pd.DataFrame(my_kbs),
                use_container_width=True,
                column_config={
                    "创建时间": st.column_config.DatetimeColumn(format="YYYY-MM-DD HH:mm")
                }
            )
        else:
            st.warning("📭 您暂时没有创建任何知识库")
            st.caption("💡 请在左侧侧边栏选择 '➕ 新建知识库' 来创建您的第一个资产。")

    @staticmethod
    def _render_my_connections(username):
        """渲染个人数据库连接配置"""
        conn_mgr = ConnectionManager()
        all_conns = conn_mgr.load_connections()
        
        # 筛选：仅显示自己创建的，或标记为 public 的 (暂未实现 public，仅 owner)
        my_conns = {k: v for k, v in all_conns.items() if v.get('owner') == username}
        
        col_list, col_form = st.columns([1, 2])
        
        # 左侧：连接列表
        with col_list:
            st.subheader("已配置连接")
            if my_conns:
                for alias in my_conns:
                    if st.button(f"🔌 {alias}", use_container_width=True, key=f"btn_conn_{alias}"):
                        st.session_state.editing_conn = alias
            else:
                st.caption("暂无配置")
            
            if st.button("➕ 新建连接", type="primary", use_container_width=True):
                st.session_state.editing_conn = None

        # 右侧：编辑/新建表单
        with col_form:
            target_alias = st.session_state.get('editing_conn')
            form_title = f"编辑: {target_alias}" if target_alias else "新建连接"
            st.subheader(form_title)
            
            # 加载现有数据
            default_data = {}
            if target_alias and target_alias in my_conns:
                default_data = my_conns[target_alias]
            
            with st.form("conn_form"):
                new_alias = st.text_input("连接名称 (Alias)", value=target_alias if target_alias else "", disabled=bool(target_alias))
                db_type = st.selectbox("数据库类型", ["MySQL", "PostgreSQL", "MSSQL", "ClickHouse", "Oracle", "SQLite"], 
                                     index=["MySQL", "PostgreSQL", "MSSQL", "ClickHouse", "Oracle", "SQLite"].index(default_data.get('type', 'MySQL')))
                
                c1, c2 = st.columns(2)
                host = c1.text_input("主机 (Host)", value=default_data.get('host', 'localhost'))
                port = c2.number_input("端口 (Port)", value=int(default_data.get('port', 3306)), step=1)
                
                c3, c4 = st.columns(2)
                user = c3.text_input("用户名", value=default_data.get('user', 'root'))
                password = c4.text_input("密码", value=default_data.get('password', ''), type="password")
                
                db_name = st.text_input("数据库名", value=default_data.get('database', ''))
                
                submitted = st.form_submit_button("💾 保存配置")
                
                if submitted:
                    if not new_alias:
                        st.error("请输入连接名称")
                    else:
                        # 强制标记 owner 为当前用户
                        success = conn_mgr.save_connection(new_alias, db_type, host, port, user, password, db_name, owner=username)
                        if success:
                            st.success(f"✅ 连接 '{new_alias}' 已保存")
                            st.rerun()
                        else:
                            st.error("❌ 保存失败")
            
            # 删除按钮 (仅限编辑模式)
            if target_alias:
                st.markdown("---")
                if st.button("🗑️ 删除此连接", type="secondary"):
                    if conn_mgr.delete_connection(target_alias):
                        st.toast(f"已删除 {target_alias}")
                        st.session_state.editing_conn = None
                        st.rerun()
                    else:
                        st.error("删除失败")
