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


def render_llm_config(defaults: dict) -> Tuple[str, str, str, str]:
    """
    渲染 LLM 配置表单
    
    Args:
        defaults: 默认配置字典
        
    Returns:
        Tuple[str, str, str, str]: (provider, url, model, key)
    """
    st.markdown("**LLM 对话模型**")
    
    llm_provider_choice = st.radio(
        "供应商",
        ["Ollama (本地)", "OpenAI-Compatible (云端)"],
        horizontal=True,
        label_visibility="collapsed",
        key="config_llm_provider_radio"
    )
    
    if llm_provider_choice.startswith("Ollama"):
        llm_provider = "Ollama"
        # Ollama URL 和状态同行显示
        col_url, col_status = st.columns([3, 1])
        with col_url:
            llm_url = st.text_input("Ollama URL", defaults.get("llm_url_ollama", "http://localhost:11434"), key="config_ollama_url")
        
        # 检测 Ollama 状态
        from src.utils.model_utils import check_ollama_status
        ollama_ok = check_ollama_status(llm_url)
        
        with col_status:
            st.write("")  # 占位，对齐输入框
            if ollama_ok:
                st.success("✅ Ollama 已连接")
            else:
                st.warning("⚠️ Ollama 未运行")
        
        # 使用模型选择器组件
        saved_model = defaults.get("llm_model_ollama", "qwen2.5:7b")
        llm_model, save_as_default = render_ollama_model_selector(llm_url, saved_model, ollama_ok)
        
        # 处理"设为默认"
        if save_as_default:
            from src.config import ConfigLoader
            import time
            config = ConfigLoader.load()
            config["llm_model_ollama"] = llm_model
            ConfigLoader.save(config)
            st.success(f"✅ 已设为默认: {llm_model}")
            time.sleep(1)
            st.rerun()
        
        llm_key = ""
    else:
        llm_provider = "OpenAI-Compatible"
        llm_url = st.text_input("Base URL", defaults.get("llm_url_openai", "https://api.deepseek.com"))
        
        # 优先从环境变量获取 Key
        env_key = os.getenv('OPENAI_API_KEY', "")
        default_key = defaults.get("llm_key", "") or env_key
        
        llm_key = st.text_input(
            "API Key",
            value=default_key,
            type="password",
            help="可从环境变量 OPENAI_API_KEY 自动加载"
        )
        
        # 使用模型选择器组件
        saved_model = defaults.get("llm_model_openai", "deepseek-chat")
        llm_model = render_openai_model_selector(llm_url, llm_key, saved_model)
    
    return llm_provider, llm_url, llm_model, llm_key


def render_embedding_config(defaults: dict) -> Tuple[str, str, str, str]:
    """
    渲染 Embedding 配置表单
    
    Args:
        defaults: 默认配置字典
        
    Returns:
        Tuple[str, str, str, str]: (provider, model, url, key)
    """
    st.markdown("---")
    st.markdown("**Embedding 向量模型**")
    st.caption("💡 用于理解文档语义")
    
    embed_idx = defaults.get("embed_provider_idx", 0)
    if embed_idx > 2:
        embed_idx = 0
    
    embed_provider = st.selectbox(
        "供应商",
        ["HuggingFace (本地/极速)", "OpenAI-Compatible", "Ollama"],
        index=embed_idx,
        key="config_embed_provider"
    )
    
    if embed_provider.startswith("HuggingFace"):
        # 使用 HF 嵌入模型选择器组件
        saved_model = defaults.get("embed_model_hf", "BAAI/bge-small-zh-v1.5")
        embed_model = render_hf_embedding_selector(saved_model)
        
        # 处理"设为默认"信号
        if st.session_state.get('save_embed_model'):
            from src.config import ConfigLoader
            import time
            config = ConfigLoader.load()
            config["embed_model_hf"] = st.session_state.save_embed_model
            ConfigLoader.save(config)
            st.success(f"✅ 已设为默认")
            time.sleep(1)
            del st.session_state.save_embed_model
            st.rerun()
        
        embed_url = ""
        embed_key = ""
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
        dict: 配置字典 {
            'llm_provider': str,
            'llm_url': str,
            'llm_model': str,
            'llm_key': str,
            'embed_provider': str,
            'embed_model': str,
            'embed_url': str,
            'embed_key': str
        }
    """
    with st.expander("⚙️ 基础配置", expanded=True):
        # LLM 配置
        llm_provider, llm_url, llm_model, llm_key = render_llm_config(defaults)
        
        # Embedding 配置
        embed_provider, embed_model, embed_url, embed_key = render_embedding_config(defaults)
    
    return {
        'llm_provider': llm_provider,
        'llm_url': llm_url,
        'llm_model': llm_model,
        'llm_key': llm_key,
        'embed_provider': embed_provider,
        'embed_model': embed_model,
        'embed_url': embed_url,
        'embed_key': embed_key
    }
