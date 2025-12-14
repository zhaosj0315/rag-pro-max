"""
移动端响应式设计组件
解决移动端不可用问题
"""

import streamlit as st

def inject_mobile_css():
    """注入移动端CSS样式"""
    mobile_css = """
    <style>
    /* 移动端适配 */
    @media (max-width: 768px) {
        /* 主容器适配 */
        .main .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }
        
        /* 侧边栏适配 */
        .css-1d391kg {
            width: 100% !important;
        }
        
        /* 按钮适配 */
        .stButton > button {
            width: 100% !important;
            margin-bottom: 0.5rem !important;
            font-size: 14px !important;
            padding: 0.5rem !important;
        }
        
        /* 输入框适配 */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea {
            font-size: 16px !important; /* 防止iOS缩放 */
        }
        
        /* 选择框适配 */
        .stSelectbox > div > div {
            font-size: 14px !important;
        }
        
        /* 文件上传适配 */
        .stFileUploader {
            font-size: 14px !important;
        }
        
        /* 表格适配 */
        .dataframe {
            font-size: 12px !important;
            overflow-x: auto !important;
        }
        
        /* 聊天消息适配 */
        .stChatMessage {
            margin-bottom: 1rem !important;
        }
        
        /* 状态指示器适配 */
        .stStatus {
            font-size: 14px !important;
        }
        
        /* 隐藏不必要的元素 */
        .stDeployButton {
            display: none !important;
        }
    }
    
    /* 平板适配 */
    @media (min-width: 769px) and (max-width: 1024px) {
        .main .block-container {
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }
        
        .stButton > button {
            font-size: 15px !important;
        }
    }
    
    /* 触摸优化 */
    @media (hover: none) and (pointer: coarse) {
        .stButton > button {
            min-height: 44px !important; /* 触摸目标最小尺寸 */
        }
        
        .stSelectbox > div > div {
            min-height: 44px !important;
        }
    }
    </style>
    """
    st.markdown(mobile_css, unsafe_allow_html=True)

def detect_mobile():
    """检测是否为移动设备"""
    # 通过JavaScript检测屏幕宽度
    mobile_detect_js = """
    <script>
    function detectMobile() {
        return window.innerWidth <= 768;
    }
    
    if (detectMobile()) {
        document.body.classList.add('mobile-device');
    }
    </script>
    """
    st.markdown(mobile_detect_js, unsafe_allow_html=True)

def mobile_sidebar_layout():
    """移动端侧边栏布局优化"""
    if st.sidebar.button("📱 移动端模式", help="优化移动端显示"):
        st.session_state.mobile_mode = True
        st.rerun()
    
    if st.session_state.get('mobile_mode', False):
        st.sidebar.success("📱 移动端模式已启用")
        if st.sidebar.button("💻 桌面端模式"):
            st.session_state.mobile_mode = False
            st.rerun()

def mobile_chat_interface():
    """移动端聊天界面优化"""
    if st.session_state.get('mobile_mode', False):
        # 移动端专用聊天输入
        st.markdown("### 💬 智能问答")
        
        # 简化的输入界面
        user_input = st.text_area(
            "输入问题...", 
            height=100,
            placeholder="在这里输入你的问题...",
            key="mobile_chat_input"
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            send_button = st.button("📤 发送", use_container_width=True)
        with col2:
            clear_button = st.button("🧹 清空", use_container_width=True)
        
        return user_input, send_button, clear_button
    
    return None, None, None

def mobile_file_upload():
    """移动端文件上传优化"""
    if st.session_state.get('mobile_mode', False):
        st.markdown("### 📁 文件上传")
        
        # 简化的上传界面
        uploaded_file = st.file_uploader(
            "选择文件",
            type=['pdf', 'txt', 'docx', 'md', 'xlsx', 'csv'],
            help="支持PDF、Word、Excel等格式"
        )
        
        if uploaded_file:
            st.success(f"✅ 已选择: {uploaded_file.name}")
            if st.button("🚀 开始处理", use_container_width=True):
                return uploaded_file
        
        return None
    
    return None

def mobile_knowledge_base_selector():
    """移动端知识库选择器"""
    if st.session_state.get('mobile_mode', False):
        st.markdown("### 📚 知识库")
        
        # 简化的知识库选择
        kb_options = ["新建知识库", "知识库1", "知识库2"]  # 实际应该从系统获取
        selected_kb = st.selectbox(
            "选择知识库",
            kb_options,
            key="mobile_kb_selector"
        )
        
        return selected_kb
    
    return None

def apply_mobile_optimizations():
    """应用所有移动端优化"""
    # 注入CSS
    inject_mobile_css()
    
    # 检测移动设备
    detect_mobile()
    
    # 移动端提示
    if st.session_state.get('mobile_mode', False):
        st.info("📱 移动端模式已启用 - 界面已优化适配手机使用")
    
    # 添加移动端切换按钮到侧边栏
    mobile_sidebar_layout()
