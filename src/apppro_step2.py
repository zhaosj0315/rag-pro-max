#!/usr/bin/env python3
"""
RAG Pro Max - 逐步重构版本 Step 2
添加主界面功能模块
"""

# 环境初始化
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 核心模块导入
from src.core.environment import initialize_environment
from src.core.app_config import load_config
from src.ui.page_style import PageStyle
from src.core.main_controller import MainController

# 初始化环境
initialize_environment()

# 基础库导入
import streamlit as st
from datetime import datetime

# 业务模块导入
from src.app_logging import LogManager
from src.utils.memory import cleanup_memory
from src.kb.kb_manager import KBManager
from src.chat.chat_engine import ChatEngine
from src.processors.enhanced_upload_handler import EnhancedUploadHandler
from src.ui.compact_sidebar import render_compact_sidebar
from src.ui.main_interface import MainInterface

# 初始化组件
logger = LogManager()
kb_manager = KBManager()
chat_engine = ChatEngine()
upload_handler = EnhancedUploadHandler()
main_controller = MainController()
main_interface = MainInterface()

# 页面配置
PageStyle.setup_page()

# 紧凑侧边栏CSS样式
st.markdown("""
<style>
/* 侧边栏紧凑化 */
.css-1d391kg {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}

/* 减少标题间距 */
.css-1lcbmhc {
    margin-bottom: 0.25rem;
    margin-top: 0.25rem;
}

/* 紧凑按钮 */
.stButton > button {
    height: 1.8rem;
    padding: 0.2rem 0.4rem;
    font-size: 11px;
    margin-bottom: 0.2rem;
}

/* 紧凑输入框 */
.stTextInput > div > div > input {
    height: 1.8rem;
    font-size: 12px;
}

/* 紧凑选择框 */
.stSelectbox > div > div > div {
    height: 1.8rem;
    font-size: 12px;
}

/* 减少expander间距 */
.streamlit-expanderHeader {
    padding: 0.25rem 0.5rem;
    font-size: 13px;
}

/* 紧凑指标 */
.css-1xarl3l {
    padding: 0.25rem;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ RAG Pro Max")

# 渲染紧凑侧边栏
render_compact_sidebar()

# 主界面内容
if st.session_state.get('active_kb_name'):
    # 有知识库时显示聊天界面
    main_interface.render_chat_interface()
else:
    # 无知识库时显示欢迎界面
    main_interface.render_welcome_interface()

# 处理文件上传
if st.session_state.get('should_process_files'):
    main_controller.process_uploaded_files()

# 显示系统状态
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    kb_count = len(main_controller.get_knowledge_bases())
    st.metric("知识库", kb_count)
with col2:
    if st.session_state.get('active_kb_name'):
        doc_count = main_controller.get_document_count(st.session_state.active_kb_name)
        st.metric("文档数", doc_count)
    else:
        st.metric("文档数", 0)
with col3:
    msg_count = len(st.session_state.get('messages', []))
    st.metric("对话数", msg_count)
with col4:
    st.metric("版本", "v1.8.2")

# 重构进度
with st.expander("🔄 重构进度"):
    st.markdown("### Step 2: 主界面功能已模块化")
    st.markdown("- ✅ 导入部分已模块化")
    st.markdown("- ✅ 主界面功能已模块化")
    st.markdown("- ✅ 控制器逻辑已分离")
    st.markdown("- ⏳ 文件处理功能待迁移")
    st.markdown("- ⏳ 对话功能待迁移")
