"""
配置表单组件
Stage 3.2.2 - 中风险重构
提取自 apppro.py
"""

import os
import streamlit as st
from typing import Tuple, Dict
from .model_selectors import (
    render_ollama_model_selector,
    render_openai_model_selector,
    render_hf_embedding_selector
)


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
            "Groq (极速)"
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
                llm_url = st.text_input("Ollama URL", defaults.get("llm_url_ollama", "http://localhost:11434"), key="config_ollama_url")
            
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
            
        elif llm_provider_choice.startswith("OpenAI"):
            llm_provider = "OpenAI"
            llm_url = st.text_input("Base URL", defaults.get("llm_url_openai", "https://api.openai.com/v1"))
            llm_key = st.text_input("API Key", defaults.get("llm_key", ""), type="password")
            llm_model = st.text_input("模型名称", defaults.get("llm_model_openai", "gpt-3.5-turbo"))
            
        elif llm_provider_choice.startswith("Azure"):
            llm_provider = "Azure OpenAI"
            llm_url = st.text_input("Azure Endpoint", defaults.get("azure_endpoint", ""), placeholder="https://{resource}.openai.azure.com/", key="config_azure_endpoint")
            llm_key = st.text_input("API Key", defaults.get("azure_key", ""), type="password", key="config_azure_key")
            llm_model = st.text_input("Deployment Name", defaults.get("azure_deployment", ""), help="在Azure控制台中部署的模型名称", key="config_azure_deployment")
            
            api_version = st.text_input("API Version", defaults.get("azure_api_version", "2023-05-15"), help="例如: 2023-05-15, 2024-02-15-preview", key="config_azure_api_version")
            extra_params = {"api_version": api_version}
            
        elif llm_provider_choice.startswith("Anthropic"):
            llm_provider = "Anthropic"
            llm_key = st.text_input("API Key", defaults.get("anthropic_key", ""), type="password", key="config_anthropic_key")
            llm_model = st.selectbox("模型", ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"], index=0, key="config_anthropic_model")
            
        elif llm_provider_choice.startswith("Moonshot"):
            llm_provider = "Moonshot"
            llm_url = st.text_input("Base URL", "https://api.moonshot.cn/v1", disabled=True, key="config_moonshot_url")
            llm_key = st.text_input("API Key", defaults.get("moonshot_key", ""), type="password", key="config_moonshot_key")
            llm_model = st.selectbox("模型", ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"], index=0, key="config_moonshot_model")
            
        elif llm_provider_choice.startswith("Gemini"):
            llm_provider = "Gemini"
            llm_key = st.text_input("API Key", defaults.get("gemini_key", ""), type="password", key="config_gemini_key")
            llm_model = st.selectbox("模型", ["gemini-pro", "gemini-pro-vision"], index=0, key="config_gemini_model")
            
        elif llm_provider_choice.startswith("Groq"):
            llm_provider = "Groq"
            llm_url = st.text_input("Base URL", "https://api.groq.com/openai/v1", disabled=True, key="config_groq_url")
            llm_key = st.text_input("API Key", defaults.get("groq_key", ""), type="password", key="config_groq_key")
            llm_model = st.selectbox("模型", ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"], index=0, key="config_groq_model")

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
                saved_model = defaults.get("embed_model_hf", "BAAI/bge-small-zh-v1.5")
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
