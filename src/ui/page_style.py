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
        /* 全局样式优化 */
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 100%;
        }
        
        /* 侧边栏样式 */
        section[data-testid="stSidebar"] {
            width: 350px !important;
            min-width: 350px !important;
        }
        
        section[data-testid="stSidebar"] > div {
            padding-top: 1rem !important;
            margin-top: 0rem !important;
        }
        
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
            padding-top: 0rem !important;
            margin-top: 0rem !important;
            gap: 0.5rem !important;
        }
        
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:first-child {
            padding-top: 0rem !important;
            margin-top: 0rem !important;
        }
        
        /* 最小化顶部空白 */
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 0.5rem !important;
        }
        
        /* 紧凑标题 */
        h3, h4 {
            margin-top: 0 !important;
            margin-bottom: 0.5rem !important;
            padding-top: 0 !important;
            line-height: 1.2 !important;
        }
        
        /* 超紧凑指标卡片 */
        [data-testid="stMetricValue"] {
            font-size: 1.1rem !important;
        }
        
        [data-testid="stMetricLabel"] {
            font-size: 0.8rem !important;
        }
        
        [data-testid="stMetricDelta"] {
            font-size: 0.7rem !important;
        }
        
        /* 紧凑按钮 */
        .stButton > button {
            padding: 0.25rem 0.5rem !important;
            font-size: 0.85rem !important;
            line-height: 1.2 !important;
        }
        
        /* 紧凑输入框 */
        .stTextInput > div > div > input {
            padding: 0.25rem 0.5rem !important;
            font-size: 0.85rem !important;
        }
        
        /* 紧凑选择框 */
        .stSelectbox > div > div > div {
            padding: 0.25rem 0.5rem !important;
            font-size: 0.85rem !important;
        }
        
        /* 紧凑复选框 */
        .stCheckbox > label {
            font-size: 0.85rem !important;
            line-height: 1.2 !important;
        }
        
        /* 紧凑滑块 */
        .stSlider > div > div > div {
            font-size: 0.8rem !important;
        }
        
        /* 紧凑数字输入 */
        .stNumberInput > div > div > input {
            padding: 0.25rem 0.5rem !important;
            font-size: 0.85rem !important;
        }
        
        /* 紧凑文本区域 */
        .stTextArea > div > div > textarea {
            padding: 0.25rem 0.5rem !important;
            font-size: 0.85rem !important;
        }
        
        /* 紧凑标签页 */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem !important;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0.25rem 0.75rem !important;
            font-size: 0.85rem !important;
        }
        
        /* 紧凑展开器 */
        .streamlit-expanderHeader {
            font-size: 0.9rem !important;
            padding: 0.25rem 0.5rem !important;
        }
        
        /* 紧凑状态显示 */
        .stStatus > div {
            padding: 0.5rem !important;
        }
        
        /* 紧凑进度条 */
        .stProgress > div > div {
            height: 0.5rem !important;
        }
        
        /* 紧凑警告/信息框 */
        .stAlert {
            padding: 0.5rem !important;
            font-size: 0.85rem !important;
        }
        
        /* 紧凑成功/错误消息 */
        .stSuccess, .stError, .stWarning, .stInfo {
            padding: 0.5rem !important;
            font-size: 0.85rem !important;
        }
        
        /* 聊天消息样式 */
        .stChatMessage {
            padding: 0.5rem !important;
        }
        
        /* 欢迎框样式 */
        .welcome-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
            margin: 1rem 0;
        }
        
        .welcome-box h2 {
            margin-bottom: 1rem;
            font-size: 1.8rem;
        }
        
        .welcome-box p {
            font-size: 1.1rem;
            margin-bottom: 0;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            section[data-testid="stSidebar"] {
                width: 300px !important;
                min-width: 300px !important;
            }
            
            .main .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
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
