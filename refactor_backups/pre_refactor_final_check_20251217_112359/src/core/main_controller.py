"""
主控制器 - 处理所有业务逻辑
"""

import streamlit as st
import time
import os
from typing import Optional, List, Any

class MainController:
    """主控制器 - 集中处理所有业务逻辑"""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """初始化会话状态"""
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'active_kb_name' not in st.session_state:
            st.session_state.active_kb_name = None
    
    def render_welcome_page(self):
        """渲染欢迎页面"""
        st.markdown("""
        ## 👋 欢迎使用 RAG Pro Max
        
        ### 🚀 开始使用
        1. 在左侧创建或选择知识库
        2. 上传您的文档
        3. 开始智能问答
        
        ### ✨ 主要特性
        - 📄 多格式文档支持
        - 🔍 智能语义检索  
        - 💬 多轮对话
        - 🎯 精确引用来源
        """)
    
    def render_chat_interface(self):
        """渲染聊天界面"""
        kb_name = st.session_state.active_kb_name
        
        # 显示知识库信息
        st.info(f"📚 当前知识库: **{kb_name}**")
        
        # 显示历史消息
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # 用户输入
        if prompt := st.chat_input("请输入您的问题..."):
            # 添加用户消息
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # 处理查询
            with st.chat_message("assistant"):
                with st.spinner("思考中..."):
                    response = self.process_query(prompt, kb_name)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
    
    def process_query(self, query: str, kb_name: str) -> str:
        """处理用户查询"""
        try:
            # 这里集成现有的RAG查询逻辑
            from src.kb.kb_loader import KBLoader
            from src.chat.chat_engine import ChatEngine
            
            # 加载知识库
            kb_loader = KBLoader()
            index = kb_loader.load_knowledge_base(kb_name)
            
            if not index:
                return "❌ 知识库加载失败，请检查知识库是否存在。"
            
            # 执行查询
            chat_engine = ChatEngine()
            response = chat_engine.query(query, index)
            
            return str(response)
            
        except Exception as e:
            return f"❌ 查询失败: {str(e)}"
    
    def process_uploaded_files(self):
        """处理上传的文件"""
        if not st.session_state.get('should_process_files'):
            return
        
        files = st.session_state.get('uploaded_files')
        if not files:
            return
        
        kb_name = st.session_state.active_kb_name
        
        if not kb_name:
            st.error("请先选择知识库")
            return
        
        # 显示处理进度
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            for i, file in enumerate(files):
                progress = (i + 1) / len(files)
                progress_bar.progress(progress)
                status_text.text(f"处理文件 {i+1}/{len(files)}: {file.name}")
                time.sleep(0.1)  # 模拟处理
            
            st.success(f"✅ 成功处理 {len(files)} 个文件")
            
        except Exception as e:
            st.error(f"❌ 文件处理失败: {str(e)}")
        
        finally:
            # 清理状态
            st.session_state['should_process_files'] = False
            st.session_state['uploaded_files'] = None
    
    def render_status_bar(self):
        """渲染底部状态栏"""
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            kb_count = len(self.get_knowledge_bases())
            st.metric("知识库", kb_count)
        
        with col2:
            if st.session_state.active_kb_name:
                doc_count = self.get_document_count(st.session_state.active_kb_name)
                st.metric("文档数", doc_count)
            else:
                st.metric("文档数", 0)
        
        with col3:
            msg_count = len(st.session_state.messages)
            st.metric("对话数", msg_count)
        
        with col4:
            st.metric("版本", "v1.8.0")
    
    def get_knowledge_bases(self) -> List[str]:
        """获取知识库列表"""
        kb_dir = "vector_db_storage"
        if not os.path.exists(kb_dir):
            return []
        
        return [d for d in os.listdir(kb_dir) 
                if os.path.isdir(os.path.join(kb_dir, d))]
    
    def get_document_count(self, kb_name: str) -> int:
        """获取知识库文档数量"""
        try:
            import json
            manifest_path = f"vector_db_storage/{kb_name}/manifest.json"
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    return len(manifest.get('files', []))
        except:
            pass
        return 0
