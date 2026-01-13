"""
移动端适配器 (Mobile Adapter)
负责模拟移动设备和平板设备的视图布局，通过 CSS 注入实现响应式预览。
不影响核心业务逻辑，仅改变容器样式。
"""

import streamlit as st

class MobileAdapter:
    """移动端视图适配器"""

    MODES = {
        "desktop": {"icon": "🖥️", "label": "桌面版", "width": "100%"},
        "tablet": {"icon": "📟", "label": "平板版", "width": "768px"},
        "mobile": {"icon": "📱", "label": "手机版", "width": "390px"}
    }

    @staticmethod
    def init_state():
        """初始化视图状态"""
        if "view_mode" not in st.session_state:
            st.session_state.view_mode = "desktop"

    @staticmethod
    def render_view_selector():
        """渲染视图切换器 (已简化：仅保留桌面模式)"""
        MobileAdapter.init_state()
        
        # 强制锁定为桌面模式
        if st.session_state.view_mode != "desktop":
            st.session_state.view_mode = "desktop"
            st.rerun()

        # 不再显示切换按钮，直接应用桌面样式
        MobileAdapter._apply_css("desktop")

    @staticmethod
    def _apply_css(mode):
        """注入对应模式的 CSS"""
        if mode == "desktop":
            # 桌面模式: 恢复默认宽度
            css_content = """
            .main .block-container {
                max-width: 100% !important;
                width: 100% !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
                margin: 0 auto !important;
                border: none !important;
                box-shadow: none !important;
            }
            html { font-size: 16px !important; }
            
            /* 桌面模式恢复侧边栏拖拽功能 */
            .sidebar-resizer {
                display: block !important;
            }
            """
        else:
            target_width = MobileAdapter.MODES[mode]["width"]
            
            # 基础 CSS: 容器限制
            css_content = f"""
            /* 1. 强制修改主容器宽度并居中 */
            .main .block-container {{
                max-width: {target_width} !important;
                width: {target_width} !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
                margin: 0 auto !important; /* 居中 */
                
                /* 模拟设备边框和阴影 */
                border-left: 2px solid #007acc;
                border-right: 2px solid #007acc;
                box-shadow: 0 0 20px rgba(0,122,204,0.3);
                background-color: white;
                min-height: 100vh;
                position: relative;
            }}

            /* 设备标识 */
            .main .block-container::before {{
                content: "{MobileAdapter.MODES[mode]['icon']} {MobileAdapter.MODES[mode]['label']} ({target_width})";
                position: fixed;
                top: 10px;
                right: 20px;
                background: #007acc;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 9999;
            }}

            /* 深色模式适配 */
            @media (prefers-color-scheme: dark) {{
                .main .block-container {{
                    background-color: #0e1117; 
                    border-color: #007acc;
                    box-shadow: 0 0 20px rgba(0,122,204,0.5);
                }}
            }}

            /* 2. 保留侧边栏拖拽功能 (所有模式都可拖拽) */
            .sidebar-resizer {{
                display: block !important;
                opacity: 0.7 !important;
            }}
            
            .sidebar-resizer:hover {{
                opacity: 1 !important;
                background-color: #007acc !important;
            }}
            
            /* 3. 全局字体与控件调整 */
            html {{ font-size: 14px !important; }}
            .stButton button {{ padding: 0.3rem 0.6rem !important; }}
            .stTextInput input {{ font-size: 14px !important; }}
            .stSelectbox {{ width: 100% !important; }}
            
            /* 确保搜索和输入控件正常显示 */
            .stTextInput, .stSelectbox, .stButton {{
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
            }}
            """

            # 针对手机模式的特殊处理：强制单列堆叠
            if mode == "mobile":
                css_content += """
                /* 4. 强制列堆叠 (Fix: 只能看到左边的问题) */
                [data-testid="column"] {
                    width: 100% !important;
                    flex: 1 1 auto !important;
                    min-width: 100% !important;
                    display: block !important;
                    margin-bottom: 1rem !important;
                }
                
                /* 5. 侧边栏在手机模式下默认较窄，但仍可拖拽 */
                section[data-testid="stSidebar"] {
                    width: 280px !important; 
                    min-width: 200px !important;
                    max-width: 400px !important;
                }
                
                /* 增强手机模式下的拖拽手柄可见性 */
                .sidebar-resizer {
                    width: 6px !important;
                    background-color: #007acc !important;
                    opacity: 0.8 !important;
                }
                
                .sidebar-resizer:hover {
                    width: 8px !important;
                    background-color: #005a9e !important;
                    opacity: 1 !important;
                }
                
                /* 6. 图片和图表自适应 */
                img, canvas, iframe, .stPlotlyChart {
                    max-width: 100% !important;
                    height: auto !important;
                }
                
                /* 7. 手机模式字体更小 */
                html { font-size: 12px !important; }
                
                /* 8. 按钮和输入框更紧凑，但保持功能 */
                .stButton button { 
                    padding: 0.2rem 0.4rem !important; 
                    font-size: 12px !important;
                }
                
                .stTextInput input, .stSelectbox select {
                    font-size: 12px !important;
                    padding: 0.3rem !important;
                }
                
                /* 确保搜索框在手机模式下可见可用 */
                .stTextInput, .stSelectbox, .stButton {
                    width: 100% !important;
                    display: block !important;
                    margin-bottom: 0.5rem !important;
                }
                """
            
            # 针对平板模式的特殊处理
            if mode == "tablet":
                 css_content += """
                /* 平板模式下侧边栏可调节 */
                section[data-testid="stSidebar"] {
                    width: 320px !important; 
                    min-width: 250px !important;
                    max-width: 450px !important;
                }
                
                /* 增强平板模式下的拖拽手柄 */
                .sidebar-resizer {
                    width: 5px !important;
                    background-color: #007acc !important;
                    opacity: 0.6 !important;
                }
                
                .sidebar-resizer:hover {
                    width: 7px !important;
                    opacity: 1 !important;
                }
                
                /* 平板模式字体适中 */
                html { font-size: 15px !important; }
                
                /* 确保平板模式下搜索控件正常 */
                .stTextInput, .stSelectbox, .stButton {
                    display: block !important;
                    width: 100% !important;
                }
                """

        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
