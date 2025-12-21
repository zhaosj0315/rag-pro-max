"""
主应用入口 - 整合各个模块
"""

import os
import time
import streamlit as st
from src.app.app_initializer import AppInitializer
from src.ui.sidebar_manager import SidebarManager
from src.chat.chat_interface import ChatInterface
from src.kb.kb_interface import KBInterface


class MainApp:
    """主应用类"""
    
    def __init__(self):
        """初始化应用"""
        AppInitializer.initialize_app()
        
        # 初始化会话状态
        from src.utils.app_utils import initialize_session_state
        initialize_session_state()
        
        # 初始化各个管理器
        self.sidebar_manager = SidebarManager()
        self.chat_interface = ChatInterface()
        self.kb_interface = KBInterface()
    
    def run(self):
        """运行应用"""
        # 渲染侧边栏
        with st.sidebar:
            self.sidebar_manager.render()
        
        # 获取当前选择的知识库
        active_kb = st.session_state.get('current_kb_name')
        
        # 自动加载知识库逻辑
        if active_kb and active_kb != st.session_state.get('current_kb_id'):
            # 只在没有正在处理的问题时才切换
            if not st.session_state.get('is_processing', False):
                st.session_state.current_kb_id = active_kb
                st.session_state.chat_engine = None
                
                # 加载对话历史
                with st.spinner("📜 正在加载对话历史..."):
                    from src.chat import HistoryManager
                    st.session_state.messages = HistoryManager.load(active_kb)
                
                st.session_state.suggestions_history = []
            else:
                st.warning("⚠️ 正在处理问题，请等待完成后再切换知识库")
                # 恢复到之前的知识库
                st.session_state.current_nav = f"📂 {st.session_state.current_kb_id}"
        
        if active_kb:
            # 有知识库时显示聊天界面
            self.chat_interface.render(active_kb)
            
            # 渲染文档详情对话框
            self.chat_interface.render_document_detail_dialog()
        else:
            # 无知识库时显示欢迎界面
            self.render_welcome()
        
        # 处理首次使用引导
        self.handle_first_time_guide()
    
    def render_welcome(self):
        """渲染欢迎界面"""
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: rgba(255,75,75,0.02); border-radius: 10px; margin: 1rem 0;">
            <h2>👋 欢迎使用 RAG Pro Max</h2>
            <p><b>快速开始指南：</b></p>
            <p>1️⃣ 点击左侧"⚡ 一键配置"</p>
            <p>2️⃣ 创建知识库并上传文档</p>
            <p>3️⃣ 开始智能问答</p>
        </div>
        """, unsafe_allow_html=True)
    
    def handle_first_time_guide(self):
        """处理首次使用引导"""
        # 获取现有知识库
        from src.kb import KBManager
        kb_manager = KBManager()
        output_base = os.path.join(os.getcwd(), "vector_db_storage")
        kb_manager.base_path = output_base
        existing_kbs = kb_manager.list_all()
        
        # 首次使用引导
        if not st.session_state.get('first_time_guide_shown', False) and len(existing_kbs) == 0:
            st.info("""
            ### 👋 欢迎使用 RAG Pro Max！
            
            **快速开始指南：**
            
            1️⃣ **配置 LLM**（左侧边栏）
            - 选择 Ollama（本地）或 OpenAI（云端）
            - 输入 API 信息
            
            2️⃣ **创建知识库**
            - 点击 "➕ 新建知识库..."
            - 输入名称，上传文档
            
            3️⃣ **开始对话**
            - 选择知识库
            - 在下方输入问题
            
            💡 **提示**：支持 PDF、DOCX、TXT、MD 等多种格式
            """)
            
            if st.button("✅ 我知道了，开始使用", use_container_width=True):
                st.session_state.first_time_guide_shown = True
                st.rerun()
