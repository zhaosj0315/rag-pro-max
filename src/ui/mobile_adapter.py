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
        """渲染视图切换器 (建议放在侧边栏)"""
        MobileAdapter.init_state()
        
        st.markdown("### 📱 视图预览", help="切换不同设备的视图布局，不影响功能，仅改变显示宽度。")
        
        # 使用列布局放置三个小按钮
        cols = st.columns(3)
        
        # 定义按钮点击回调
        def set_mode(mode):
            st.session_state.view_mode = mode

        # 渲染按钮
        current_mode = st.session_state.view_mode
        
        with cols[0]:
            # 桌面按钮
            if st.button("🖥️", key="btn_view_desktop", help="桌面全宽视图", 
                         type="primary" if current_mode == "desktop" else "secondary",
                         use_container_width=True):
                set_mode("desktop")
                st.rerun()
                
        with cols[1]:
            # 平板按钮
            if st.button("📟", key="btn_view_tablet", help="平板 (iPad) 视图", 
                         type="primary" if current_mode == "tablet" else "secondary",
                         use_container_width=True):
                set_mode("tablet")
                st.rerun()
                
        with cols[2]:
            # 手机按钮
            if st.button("📱", key="btn_view_mobile", help="手机视图", 
                         type="primary" if current_mode == "mobile" else "secondary",
                         use_container_width=True):
                set_mode("mobile")
                st.rerun()

        # 立即应用对应的 CSS
        MobileAdapter._apply_css(current_mode)

    @staticmethod
    def _apply_css(mode):
        """注入对应模式的 CSS"""
        if mode == "desktop":
            return # 桌面模式无需额外 CSS，使用默认流式布局

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
            border-left: 1px solid #e0e0e0;
            border-right: 1px solid #e0e0e0;
            box-shadow: 0 0 40px rgba(0,0,0,0.1);
            background-color: white;
            min-height: 100vh;
        }}

        /* 深色模式适配 */
        @media (prefers-color-scheme: dark) {{
            .main .block-container {{
                background-color: #0e1117; 
                border-color: #333;
                box-shadow: 0 0 40px rgba(0,0,0,0.5);
            }}
        }}

        /* 2. 隐藏侧边栏拖拽手柄 (移动预览模式禁用拖拽) */
        .sidebar-resizer {{
            display: none !important;
        }}
        
        /* 3. 全局字体与控件调整 */
        html {{ font-size: 14px !important; }}
        .stButton button {{ padding: 0.3rem 0.6rem !important; width: 100% !important; }}
        .stTextInput input {{ font-size: 14px !important; }}
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
            }
            
            /* 5. 侧边栏在手机模式下强制变窄，避免遮挡 */
            section[data-testid="stSidebar"] {
                width: 320px !important; 
                min-width: 320px !important;
                max-width: 320px !important;
            }
            
            /* 6. 图片和图表自适应 */
            img, canvas, iframe, .stPlotlyChart {
                max-width: 100% !important;
                height: auto !important;
            }
            """
        
        # 针对平板模式的特殊处理
        if mode == "tablet":
             css_content += """
            /* 平板模式下侧边栏稍微窄一点 */
            section[data-testid="stSidebar"] {
                width: 350px !important; 
                min-width: 300px !important;
            }
            """

        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
