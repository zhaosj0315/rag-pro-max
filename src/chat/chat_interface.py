"""
聊天界面 - 负责聊天相关的所有UI逻辑
"""

import streamlit as st


class ChatInterface:
    """聊天界面管理器"""
    
    def __init__(self):
        """初始化聊天界面"""
        pass
    
    def render(self, kb_name: str):
        """渲染聊天界面"""
        st.title("🛡️ RAG Pro Max")
        
        # 显示知识库信息
        self.render_kb_info(kb_name)
        
        # 渲染聊天历史
        self.render_chat_history()
        
        # 渲染输入区域
        self.render_input_area()
        
        # 渲染推荐问题
        self.render_suggestions()
    
    def render_kb_info(self, kb_name: str):
        """渲染知识库信息"""
        # 获取知识库统计信息
        try:
            from src.documents.document_manager import DocumentManager
            import os
            
            default_output_path = os.path.join(os.getcwd(), "vector_db_storage")
            db_path = os.path.join(default_output_path, kb_name)
            
            if os.path.exists(db_path):
                doc_manager = DocumentManager(db_path)
                stats = doc_manager.get_kb_statistics()
                
                # 显示统计信息
                col1, col2, col3 = st.columns(3)
                col1.metric("📄 文档数", stats.get('file_cnt', 0))
                col2.metric("🧩 片段数", stats.get('total_chunks', 0))
                col3.metric("💾 大小", f"{stats.get('size', 0) / (1024 * 1024):.1f}MB")
                
                # 文档管理入口
                with st.expander("📊 知识库详情与管理", expanded=False):
                    from src.document.document_manager_ui import DocumentManagerUI
                    doc_ui = DocumentManagerUI()
                    doc_ui.render_document_list(kb_name)
                    
                    st.divider()
                    doc_ui.render_document_operations(kb_name)
                    
        except Exception as e:
            st.caption(f"无法加载知识库信息: {str(e)}")
    
    def render_document_detail_dialog(self):
        """渲染文档详情对话框"""
        if st.session_state.get('show_doc_detail') and st.session_state.get('show_doc_detail_kb'):
            from src.document.document_manager_ui import DocumentManagerUI
            DocumentManagerUI.show_document_detail_dialog(
                st.session_state.show_doc_detail_kb, 
                st.session_state.show_doc_detail
            )
    
    def render_chat_history(self):
        """渲染聊天历史"""
        # 初始化消息历史
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # 显示聊天历史
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # 显示推荐问题
                if message["role"] == "assistant" and message.get("suggestions"):
                    self.render_message_suggestions(message["suggestions"])
    
    def render_input_area(self):
        """渲染输入区域"""
        # 检查是否正在处理
        if st.session_state.get('is_processing'):
            # 正在处理时显示停止按钮
            col1, col2 = st.columns([4, 1])
            with col1:
                st.chat_input("正在生成回答中...", disabled=True)
            with col2:
                if st.button("⏹ 停止", key="stop_generation"):
                    st.session_state.stop_generation = True
                    st.session_state.is_processing = False
                    st.rerun()
        else:
            # 正常输入状态
            if prompt := st.chat_input("请输入您的问题..."):
                self.handle_user_input(prompt)
    
    def render_suggestions(self):
        """渲染推荐问题"""
        # 显示全局推荐问题
        if hasattr(st.session_state, 'global_suggestions') and st.session_state.global_suggestions:
            st.markdown("#### 💡 推荐问题")
            
            cols = st.columns(min(len(st.session_state.global_suggestions), 3))
            for i, suggestion in enumerate(st.session_state.global_suggestions[:3]):
                with cols[i]:
                    if st.button(suggestion, key=f"global_suggestion_{i}", use_container_width=True):
                        self.handle_user_input(suggestion)
    
    def render_message_suggestions(self, suggestions):
        """渲染消息相关的推荐问题"""
        if suggestions:
            st.markdown("**💡 相关问题:**")
            for i, suggestion in enumerate(suggestions[:3]):
                if st.button(suggestion, key=f"msg_suggestion_{i}_{len(st.session_state.messages)}", use_container_width=True):
                    self.handle_user_input(suggestion)
    
    def handle_user_input(self, prompt: str):
        """处理用户输入"""
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # 显示用户消息
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # 生成助手回复
        with st.chat_message("assistant"):
            self.generate_response(prompt)
    
    def generate_response(self, prompt: str):
        """生成助手回复"""
        # 设置处理状态
        st.session_state.is_processing = True
        
        try:
            # 检查是否有聊天引擎
            if not st.session_state.get('chat_engine'):
                # 尝试加载聊天引擎
                self.load_chat_engine()
                
                if not st.session_state.get('chat_engine'):
                    st.error("❌ 知识库未加载，请先选择知识库")
                    return
            
            # 生成回复
            response_placeholder = st.empty()
            
            # 实际调用聊天引擎
            try:
                # 检查chat_engine是否存在且有效
                if not hasattr(st.session_state, 'chat_engine'):
                    raise Exception("Chat engine not initialized in session state")
                
                if st.session_state.chat_engine is None:
                    raise Exception("Chat engine is None")
                
                chat_engine = st.session_state.chat_engine
                response = chat_engine.stream_chat(prompt)
                
                full_response = ""
                for token in response.response_gen:
                    # 检查停止信号
                    if st.session_state.get('stop_generation'):
                        st.session_state.stop_generation = False
                        full_response += "\n\n⏹ **生成已停止**"
                        break
                    
                    full_response += token
                    response_placeholder.markdown(full_response + "▌")
                
                # 完成生成
                response_placeholder.markdown(full_response)
                
                # 生成追问问题
                suggestions = self.generate_follow_up_questions(prompt, full_response)
                
                # 添加到消息历史
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": full_response,
                    "suggestions": suggestions
                })
                
                # 保存聊天历史
                kb_name = st.session_state.get('current_kb_name')
                if kb_name:
                    from src.chat import HistoryManager
                    HistoryManager.save(kb_name, st.session_state.messages)
                
            except Exception as e:
                st.error(f"❌ 生成回复时出错: {str(e)}")
        
        finally:
            # 清除处理状态
            st.session_state.is_processing = False
    
    def load_chat_engine(self):
        """加载聊天引擎"""
        kb_name = st.session_state.get('current_kb_name')
        if not kb_name:
            return
        
        try:
            from src.kb.kb_loader import KnowledgeBaseLoader
            from src.config import ConfigLoader
            
            # 获取配置
            config = ConfigLoader.load()
            embed_provider = config.get('embed_provider', 'HuggingFace (本地/极速)')
            embed_model = config.get('embed_model_hf', 'sentence-transformers/all-MiniLM-L6-v2')
            embed_key = config.get('embed_key', '')
            embed_url = config.get('embed_url', '')
            
            # 加载知识库
            output_base = os.path.join(os.getcwd(), "vector_db_storage")
            kb_loader = KnowledgeBaseLoader(output_base)
            
            chat_engine, error_msg = kb_loader.load_knowledge_base(
                kb_name, embed_provider, embed_model, embed_key, embed_url
            )
            
            if chat_engine:
                st.session_state.chat_engine = chat_engine
                st.session_state.current_kb_id = kb_name
                
                from src.app_logging import LogManager
                logger = LogManager()
                logger.success("问答引擎已启用GPU加速")
                logger.log("SUCCESS", f"知识库加载成功: {kb_name}", stage="知识库加载")
                
                st.toast(f"✅ 知识库 '{kb_name}' 挂载成功！")
                
                from src.utils.memory import cleanup_memory
                cleanup_memory()
                
                # 加载聊天历史
                from src.chat import HistoryManager
                st.session_state.messages = HistoryManager.load(kb_name)
                
            else:
                from src.app_logging import LogManager
                logger = LogManager()
                logger.log("ERROR", f"知识库加载失败: {kb_name} - {error_msg}", stage="知识库加载")
                
                if "维度不匹配" in error_msg:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 重建索引", type="primary", use_container_width=True):
                            import shutil
                            db_path = os.path.join(output_base, kb_name)
                            shutil.rmtree(db_path, ignore_errors=True)
                            st.success("✅ 索引已清理，请重新上传文档")
                            time.sleep(2)
                            st.rerun()
                    with col2:
                        if st.button("↩️ 切换模型", use_container_width=True):
                            st.info("请在侧边栏选择原模型（通常是 bge-small-zh-v1.5）")
                else:
                    st.error(f"知识库挂载失败：{error_msg}")
                
                st.session_state.chat_engine = None
                
        except Exception as e:
            st.error(f"加载聊天引擎失败: {str(e)}")
            st.session_state.chat_engine = None
    
    def generate_follow_up_questions(self, prompt: str, response: str):
        """生成追问问题"""
        try:
            from src.chat_utils_improved import generate_follow_up_questions_safe
            
            # 使用改进的追问生成
            suggestions = generate_follow_up_questions_safe(prompt, response)
            return suggestions[:3] if suggestions else []
            
        except Exception:
            # 降级到简单的追问问题
            follow_ups = [
                "能详细解释一下吗？",
                "有相关的例子吗？",
                "还有其他方法吗？"
            ]
            return follow_ups[:2]
