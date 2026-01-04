"""
页面样式模块
负责页面配置、CSS样式和布局设置
"""

import streamlit as st


class PageStyle:
    """页面样式管理器"""
    
    @staticmethod
    def setup_page_config():
        """设置页面配置"""
        st.set_page_config(
            page_title="RAG Pro Max",
            page_icon="🛡️",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/yourusername/rag-pro-max',
                'Report a bug': 'https://github.com/yourusername/rag-pro-max/issues',
                'About': "# RAG Pro Max\n基于 Streamlit 的 RAG 应用"
            }
        )
    
    @staticmethod
    def apply_custom_css():
        """应用自定义 CSS 样式"""
        st.markdown(PageStyle._get_custom_css(), unsafe_allow_html=True)
    
    @staticmethod
    def _get_custom_css():
        """获取自定义 CSS"""
        return """
        <style>
        /* 舒适的全局样式 */
        .main .block-container {
            padding-top: 0.75rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }
        
        /* 舒适的侧边栏 - 允许JS动态调整 */
        section[data-testid="stSidebar"] {
            width: 850px;
            min-width: 250px;
            transition: width 0.1s; /* 添加一点平滑过渡 */
        }
        
        section[data-testid="stSidebar"] > div {
            padding-top: 0.75rem !important;
        }
        
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            gap: 1px !important;
        }
        
        /* 舒适的元素间距 */
        .element-container {
            margin-bottom: 0.75rem !important;
        }
        
        /* 标题间距 */
        h1, h2, h3, h4, h5, h6 {
            margin-top: 0.5rem !important;
            margin-bottom: 0.75rem !important;
            line-height: 1.3 !important;
        }
        
        /* 舒适的按钮 */
        .stButton > button {
            padding: 0.5rem 1rem !important;
            font-size: 0.9rem !important;
            line-height: 1.4 !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* 舒适的输入框 */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > div,
        .stNumberInput > div > div > input {
            padding: 0.5rem 0.75rem !important;
            font-size: 0.9rem !important;
            line-height: 1.4 !important;
        }

        /* 修复 Selectbox 文字截断 */
        .stSelectbox > div > div > div {
            white-space: normal !important;
            height: auto !important;
            overflow: visible !important;
        }
        
        /* 舒适的标签页 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 1rem !important;
            margin-bottom: 1rem !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 1rem !important;
            font-size: 0.9rem !important;
            line-height: 1.4 !important;
        }
        
        /* 舒适的展开器 */
        .streamlit-expanderHeader {
            font-size: 0.95rem !important;
            padding: 0.75rem !important;
            line-height: 1.4 !important;
        }
        
        .streamlit-expanderContent {
            padding: 0.75rem 0 !important;
        }
        
        /* 舒适的复选框 */
        .stCheckbox > label,
        .stRadio > label {
            font-size: 0.9rem !important;
            line-height: 1.4 !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* 舒适的文本区域 */
        .stTextArea > div > div > textarea {
            padding: 0.75rem !important;
            font-size: 0.9rem !important;
            line-height: 1.5 !important;
        }
        
        /* 舒适的状态消息 */
        .stAlert, .stSuccess, .stError, .stWarning, .stInfo {
            padding: 0.75rem 1rem !important;
            font-size: 0.9rem !important;
            margin: 0.75rem 0 !important;
            line-height: 1.4 !important;
        }
        
        /* 舒适的聊天消息 */
        .stChatMessage {
            padding: 1rem !important;
            margin-bottom: 0.75rem !important;
        }
        
        /* 舒适的指标卡片 */
        [data-testid="stMetricValue"] {
            font-size: 1.2rem !important;
            line-height: 1.3 !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.85rem !important;
            margin-bottom: 0.25rem !important;
        }
        
        /* 列间距 */
        [data-testid="column"] {
            padding: 0 0.5rem !important;
        }
        
        /* 容器间距 */
        .stContainer {
            padding: 0.75rem !important;
        }
        
        /* 欢迎框 - 舒适版 */
        .welcome-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            margin: 1rem 0;
        }
        
        .welcome-box h2 {
            margin-bottom: 1rem;
            font-size: 1.6rem;
            line-height: 1.3;
        }
        
        .welcome-box p {
            font-size: 1rem;
            margin-bottom: 0;
            line-height: 1.5;
        }
        
        /* 隐藏不必要的元素 */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {
                width: 100% !important;
                min-width: 100% !important;
            }
            
            .main .block-container {
                padding: 0.5rem !important;
            }
            
            .stButton > button {
                width: 100% !important;
                padding: 0.75rem !important;
                font-size: 1rem !important;
            }
            
            .welcome-box {
                padding: 1.5rem 1rem !important;
                margin: 0.5rem 0 !important;
            }
            
            .welcome-box h2 {
                font-size: 1.3rem !important;
            }
            
            .welcome-box p {
                font-size: 0.95rem !important;
            }
        }
        
        @media (min-width: 768px) and (max-width: 1024px) {
            section[data-testid="stSidebar"] {
                width: 400px !important;
                min-width: 400px !important;
            }
        }
        </style>
        """
    
    @staticmethod
    def render_welcome_message():
        """渲染欢迎消息"""
        st.markdown("""
        <div class="welcome-box">
            <h2>👋 欢迎使用知识库</h2>
            <p>请在左侧 <b>侧边栏</b> 配置数据源 (支持粘贴路径或拖拽文件)，点击 <b>🚀 立即创建</b> 开始。</p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def inject_resizable_sidebar():
        """注入可拖拽侧边栏的 JS/CSS (修复版)"""
        js = """
        <script>
        (function() {
            try {
                // 获取父级文档（突破 iframe 限制）
                const doc = window.parent.document;
                
                // 避免重复注入
                if (doc.window && doc.window.hasInjectedResizeHandler) return;
                if (doc.window) doc.window.hasInjectedResizeHandler = true;

                function initResizeHandler() {
                    const sidebar = doc.querySelector('section[data-testid="stSidebar"]');
                    if (!sidebar) {
                        setTimeout(initResizeHandler, 300);
                        return;
                    }

                    // 如果已经有手柄了，先移除（防止热重载导致重复）
                    const oldResizer = sidebar.querySelector('.sidebar-resizer');
                    if (oldResizer) oldResizer.remove();

                    // 创建拖拽手柄
                    const resizer = doc.createElement('div');
                    resizer.className = 'sidebar-resizer';
                    resizer.style.width = '10px'; // 加宽一点更容易抓取
                    resizer.style.background = 'transparent';
                    resizer.style.position = 'absolute';
                    resizer.style.top = '0';
                    resizer.style.bottom = '0';
                    resizer.style.right = '-5px'; // 向右偏移，覆盖边缘
                    resizer.style.cursor = 'col-resize';
                    resizer.style.zIndex = '999999';
                    resizer.setAttribute('title', '↔ 拖动调整侧边栏宽度');
                    
                    // 鼠标悬停变色提示 (蓝色光晕)
                    resizer.onmouseover = () => { 
                        resizer.style.background = 'rgba(64, 156, 255, 0.3)'; 
                        resizer.style.boxShadow = '0 0 10px rgba(64, 156, 255, 0.5)';
                    };
                    resizer.onmouseout = () => { 
                        resizer.style.background = 'transparent'; 
                        resizer.style.boxShadow = 'none';
                    };

                    sidebar.appendChild(resizer);
                    // 确保侧边栏定位是 relative 或 absolute，以便手柄定位
                    if (window.getComputedStyle(sidebar).position === 'static') {
                        sidebar.style.position = 'relative';
                    }

                    let isResizing = false;

                    resizer.addEventListener('mousedown', (e) => {
                        isResizing = true;
                        doc.body.style.cursor = 'col-resize';
                        e.preventDefault();
                    });

                    doc.addEventListener('mousemove', (e) => {
                        if (!isResizing) return;
                        
                        const newWidth = e.clientX;
                        // 限制宽度范围 (200px ~ 80% 屏幕宽度)
                        if (newWidth > 200 && newWidth < window.innerWidth * 0.8) {
                            // 使用 setProperty(..., 'important') 强制覆盖 CSS
                            sidebar.style.setProperty('width', newWidth + 'px', 'important');
                            sidebar.style.setProperty('min-width', newWidth + 'px', 'important');
                            sidebar.style.setProperty('max-width', newWidth + 'px', 'important');
                        }
                    });

                    doc.addEventListener('mouseup', () => {
                        if (isResizing) {
                            isResizing = false;
                            doc.body.style.cursor = 'default';
                        }
                    });
                }

                // 启动初始化
                if (doc.readyState === 'loading') {
                    doc.addEventListener('DOMContentLoaded', initResizeHandler);
                } else {
                    initResizeHandler();
                }
            } catch (e) {
                console.error("Sidebar Resizer Injection Failed:", e);
            }
        })();
        </script>
        """
        st.components.v1.html(js, height=0, width=0)

    @staticmethod
    def setup_page():
        """设置完整页面"""
        PageStyle.setup_page_config()
        PageStyle.apply_custom_css()
        PageStyle.inject_resizable_sidebar()
