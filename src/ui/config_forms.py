"""
配置表单组件
Stage 3.2.2 - 中风险重构
提取自 apppro.py
使用统一配置组件
"""

import os
import streamlit as st
from typing import Tuple, Dict
from .model_selectors import (
    render_ollama_model_selector,
    render_openai_model_selector,
    render_hf_embedding_selector
)
from .unified_config_components import render_basic_config, render_embedding_config
from src.utils.model_utils import fetch_remote_models
from src.services.unified_config_service import save_config, load_config
from src.utils.model_manager import set_global_llm_model


def render_llm_config(defaults: dict) -> Tuple[str, str, str, str, dict]:
    """
    渲染 LLM 配置表单 (增强版)
    Returns: (provider, url, model, key, extra_params)
    """
    with st.container(border=True):
        st.markdown("#### 🤖 LLM 对话模型")
        
        # 1. 供应商选择
        provider_options = [
            "Ollama (本地)", 
            "OpenAI (云端)", 
            "Azure OpenAI", 
            "Anthropic (Claude)", 
            "Moonshot (Kimi)", 
            "Gemini (Google)", 
            "Groq (极速)",
            "Other (自定义)"
        ]
        
        # 尝试恢复上次的选择
        saved_provider = defaults.get("llm_provider_label", "Ollama (本地)")
        if saved_provider not in provider_options:
            saved_provider = "Ollama (本地)"
            
        llm_provider_choice = st.selectbox(
            "供应商",
            provider_options,
            index=provider_options.index(saved_provider),
            key="config_llm_provider_select"
        )
        
        # 保存显示标签以便下次恢复
        st.session_state.llm_provider_label = llm_provider_choice
        
        llm_provider = ""
        llm_url = ""
        llm_model = ""
        llm_key = ""
        extra_params = {}

        # 2. 动态配置表单
        if llm_provider_choice.startswith("Ollama"):
            llm_provider = "Ollama"
            col_url, col_status = st.columns([3, 1])
            with col_url:
                llm_url = st.text_input("Ollama URL", defaults.get("llm_url_ollama") or "http://localhost:11434", key="config_ollama_url")
            
            from src.utils.model_utils import check_ollama_status
            ollama_ok = check_ollama_status(llm_url)
            
            with col_status:
                st.write("")
                if ollama_ok:
                    st.caption("✅ 已连接")
                else:
                    st.caption("⚠️ 未运行")
            
            saved_model = defaults.get("llm_model_ollama", "gpt-oss:20b")
            llm_model, _ = render_ollama_model_selector(llm_url, saved_model, ollama_ok)
            
            # 持久化保存按钮 (新增)
            if st.button("💾 保存 Ollama 配置", key="save_ollama_config"):
                config_data = {
                    "llm_provider": "Ollama",
                    "llm_url_ollama": llm_url,
                    "llm_model_ollama": llm_model,
                    "llm_provider_label": "Ollama (本地)"
                }
                
                # 加载现有配置并合并
                existing_config = load_config("rag_config")
                existing_config.update(config_data)
                
                # 保存到 rag_config.json
                if save_config(existing_config, "rag_config"):
                    # 立即生效：更新全局 LLM
                    if set_global_llm_model(llm_provider, llm_model, "", llm_url):
                        st.success("✅ Ollama 配置已保存并生效 (Hot Reload)")
                        st.session_state.selected_model = llm_model
                    else:
                        st.warning("⚠️ 配置已保存，但热更新失败")
                        
                    defaults.update(config_data)
                else:
                    st.error("❌ 保存失败")
            
        elif llm_provider_choice.startswith("OpenAI"):
            llm_provider = "OpenAI"
            
            col1, col2 = st.columns([2, 1])
            with col1:
                llm_url = st.text_input("Base URL", defaults.get("llm_url_openai", "https://api.openai.com/v1"), key="config_openai_url")
            with col2:
                llm_key = st.text_input("API Key", defaults.get("llm_key", ""), type="password", key="config_openai_key")
            
            # 自动获取模型逻辑
            # 使用 URL + Key 作为缓存键
            cache_key = f"models_openai_{llm_url}_{llm_key}"
            available_models = st.session_state.get(cache_key, [])
            
            # 如果没有缓存且有足够的凭证，尝试获取
            if not available_models and llm_url and llm_key:
                with st.spinner("🔄 正在自动加载模型列表..."):
                    models, err = fetch_remote_models(llm_url, llm_key)
                    if models:
                        available_models = models
                        st.session_state[cache_key] = models
                        st.toast(f"✅ 已加载 {len(models)} 个模型")
                    elif err:
                        st.caption(f"⚠️ 无法加载模型: {err}")
            
            # 模型选择器
            saved_model = defaults.get("llm_model_openai", "gpt-3.5-turbo")
            
            if available_models:
                # 确保保存的模型在列表中
                if saved_model not in available_models:
                    available_models.insert(0, saved_model)
                
                llm_model = st.selectbox(
                    "选择模型", 
                    available_models, 
                    index=available_models.index(saved_model) if saved_model in available_models else 0,
                    key="config_openai_model_select"
                )
            else:
                llm_model = st.text_input("模型名称", saved_model, help="无法自动加载时请手动输入", key="config_openai_model_input")
            
            # 持久化保存按钮
            if st.button("💾 保存 OpenAI 配置", key="save_openai_config"):
                config_data = {
                    "llm_provider": "OpenAI",
                    "llm_url_openai": llm_url,
                    "llm_key": llm_key,
                    "llm_model_openai": llm_model,
                    "llm_provider_label": "OpenAI (云端)"
                }
                
                # 加载现有配置并合并
                existing_config = load_config("rag_config")
                existing_config.update(config_data)
                
                # 保存到 rag_config.json
                if save_config(existing_config, "rag_config"):
                    # 立即生效：更新全局 LLM
                    if set_global_llm_model(llm_provider, llm_model, llm_key, llm_url):
                        st.success("✅ 配置已保存并生效 (Hot Reload)")
                        st.session_state.selected_model = llm_model  # <--- 关键修复：立即更新前端状态
                    else:
                        st.warning("⚠️ 配置已保存，但热更新失败")
                        
                    # 同时也更新当前的 defaults 以便即时生效 (可选)
                    defaults.update(config_data)
                else:
                    st.error("❌ 保存失败")

        elif llm_provider_choice.startswith("Other"):
            llm_provider = "OpenAI-Compatible"
            st.caption("💡 适用于 DeepSeek, Yi, ChatGLM, vLLM 等兼容 OpenAI 协议的服务")
            
            col1, col2 = st.columns([2, 1])
            with col1:
                # 智能回退：如果 specific key 为空，尝试使用 generic key
                def_url = defaults.get("llm_url_other") or defaults.get("llm_url") or "https://api.deepseek.com/v1"
                llm_url = st.text_input("Base URL", def_url, key="config_other_url")
            with col2:
                # 智能回退：如果 specific key 为空，尝试使用 generic key
                def_key = defaults.get("llm_key_other") or defaults.get("llm_key", "")
                llm_key = st.text_input("API Key", def_key, type="password", key="config_other_key")
            
            # 自动获取模型逻辑 (复用 OpenAI 逻辑)
            cache_key = f"models_other_{llm_url}_{llm_key}"
            available_models = st.session_state.get(cache_key, [])
            
            if not available_models and llm_url:
                with st.spinner("🔄 正在探测模型列表..."):
                    models, err = fetch_remote_models(llm_url, llm_key)
                    if models:
                        available_models = models
                        st.session_state[cache_key] = models
                        st.toast(f"✅ 已加载 {len(models)} 个模型")
            
            saved_model = defaults.get("llm_model_other", "")
            
            if available_models:
                if saved_model and saved_model not in available_models:
                    available_models.insert(0, saved_model)
                
                llm_model = st.selectbox(
                    "选择模型", 
                    available_models, 
                    index=available_models.index(saved_model) if saved_model in available_models else 0,
                    key="config_other_model_select"
                )
            else:
                llm_model = st.text_input("模型名称", saved_model, placeholder="例如: deepseek-chat", key="config_other_model_input")
            
            if st.button("💾 保存自定义配置", key="save_other_config"):
                config_data = {
                    "llm_provider": "OpenAI-Compatible", # 内部标识为兼容模式
                    "llm_url_other": llm_url,
                    "llm_key_other": llm_key,
                    "llm_model_other": llm_model,
                    "llm_provider_label": "Other (自定义)"
                }
                
                # 为了兼容统一读取逻辑，我们同时也写入标准字段
                config_data["llm_url"] = llm_url
                config_data["llm_key"] = llm_key
                config_data["llm_model"] = llm_model
                
                # 加载现有配置并合并
                existing_config = load_config("rag_config")
                existing_config.update(config_data)
                
                if save_config(existing_config, "rag_config"):
                    if set_global_llm_model("OpenAI-Compatible", llm_model, llm_key, llm_url):
                        st.success("✅ 自定义配置已保存并生效")
                        st.session_state.selected_model = llm_model  # <--- 关键修复：立即更新前端状态
                    defaults.update(config_data)
                else:
                    st.error("❌ 保存失败")
            
        elif llm_provider_choice.startswith("Azure"):
            llm_provider = "Azure OpenAI"
            llm_url = st.text_input("Azure Endpoint", defaults.get("azure_endpoint", ""), placeholder="https://{resource}.openai.azure.com/", key="config_azure_endpoint")
            llm_key = st.text_input("API Key", defaults.get("azure_key", ""), type="password", key="config_azure_key")
            llm_model = st.text_input("Deployment Name", defaults.get("azure_deployment", ""), help="在Azure控制台中部署的模型名称", key="config_azure_deployment")
            
            api_version = st.text_input("API Version", defaults.get("azure_api_version", "2023-05-15"), help="例如: 2023-05-15, 2024-02-15-preview", key="config_azure_api_version")
            extra_params = {"api_version": api_version}
            
            if st.button("💾 保存 Azure 配置", key="save_azure_config"):
                config_data = {
                    "llm_provider": "Azure OpenAI",
                    "azure_endpoint": llm_url,
                    "azure_key": llm_key,
                    "azure_deployment": llm_model,
                    "azure_api_version": api_version,
                    "llm_provider_label": "Azure OpenAI",
                    # 兼容性字段
                    "llm_url": llm_url,
                    "llm_key": llm_key,
                    "llm_model": llm_model
                }
                
                existing_config = load_config("rag_config")
                existing_config.update(config_data)
                
                if save_config(existing_config, "rag_config"):
                    if set_global_llm_model("Azure OpenAI", llm_model, llm_key, llm_url, api_version=api_version):
                        st.success("✅ Azure 配置已保存并生效")
                        st.session_state.selected_model = llm_model
                    else:
                        st.warning("⚠️ 保存成功但热更新失败")
                    defaults.update(config_data)
                else:
                    st.error("❌ 保存失败")
            
        elif llm_provider_choice.startswith("Anthropic"):
            llm_provider = "Anthropic"
            llm_key = st.text_input("API Key", defaults.get("anthropic_key", ""), type="password", key="config_anthropic_key")
            llm_model = st.selectbox("模型", ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"], index=0, key="config_anthropic_model")
            
            if st.button("💾 保存 Anthropic 配置", key="save_anthropic_config"):
                config_data = {
                    "llm_provider": "Anthropic",
                    "anthropic_key": llm_key,
                    "config_anthropic_model": llm_model,
                    "llm_provider_label": "Anthropic (Claude)",
                    "llm_key": llm_key,
                    "llm_model": llm_model
                }
                
                existing_config = load_config("rag_config")
                existing_config.update(config_data)
                
                if save_config(existing_config, "rag_config"):
                    if set_global_llm_model("Anthropic", llm_model, llm_key):
                        st.success("✅ Anthropic 配置已保存并生效")
                        st.session_state.selected_model = llm_model
                    defaults.update(config_data)
                else:
                    st.error("❌ 保存失败")
            
        elif llm_provider_choice.startswith("Moonshot"):
            llm_provider = "Moonshot"
            llm_url = st.text_input("Base URL", "https://api.moonshot.cn/v1", disabled=True, key="config_moonshot_url")
            llm_key = st.text_input("API Key", defaults.get("moonshot_key", ""), type="password", key="config_moonshot_key")
            llm_model = st.selectbox("模型", ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"], index=0, key="config_moonshot_model")
            
            if st.button("💾 保存 Moonshot 配置", key="save_moonshot_config"):
                config_data = {
                    "llm_provider": "Moonshot",
                    "moonshot_key": llm_key,
                    "config_moonshot_model": llm_model,
                    "llm_provider_label": "Moonshot (Kimi)",
                    "llm_key": llm_key,
                    "llm_model": llm_model,
                    "llm_url": llm_url
                }
                
                existing_config = load_config("rag_config")
                existing_config.update(config_data)
                
                if save_config(existing_config, "rag_config"):
                    if set_global_llm_model("Moonshot", llm_model, llm_key, llm_url):
                        st.success("✅ Moonshot 配置已保存并生效")
                        st.session_state.selected_model = llm_model
                    defaults.update(config_data)
                else:
                    st.error("❌ 保存失败")
            
        elif llm_provider_choice.startswith("Gemini"):
            llm_provider = "Gemini"
            llm_key = st.text_input("API Key", defaults.get("gemini_key", ""), type="password", key="config_gemini_key")
            llm_model = st.selectbox("模型", ["gemini-pro", "gemini-pro-vision"], index=0, key="config_gemini_model")
            
            if st.button("💾 保存 Gemini 配置", key="save_gemini_config"):
                config_data = {
                    "llm_provider": "Gemini",
                    "gemini_key": llm_key,
                    "config_gemini_model": llm_model,
                    "llm_provider_label": "Gemini (Google)",
                    "llm_key": llm_key,
                    "llm_model": llm_model
                }
                
                existing_config = load_config("rag_config")
                existing_config.update(config_data)
                
                if save_config(existing_config, "rag_config"):
                    if set_global_llm_model("Gemini", llm_model, llm_key):
                        st.success("✅ Gemini 配置已保存并生效")
                        st.session_state.selected_model = llm_model
                    defaults.update(config_data)
                else:
                    st.error("❌ 保存失败")
            
        elif llm_provider_choice.startswith("Groq"):
            llm_provider = "Groq"
            llm_url = st.text_input("Base URL", "https://api.groq.com/openai/v1", disabled=True, key="config_groq_url")
            llm_key = st.text_input("API Key", defaults.get("groq_key", ""), type="password", key="config_groq_key")
            llm_model = st.selectbox("模型", ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"], index=0, key="config_groq_model")

            if st.button("💾 保存 Groq 配置", key="save_groq_config"):
                config_data = {
                    "llm_provider": "Groq",
                    "groq_key": llm_key,
                    "config_groq_model": llm_model,
                    "llm_provider_label": "Groq (极速)",
                    "llm_key": llm_key,
                    "llm_model": llm_model,
                    "llm_url": llm_url
                }
                
                existing_config = load_config("rag_config")
                existing_config.update(config_data)
                
                if save_config(existing_config, "rag_config"):
                    if set_global_llm_model("Groq", llm_model, llm_key, llm_url):
                        st.success("✅ Groq 配置已保存并生效")
                        st.session_state.selected_model = llm_model
                    defaults.update(config_data)
                else:
                    st.error("❌ 保存失败")

    return llm_provider, llm_url, llm_model, llm_key, extra_params

    return llm_provider, llm_url, llm_model, llm_key, extra_params


def render_embedding_config(defaults: dict) -> Tuple[str, str, str, str]:
    """
    渲染 Embedding 配置表单 (优化版)
    """
    with st.container(border=True):
        st.markdown("#### 🧬 向量模型 (Embedding)")
        
        embed_idx = defaults.get("embed_provider_idx", 0)
        if embed_idx > 2: embed_idx = 0
        
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            embed_provider = st.selectbox(
                "供应商",
                ["HuggingFace (本地/极速)", "OpenAI-Compatible", "Ollama"],
                index=embed_idx,
                key="config_embed_provider",
                label_visibility="collapsed"
            )
        
        with col2:
            if embed_provider.startswith("HuggingFace"):
                saved_model = defaults.get("embed_model_hf", "sentence-transformers/all-MiniLM-L6-v2")
                embed_model = render_hf_embedding_selector(saved_model)
                embed_url = ""
                embed_key = ""
                
                # 处理默认保存
                if st.session_state.get('save_embed_model'):
                    from src.config import ConfigLoader
                    import time
                    config = ConfigLoader.load()
                    config["embed_model_hf"] = st.session_state.save_embed_model
                    ConfigLoader.save(config)
                    st.toast(f"✅ 默认嵌入模型已更新")
                    del st.session_state.save_embed_model
                    time.sleep(1)
                    st.rerun()
            elif embed_provider.startswith("OpenAI"):
                embed_model = st.text_input("模型名", defaults.get("embed_model_openai", "text-embedding-3-small"))
                embed_url = st.text_input("Base URL", defaults.get("embed_url_openai", "https://api.openai.com/v1"))
                embed_key = st.text_input("API Key", defaults.get("embed_key", ""), type="password")
            else:  # Ollama
                embed_model = st.text_input("模型名", defaults.get("embed_model_ollama", "nomic-embed-text"))
                embed_url = st.text_input("URL", defaults.get("embed_url_ollama", "http://localhost:11434"))
                embed_key = ""
                
    return embed_provider, embed_model, embed_url, embed_key


def render_basic_config(defaults: dict) -> dict:
    """
    渲染完整的基础配置区域
    
    Args:
        defaults: 默认配置字典
        
    Returns:
        dict: 配置字典
    """
    # LLM 配置 (接收 5 个返回值)
    llm_provider, llm_url, llm_model, llm_key, extra_params = render_llm_config(defaults)
    
    # Embedding 配置
    embed_provider, embed_model, embed_url, embed_key = render_embedding_config(defaults)
    
    # 合并 extra_params 到返回结果
    result = {
        'llm_provider': llm_provider,
        'llm_url': llm_url,
        'llm_model': llm_model,
        'llm_key': llm_key,
        'embed_provider': embed_provider,
        'embed_model': embed_model,
        'embed_url': embed_url,
        'embed_key': embed_key
    }
    result.update(extra_params)
    return result
