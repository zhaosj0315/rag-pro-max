"""
紧凑侧边栏组件 - 手风琴式布局
"""

import streamlit as st
import psutil
import os

def render_compact_sidebar():
    """渲染紧凑的手风琴式侧边栏"""
    
    with st.sidebar:
        st.markdown("# 🚀 RAG Pro Max")
        
        # 1. 知识库管理 (默认展开)
        with st.expander("📚 知识库", expanded=True):
            # 获取知识库列表
            kb_dir = "vector_db_storage"
            kb_list = []
            if os.path.exists(kb_dir):
                kb_list = [d for d in os.listdir(kb_dir) if os.path.isdir(os.path.join(kb_dir, d))]
            
            if kb_list:
                selected_kb = st.selectbox("当前知识库", kb_list, key="kb_selector")
                st.session_state.active_kb_name = selected_kb
            else:
                st.info("暂无知识库")
                st.session_state.active_kb_name = None
            
            # 操作按钮 (3列布局)
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("➕", help="新建", key="create_kb_btn"):
                    st.session_state.show_create_kb = True
            with col2:
                if st.button("🔄", help="刷新", key="refresh_kb_btn"):
                    st.rerun()
            with col3:
                if st.button("🗑️", help="删除", key="delete_kb_btn", disabled=not kb_list):
                    if st.session_state.get('active_kb_name'):
                        st.session_state.show_delete_confirm = True
        
        # 新建知识库对话框
        if st.session_state.get('show_create_kb', False):
            with st.container():
                st.markdown("**新建知识库**")
                new_kb_name = st.text_input("名称", placeholder="输入知识库名称...", key="new_kb_input")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("创建", key="confirm_create"):
                        if new_kb_name.strip():
                            st.session_state.active_kb_name = new_kb_name.strip()
                            st.session_state.show_create_kb = False
                            st.success(f"知识库 '{new_kb_name}' 已创建")
                            st.rerun()
                with col2:
                    if st.button("取消", key="cancel_create"):
                        st.session_state.show_create_kb = False
                        st.rerun()
        
        # 2. 文档上传
        with st.expander("📁 文档上传"):
            uploaded_files = st.file_uploader(
                "选择文件",
                type=['pdf', 'txt', 'docx', 'md', 'xlsx', 'pptx', 'csv'],
                accept_multiple_files=True,
                key="file_uploader"
            )
            
            if uploaded_files:
                st.success(f"已选择 {len(uploaded_files)} 个文件")
                if st.button("🚀 开始处理", use_container_width=True, key="process_files"):
                    if st.session_state.get('active_kb_name'):
                        # 使用回调方式设置状态
                        st.session_state['uploaded_files'] = uploaded_files
                        st.session_state['should_process_files'] = True
                        st.rerun()
                    else:
                        st.error("请先选择或创建知识库")
        
        # 3. 模型配置
        with st.expander("🤖 模型设置"):
            # LLM配置
            llm_provider = st.radio("LLM提供商", ["Ollama", "OpenAI"], horizontal=True, key="llm_provider")
            
            if llm_provider == "Ollama":
                ollama_url = st.text_input("Ollama URL", "http://localhost:11434", key="ollama_url")
                ollama_models = ["qwen2.5:7b", "llama3:8b", "gpt-oss:20b"]
                selected_model = st.selectbox("模型", ollama_models, key="ollama_model")
            else:
                openai_key = st.text_input("OpenAI API Key", type="password", key="openai_key")
                openai_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
                selected_model = st.selectbox("模型", openai_models, key="openai_model")
            
            # 嵌入模型
            embed_models = ["BAAI/bge-small-zh-v1.5", "BAAI/bge-large-zh-v1.5"]
            embed_model = st.selectbox("嵌入模型", embed_models, key="embed_model")
        
        # 4. 检索配置
        with st.expander("🔍 检索参数"):
            col1, col2 = st.columns(2)
            with col1:
                chunk_size = st.number_input("块大小", 200, 2000, 1000, step=100, key="chunk_size")
            with col2:
                top_k = st.number_input("检索数量", 1, 20, 5, key="top_k")
            
            similarity_threshold = st.slider("相似度阈值", 0.0, 1.0, 0.7, 0.1, key="similarity")
        
        # 5. 系统监控
        with st.expander("📊 系统状态"):
            # 获取系统信息
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # 显示指标
            col1, col2 = st.columns(2)
            with col1:
                color = "🟢" if cpu_percent < 70 else "🟡" if cpu_percent < 90 else "🔴"
                st.metric("CPU", f"{cpu_percent:.0f}%", delta=color)
            with col2:
                color = "🟢" if memory.percent < 70 else "🟡" if memory.percent < 85 else "🔴"
                st.metric("内存", f"{memory.percent:.0f}%", delta=color)
            
            # 快速操作
            if st.button("🧹 清理内存", use_container_width=True, key="cleanup_memory"):
                import gc
                collected = gc.collect()
                st.success(f"已清理 {collected} 个对象")
        
        # 6. 工具箱
        with st.expander("🛠️ 工具"):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📖 帮助", key="show_help"):
                    st.session_state.show_help_modal = True
            with col2:
                if st.button("⚙️ 设置", key="show_settings"):
                    st.session_state.show_settings_modal = True
            
            # 重置按钮
            if st.button("🔄 重置会话", use_container_width=True, key="reset_session"):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("会话已重置")
                st.rerun()
        
        # 底部版本信息
        st.markdown("---")
        st.caption("RAG Pro Max v1.7.4")
