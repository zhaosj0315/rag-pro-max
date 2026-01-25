import streamlit as st
import pandas as pd
from src.utils.mysql_manager import MySQLManager

class DBAdminUI:
    @staticmethod
    def render():
        st.header("🗄️ MySQL 数据库用户管理")
        st.caption("轻量级数据库用户与权限管理工具")

        # --- 1. 连接配置 ---
        # 默认隐藏配置，使用内置默认值
        with st.expander("🔌 数据库连接配置 (默认: localhost/root)", expanded=False):
            col1, col2 = st.columns(2)
            host = col1.text_input("Host", "localhost", key="db_host")
            port = col2.number_input("Port", 3306, step=1, key="db_port")
            
            col3, col4 = st.columns(2)
            user = col3.text_input("User", "root", key="db_user")
            # 预填用户提供的密码
            password = col4.text_input("Password", value="66315066", type="password", key="db_pass")
            
            if st.button("测试连接"):
                mgr = MySQLManager(host, int(port), user, password)
                try:
                    mgr.connect()
                    st.toast("✅ 连接成功!", icon="🎉")
                    mgr.close()
                except Exception as e:
                    st.error(f"连接失败: {e}")

        # 初始化管理器
        mgr = MySQLManager(host, int(port), user, password)

        # --- 2. 功能选项卡 ---
        tab1, tab2, tab3 = st.tabs(["👥 用户与权限", "➕ 新建用户", "🗑️ 危险操作"])

        with tab1:
            st.subheader("现有用户列表")
            try:
                users = mgr.get_users()
                if users:
                    df_users = pd.DataFrame(users)
                    st.dataframe(df_users, use_container_width=True, hide_index=True)
                    
                    st.divider()
                    st.subheader("🔒 权限配置")
                    
                    # 用户选择器
                    user_options = [f"{u['User']}@{u['Host']}" for u in users]
                    selected_user_str = st.selectbox("选择要管理的用户", user_options)
                    
                    if selected_user_str:
                        sel_user, sel_host = selected_user_str.split('@')
                        
                        # 显示当前权限
                        grants = mgr.get_grants(sel_user, sel_host)
                        with st.expander("📜 查看当前权限语句", expanded=False):
                            if grants:
                                for g in grants:
                                    st.code(g, language="sql")
                            else:
                                st.info("无法获取权限或无权限")

                        # 分配新权限
                        col_db, col_act = st.columns([3, 1])
                        with col_db:
                            all_dbs = mgr.get_databases()
                            # 排除系统库建议
                            sys_dbs = ['information_schema', 'mysql', 'performance_schema', 'sys']
                            rec_dbs = [d for d in all_dbs if d not in sys_dbs]
                            
                            target_dbs = st.multiselect("选择数据库 (可多选)", all_dbs, default=None, placeholder="选择数据库...")
                        
                        with col_act:
                            st.write("") # Spacer
                            st.write("") 
                            if st.button("🚀 授予读写权限", use_container_width=True, type="primary"):
                                if not target_dbs:
                                    st.warning("请至少选择一个数据库")
                                else:
                                    success_list = []
                                    fail_list = []
                                    for db in target_dbs:
                                        ok, msg = mgr.grant_privileges(sel_user, sel_host, db)
                                        if ok:
                                            success_list.append(db)
                                        else:
                                            fail_list.append(f"{db}: {msg}")
                                    
                                    if success_list:
                                        st.success(f"✅ 已成功授权: {', '.join(success_list)}")
                                    if fail_list:
                                        st.error(f"❌ 失败: {'; '.join(fail_list)}")
                else:
                    st.info("未找到用户")

            except Exception as e:
                st.error(f"操作失败 (请检查连接配置): {e}")

        with tab2:
            st.subheader("创建新用户")
            with st.form("create_user_form"):
                c1, c2 = st.columns(2)
                new_u = c1.text_input("用户名 (User)", placeholder="例如: analyst_01")
                new_h = c2.text_input("允许主机 (Host)", value="%", help="建议使用 '%' 以允许从任意IP (含Docker网关) 连接。若填 'localhost'，则仅限数据库本机访问。")
                new_p = st.text_input("密码 (Password)", type="password")
                
                submitted = st.form_submit_button("✅ 立即创建")
                if submitted:
                    if new_u and new_p:
                        ok, msg = mgr.create_user(new_u, new_p, new_h)
                        if ok:
                            st.success(f"用户 {new_u}@{new_h} 创建成功!")
                            st.rerun()
                        else:
                            st.error(f"创建失败: {msg}")
                    else:
                        st.warning("请填写完整的用户名和密码")
            
            st.info("""
            💡 **连接故障排查**:
            如果连接时报错 `Access denied for user 'user'@'192.168.65.1'`, 说明 MySQL 识别到的来源 IP 是 `192.168.65.1` (通常是 Docker 网关)。
            此时必须确保您创建的用户 Host 为 `%` 或该特定 IP，**不能**是 `localhost`。
            """)

        with tab3:
            st.error("⚠️ 危险区域")
            st.caption("删除用户将撤销其所有权限并无法恢复。")
            
            del_u_str = st.selectbox("选择要删除的用户", user_options if 'user_options' in locals() else [], key="del_user_sel")
            
            if st.button("🗑️ 永久删除该用户", type="primary"):
                if del_u_str:
                    d_user, d_host = del_u_str.split('@')
                    # 二次确认模拟 (Streamlit button instant action usually needs session state for proper confirm, keeping simple here)
                    ok, msg = mgr.drop_user(d_user, d_host)
                    if ok:
                        st.success(f"用户 {del_u_str} 已删除")
                        st.rerun()
                    else:
                        st.error(f"删除失败: {msg}")
