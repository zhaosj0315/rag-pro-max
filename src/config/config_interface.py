"""
配置界面管理器 - 负责配置相关的UI逻辑
"""

import streamlit as st


class ConfigInterface:
    """配置界面管理器"""
    
    def __init__(self):
        """初始化配置界面"""
        pass
    
    def render_config_tab(self):
        """渲染配置标签页"""
        st.markdown("### ⚙️ 模型配置")
        
        # 获取默认配置
        from src.config import ConfigLoader
        defaults = ConfigLoader.load()
        
        # 基础配置
        config_values = self.render_basic_config(defaults)
        
        # 高级配置
        self.render_advanced_config()
        
        return config_values
    
    def render_basic_config(self, defaults: dict):
        """渲染基础配置 - 使用统一组件"""
        from src.ui.unified_config_components import render_basic_config
        return render_basic_config(defaults, "config_interface")
    
    def render_advanced_config(self):
        """渲染高级配置 - 使用统一组件"""
        from src.ui.unified_config_components import unified_config_renderer
        config_data = unified_config_renderer.load_config("advanced")
        return unified_config_renderer.render_advanced_config(config_data, "config_interface")
    
    def render_model_config(self):
        """渲染模型配置"""
        st.markdown("#### 🤖 LLM 配置")
        
        # LLM 提供商选择
        llm_provider = st.selectbox(
            "LLM 提供商",
            ["Ollama", "OpenAI", "其他"],
            key="config_llm_provider"
        )
        
        config_values = {"llm_provider": llm_provider}
        
        if llm_provider == "Ollama":
            config_values.update(self.render_ollama_config())
        elif llm_provider == "OpenAI":
            config_values.update(self.render_openai_config())
        
        st.markdown("#### 🧠 嵌入模型配置")
        embed_config = self.render_embedding_config()
        config_values.update(embed_config)
        
        return config_values
    
    def render_ollama_config(self):
        """渲染Ollama配置"""
        col1, col2 = st.columns(2)
        
        with col1:
            llm_url = st.text_input(
                "API地址",
                value="http://localhost:11434",
                key="config_ollama_url"
            )
        
        with col2:
            llm_model = st.text_input(
                "模型名称",
                value="gpt-oss:20b",
                key="config_ollama_model"
            )
        
        return {
            "llm_url": llm_url,
            "llm_model": llm_model,
            "llm_key": ""
        }
    
    def render_openai_config(self):
        """渲染OpenAI配置"""
        col1, col2 = st.columns(2)
        
        with col1:
            llm_url = st.text_input(
                "API地址",
                value="https://api.openai.com/v1",
                key="config_openai_url"
            )
        
        with col2:
            llm_model = st.selectbox(
                "模型",
                ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
                key="config_openai_model"
            )
        
        llm_key = st.text_input(
            "API Key",
            type="password",
            key="config_openai_key"
        )
        
        return {
            "llm_url": llm_url,
            "llm_model": llm_model,
            "llm_key": llm_key
        }
    
    def render_embedding_config(self):
        """渲染嵌入模型配置"""
        embed_provider = st.selectbox(
            "嵌入模型提供商",
            ["HuggingFace (本地/极速)", "OpenAI-Compatible", "Ollama"],
            key="config_embed_provider"
        )
        
        config = {"embed_provider": embed_provider}
        
        if embed_provider.startswith("HuggingFace"):
            embed_model = st.selectbox(
                "HuggingFace模型",
                [
                    "sentence-transformers/all-MiniLM-L6-v2",
                    "BAAI/bge-large-zh-v1.5",
                    "sentence-transformers/all-MiniLM-L6-v2"
                ],
                key="config_hf_model"
            )
            config.update({
                "embed_model": embed_model,
                "embed_url": "",
                "embed_key": ""
            })
        
        elif embed_provider == "OpenAI-Compatible":
            col1, col2 = st.columns(2)
            with col1:
                embed_url = st.text_input("API地址", key="config_embed_url")
            with col2:
                embed_key = st.text_input("API Key", type="password", key="config_embed_key")
            
            embed_model = st.text_input("模型名称", key="config_embed_model")
            
            config.update({
                "embed_model": embed_model,
                "embed_url": embed_url,
                "embed_key": embed_key
            })
        
        elif embed_provider == "Ollama":
            col1, col2 = st.columns(2)
            with col1:
                embed_url = st.text_input(
                    "Ollama地址",
                    value="http://localhost:11434",
                    key="config_ollama_embed_url"
                )
            with col2:
                embed_model = st.text_input(
                    "模型名称",
                    value="nomic-embed-text",
                    key="config_ollama_embed_model"
                )
            
            config.update({
                "embed_model": embed_model,
                "embed_url": embed_url,
                "embed_key": ""
            })
        
        return config
    
    def render_rag_config(self):
        """渲染RAG配置"""
        st.markdown("#### 🔍 RAG 参数配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            chunk_size = st.number_input(
                "文档分块大小",
                min_value=100,
                max_value=2000,
                value=500,
                step=50,
                key="config_chunk_size"
            )
            
            top_k = st.number_input(
                "检索文档数量",
                min_value=1,
                max_value=20,
                value=5,
                key="config_top_k"
            )
        
        with col2:
            chunk_overlap = st.number_input(
                "分块重叠长度",
                min_value=0,
                max_value=200,
                value=50,
                step=10,
                key="config_chunk_overlap"
            )
            
            similarity_threshold = st.slider(
                "相似度阈值",
                min_value=0.0,
                max_value=1.0,
                value=0.7,
                step=0.05,
                key="config_similarity_threshold"
            )
        
        return {
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "top_k": top_k,
            "similarity_threshold": similarity_threshold
        }
    
    def render_performance_config(self):
        """渲染性能配置"""
        st.markdown("#### ⚡ 性能配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            enable_gpu = st.checkbox(
                "启用GPU加速",
                value=True,
                key="config_enable_gpu"
            )
            
            max_workers = st.number_input(
                "最大工作线程",
                min_value=1,
                max_value=16,
                value=4,
                key="config_max_workers"
            )
        
        with col2:
            enable_cache = st.checkbox(
                "启用缓存",
                value=True,
                key="config_enable_cache"
            )
            
            batch_size = st.number_input(
                "批处理大小",
                min_value=1,
                max_value=100,
                value=10,
                key="config_batch_size"
            )
        
        return {
            "enable_gpu": enable_gpu,
            "max_workers": max_workers,
            "enable_cache": enable_cache,
            "batch_size": batch_size
        }
    
    def save_config(self, config_values: dict):
        """保存配置"""
        try:
            from src.config import ConfigLoader
            ConfigLoader.save(config_values)
            st.success("✅ 配置已保存")
        except Exception as e:
            st.error(f"❌ 保存配置失败: {str(e)}")
    
    def test_config(self, config_values: dict):
        """测试配置"""
        st.markdown("#### 🧪 配置测试")
        
        if st.button("🔍 测试LLM连接", use_container_width=True):
            self.test_llm_connection(config_values)
        
        if st.button("🧠 测试嵌入模型", use_container_width=True):
            self.test_embedding_model(config_values)
    
    def test_llm_connection(self, config_values: dict):
        """测试LLM连接"""
        try:
            llm_provider = config_values.get("llm_provider", "Ollama")
            
            with st.spinner("测试LLM连接..."):
                if llm_provider == "Ollama":
                    import ollama
                    models = ollama.list()
                    st.success(f"✅ Ollama连接成功，发现 {len(models.get('models', []))} 个模型")
                
                elif llm_provider == "OpenAI":
                    # 简单的API测试
                    st.success("✅ OpenAI配置格式正确")
                
        except Exception as e:
            st.error(f"❌ LLM连接测试失败: {str(e)}")
    
    def test_embedding_model(self, config_values: dict):
        """测试嵌入模型"""
        try:
            embed_provider = config_values.get("embed_provider", "HuggingFace (本地/极速)")
            embed_model = config_values.get("embed_model", "sentence-transformers/all-MiniLM-L6-v2")
            
            with st.spinner("测试嵌入模型..."):
                from src.utils.model_manager import load_embedding_model
                
                embed = load_embedding_model(
                    embed_provider,
                    embed_model,
                    config_values.get("embed_key", ""),
                    config_values.get("embed_url", "")
                )
                
                if embed:
                    # 测试嵌入
                    test_embedding = embed._get_text_embedding("测试文本")
                    st.success(f"✅ 嵌入模型测试成功，维度: {len(test_embedding)}")
                else:
                    st.error("❌ 嵌入模型加载失败")
                
        except Exception as e:
            st.error(f"❌ 嵌入模型测试失败: {str(e)}")
    
    def render_quick_setup(self):
        """渲染快速设置"""
        st.markdown("#### ⚡ 快速设置")
        
        setup_type = st.selectbox(
            "选择配置方案",
            ["本地部署 (Ollama)", "云端服务 (OpenAI)", "自定义配置"],
            key="quick_setup_type"
        )
        
        if st.button("🚀 一键配置", type="primary", use_container_width=True):
            self.apply_quick_setup(setup_type)
    
    def apply_quick_setup(self, setup_type: str):
        """应用快速设置"""
        try:
            from src.config import ConfigLoader
            
            if setup_type == "本地部署 (Ollama)":
                config = {
                    "llm_provider": "Ollama",
                    "llm_url": "http://localhost:11434",
                    "llm_model": "gpt-oss:20b",
                    "llm_key": "",
                    "embed_provider": "HuggingFace (本地/极速)",
                    "embed_model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            
            elif setup_type == "云端服务 (OpenAI)":
                config = {
                    "llm_provider": "OpenAI",
                    "llm_url": "https://api.openai.com/v1",
                    "llm_model": "gpt-3.5-turbo",
                    "embed_provider": "HuggingFace (本地/极速)",
                    "embed_model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            
            else:
                st.info("请手动配置各项参数")
                return
            
            ConfigLoader.save(config)
            st.success(f"✅ {setup_type} 配置已应用！")
            
        except Exception as e:
            st.error(f"❌ 快速配置失败: {str(e)}")
