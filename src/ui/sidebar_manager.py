"""
侧边栏管理器 - 负责整个侧边栏的渲染和逻辑
"""

import streamlit as st


class SidebarManager:
    """侧边栏管理器"""
    
    def __init__(self):
        """初始化侧边栏管理器"""
        pass
    
    def render(self):
        """渲染完整的侧边栏"""
        # 横向标签页布局 (v2.7.5: 新增角色页, 优化顺序)
        tab_main, tab_roles, tab_config, tab_monitor, tab_tools, tab_help = st.tabs([
            "🏠 主页", "🎭 角色", "⚙️ 配置", "📊 监控", "🔧 工具", "❓ 帮助"
        ])
        
        with tab_main:
            self.render_main_tab()
            
        with tab_roles:
            self.render_roles_tab()
        
        with tab_config:
            self.render_config_tab()
        
        with tab_monitor:
            self.render_monitor_tab()
            
        with tab_tools:
            self.render_tools_tab()
        
        with tab_help:
            self.render_help_tab()

    def render_roles_tab(self):
        """渲染角色管理标签"""
        from src.ui.role_manager_ui import RoleManagerUI
        RoleManagerUI.render()
    
    def render_tools_tab(self):
        """渲染工具标签"""
        from src.ui.tools_ui import ToolsUI
        ToolsUI.render()
    
    def render_main_tab(self):
        """渲染主页标签"""
        # 一键配置按钮
        col1, col2 = st.columns([9, 1])
        with col1:
            if st.button("⚡ 一键配置", type="primary", use_container_width=True):
                self.quick_setup()
        with col2:
            st.markdown("❓", help="自动配置默认设置")
        
        st.markdown("---")
        
        # 知识库控制台
        from src.kb.kb_interface import KBInterface
        kb_interface = KBInterface()
        kb_interface.render_kb_console()
    
    def render_config_tab(self):
        """渲染配置标签"""
        from src.config.config_interface import ConfigInterface
        
        config_interface = ConfigInterface()
        config_values = config_interface.render_config_tab()
        
        # 配置测试
        st.markdown("---")
        config_interface.test_config(config_values)
        
        # 快速设置
        st.markdown("---")
        config_interface.render_quick_setup()
        
        # 保存配置
        if st.button("💾 保存配置", type="primary", use_container_width=True):
            config_interface.save_config(config_values)
    
    def render_monitor_tab(self):
        """渲染监控标签"""
        from src.monitor.system_monitor_ui import SystemMonitorUI
        from src.utils.local_refresh_monitor import show_local_monitor
        
        monitor_ui = SystemMonitorUI()
        
        # 选择监控类型
        monitor_type = st.selectbox(
            "监控类型", 
            ["实时监控", "局部刷新监控", "基础监控", "性能仪表板", "v2.3监控"], 
            index=0,  # 默认选择第一个：实时监控
            key="monitor_type_select"
        )
        
        if monitor_type == "实时监控":
            # 使用实时监控，自动刷新不影响对话
            from src.utils.realtime_monitor import render_realtime_monitoring
            render_realtime_monitoring()
        elif monitor_type == "局部刷新监控":
            # 使用局部刷新监控，不影响对话区域
            show_local_monitor()
        elif monitor_type == "基础监控":
            monitor_ui.render_monitor_panel()
        elif monitor_type == "性能仪表板":
            monitor_ui.render_performance_dashboard()
        elif monitor_type == "v2.3监控":
            monitor_ui.render_v23_monitoring()
        
        # 额外监控功能
        st.markdown("---")
        
        with st.expander("📈 资源趋势", expanded=False):
            monitor_ui.render_resource_usage()
        
        with st.expander("🚨 系统告警", expanded=False):
            monitor_ui.render_alert_system()
        
        with st.expander("🔍 进程监控", expanded=False):
            monitor_ui.render_process_monitor()
    
    def render_help_tab(self):
        """渲染帮助标签"""
        st.markdown("#### 📖 帮助")
        st.info("RAG Pro Max v2.3.1 - 安全增强版")
        
        st.markdown("##### 🚀 快速开始")
        st.markdown("""
        1. 点击"⚡ 一键配置"自动设置
        2. 创建知识库并上传文档
        3. 开始智能问答
        """)
    
    def quick_setup(self):
        """一键配置"""
        from src.config import ConfigLoader
        ConfigLoader.quick_setup()
        st.success("✅ 已使用默认配置！")
        st.info("💡 下一步：创建知识库 → 上传文档 → 开始对话")
