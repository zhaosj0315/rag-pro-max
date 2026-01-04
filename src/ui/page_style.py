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
        
        /* 舒适的侧边栏 */
        section[data-testid="stSidebar"] {
            width: 850px !important;
            min-width: 850px !important;
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
    def setup_page():
        """设置完整页面"""
        PageStyle.setup_page_config()
        PageStyle.apply_custom_css()
