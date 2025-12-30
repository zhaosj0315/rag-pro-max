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
from src.utils.model_utils import fetch_remote_models
from src.services.unified_config_service import save_config, load_config
from src.utils.model_manager import set_global_llm_model


def render_llm_config(defaults: dict) -> Tuple[str, str, str, str, dict]:
    """
    渲染 LLM 配置表单 (优化版 - 仿 ChatOllama 布局)
    """
    st.markdown("#### 🧠 模型服务配置")
    
    # 定义供应商列表
    PROVIDERS = {
        "Ollama": "🦙 Ollama (本地)",
        "OpenAI": "☁️ OpenAI (云端)",
        "OpenAI-Compatible": "🔌 Other (兼容协议)",
        "Azure OpenAI": "🟦 Azure OpenAI",
        "Anthropic": "🧠 Anthropic (Claude)",
        "Moonshot": "🌙 Moonshot (Kimi)",
        "Gemini": "💎 Gemini (Google)",
        "Groq": "⚡ Groq (极速)"
    }
    
    # 布局: 左侧导航，右侧详情
    col_nav, col_form = st.columns([1, 3])
    
    # --- 左侧导航栏 ---
    with col_nav:
        st.markdown("##### 服务商")
        
        # 尝试恢复上次的选择 (将 label 转换为 key)
        saved_label = defaults.get("llm_provider_label", "Ollama (本地)")
        default_key = "Ollama"
        for k, v in PROVIDERS.items():
            if v == saved_label:
                default_key = k
                break
        
        # 能够保持状态的选择器
        selected_key = st.radio(
            "选择服务商",
            options=list(PROVIDERS.keys()),
            format_func=lambda x: PROVIDERS[x],
            index=list(PROVIDERS.keys()).index(default_key) if default_key in PROVIDERS else 0,
            key="llm_provider_nav",
            label_visibility="collapsed"
        )
        st.caption("选择 AI 服务提供商配置连接与模型")

    # --- 右侧配置表单 ---
    llm_provider = selected_key
    llm_url = ""
    llm_model = ""
    llm_key = ""
    extra_params = {}
    
    with col_form:
        st.markdown(f"#### {PROVIDERS[selected_key]} 设置")
        
        # 1. Ollama
        if selected_key == "Ollama":
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
            
            # 按钮区域
            if st.button("💾 保存 Ollama 配置", key="save_ollama_config", type="primary"):
                config_data = {
                    "llm_provider": "Ollama",
                    "llm_url_ollama": llm_url,
                    "llm_model_ollama": llm_model,
                    "llm_provider_label": PROVIDERS["Ollama"]
                }
                _save_and_apply_config(config_data, "Ollama", llm_model, "", llm_url, defaults)

        # 2. OpenAI
        elif selected_key == "OpenAI":
            col1, col2 = st.columns([2, 1])
            with col1:
                llm_url = st.text_input("Base URL", defaults.get("llm_url_openai", "https://api.openai.com/v1"), key="config_openai_url")
            with col2:
                llm_key = st.text_input("API Key", defaults.get("llm_key", ""), type="password", key="config_openai_key")
            
            # 模型选择逻辑
            saved_model = defaults.get("llm_model_openai", "gpt-3.5-turbo")
            llm_model = _render_remote_model_selector(llm_url, llm_key, saved_model, "openai")
            
            if st.button("💾 保存 OpenAI 配置", key="save_openai_config", type="primary"):
                config_data = {
                    "llm_provider": "OpenAI",
                    "llm_url_openai": llm_url,
                    "llm_key": llm_key,
                    "llm_model_openai": llm_model,
                    "llm_provider_label": PROVIDERS["OpenAI"]
                }
                _save_and_apply_config(config_data, "OpenAI", llm_model, llm_key, llm_url, defaults)

        # 3. OpenAI-Compatible (Other)
        elif selected_key == "OpenAI-Compatible":
            st.caption("💡 适用于 DeepSeek, Yi, ChatGLM, vLLM 等兼容 OpenAI 协议的服务")
            col1, col2 = st.columns([2, 1])
            with col1:
                def_url = defaults.get("llm_url_other") or defaults.get("llm_url") or "https://api.deepseek.com/v1"
                llm_url = st.text_input("Base URL", def_url, key="config_other_url")
            with col2:
                def_key = defaults.get("llm_key_other") or defaults.get("llm_key", "")
                llm_key = st.text_input("API Key", def_key, type="password", key="config_other_key")
            
            saved_model = defaults.get("llm_model_other", "")
            llm_model = _render_remote_model_selector(llm_url, llm_key, saved_model, "other")
            
            if st.button("💾 保存自定义配置", key="save_other_config", type="primary"):
                config_data = {
                    "llm_provider": "OpenAI-Compatible",
                    "llm_url_other": llm_url,
                    "llm_key_other": llm_key,
                    "llm_model_other": llm_model,
                    "llm_provider_label": PROVIDERS["OpenAI-Compatible"],
                    # 兼容字段
                    "llm_url": llm_url,
                    "llm_key": llm_key,
                    "llm_model": llm_model
                }
                _save_and_apply_config(config_data, "OpenAI-Compatible", llm_model, llm_key, llm_url, defaults)

        # 4. Azure OpenAI
        elif selected_key == "Azure OpenAI":
            llm_url = st.text_input("Azure Endpoint", defaults.get("azure_endpoint", ""), placeholder="https://{resource}.openai.azure.com/", key="config_azure_endpoint")
            llm_key = st.text_input("API Key", defaults.get("azure_key", ""), type="password", key="config_azure_key")
            llm_model = st.text_input("Deployment Name", defaults.get("azure_deployment", ""), help="在Azure控制台中部署的模型名称", key="config_azure_deployment")
            api_version = st.text_input("API Version", defaults.get("azure_api_version", "2023-05-15"), help="例如: 2023-05-15", key="config_azure_api_version")
            extra_params = {"api_version": api_version}
            
            if st.button("💾 保存 Azure 配置", key="save_azure_config", type="primary"):
                config_data = {
                    "llm_provider": "Azure OpenAI",
                    "azure_endpoint": llm_url,
                    "azure_key": llm_key,
                    "azure_deployment": llm_model,
                    "azure_api_version": api_version,
                    "llm_provider_label": PROVIDERS["Azure OpenAI"],
                    "llm_url": llm_url,
                    "llm_key": llm_key,
                    "llm_model": llm_model
                }
                _save_and_apply_config(config_data, "Azure OpenAI", llm_model, llm_key, llm_url, defaults, api_version=api_version)

        # 5. Anthropic
        elif selected_key == "Anthropic":
            llm_key = st.text_input("API Key", defaults.get("anthropic_key", ""), type="password", key="config_anthropic_key")
            llm_model = st.selectbox("模型", ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"], index=0, key="config_anthropic_model")
            
            if st.button("💾 保存 Anthropic 配置", key="save_anthropic_config", type="primary"):
                config_data = {
                    "llm_provider": "Anthropic",
                    "anthropic_key": llm_key,
                    "config_anthropic_model": llm_model,
                    "llm_provider_label": PROVIDERS["Anthropic"],
                    "llm_key": llm_key,
                    "llm_model": llm_model
                }
                _save_and_apply_config(config_data, "Anthropic", llm_model, llm_key, "", defaults)

        # 6. Moonshot
        elif selected_key == "Moonshot":
            llm_url = "https://api.moonshot.cn/v1"
            st.text_input("Base URL", llm_url, disabled=True, key="config_moonshot_url")
            llm_key = st.text_input("API Key", defaults.get("moonshot_key", ""), type="password", key="config_moonshot_key")
            llm_model = st.selectbox("模型", ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"], index=0, key="config_moonshot_model")
            
            if st.button("💾 保存 Moonshot 配置", key="save_moonshot_config", type="primary"):
                config_data = {
                    "llm_provider": "Moonshot",
                    "moonshot_key": llm_key,
                    "config_moonshot_model": llm_model,
                    "llm_provider_label": PROVIDERS["Moonshot"],
                    "llm_key": llm_key,
                    "llm_model": llm_model,
                    "llm_url": llm_url
                }
                _save_and_apply_config(config_data, "Moonshot", llm_model, llm_key, llm_url, defaults)
        
        # 7. Gemini
        elif selected_key == "Gemini":
            llm_key = st.text_input("API Key", defaults.get("gemini_key", ""), type="password", key="config_gemini_key")
            llm_model = st.selectbox("模型", ["gemini-pro", "gemini-pro-vision"], index=0, key="config_gemini_model")
            
            if st.button("💾 保存 Gemini 配置", key="save_gemini_config", type="primary"):
                config_data = {
                    "llm_provider": "Gemini",
                    "gemini_key": llm_key,
                    "config_gemini_model": llm_model,
                    "llm_provider_label": PROVIDERS["Gemini"],
                    "llm_key": llm_key,
                    "llm_model": llm_model
                }
                _save_and_apply_config(config_data, "Gemini", llm_model, llm_key, "", defaults)
        
        # 8. Groq
        elif selected_key == "Groq":
            llm_url = "https://api.groq.com/openai/v1"
            st.text_input("Base URL", llm_url, disabled=True, key="config_groq_url")
            llm_key = st.text_input("API Key", defaults.get("groq_key", ""), type="password", key="config_groq_key")
            llm_model = st.selectbox("模型", ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"], index=0, key="config_groq_model")

            if st.button("💾 保存 Groq 配置", key="save_groq_config", type="primary"):
                config_data = {
                    "llm_provider": "Groq",
                    "groq_key": llm_key,
                    "config_groq_model": llm_model,
                    "llm_provider_label": PROVIDERS["Groq"],
                    "llm_key": llm_key,
                    "llm_model": llm_model,
                    "llm_url": llm_url
                }
                _save_and_apply_config(config_data, "Groq", llm_model, llm_key, llm_url, defaults)

        # --- 通用对话设置 (仿 Screenshot) ---
        st.divider()
        st.markdown("##### 💬 对话设置")
        
        # 1. 附带消息条数 (Context Window)
        current_limit = defaults.get("chat_history_limit", 10)
        history_limit = st.slider(
            "附带历史消息数 (Context Window)", 
            min_value=1, 
            max_value=50, 
            value=current_limit,
            help="每次对话发送给模型的历史消息数量 (+1 表示加上当前问题)"
        )

        # 保存逻辑 (仅针对 Context Window)
        has_changes = (history_limit != current_limit)
        
        if has_changes:
            if st.button("💾 保存对话设置", key="save_chat_settings", type="primary"):
                config_data = {
                    "chat_history_limit": history_limit
                }
                _save_and_apply_config(config_data, selected_key, llm_model, llm_key, llm_url, defaults, only_chat_settings=True)

        extra_params['chat_history_limit'] = history_limit
        # 兼容性保留
        extra_params['system_prompt'] = defaults.get("system_prompt", "")

    return llm_provider, llm_url, llm_model, llm_key, extra_params


def _render_remote_model_selector(url: str, key: str, saved_model: str, prefix: str) -> str:
    """辅助函数：渲染远程模型选择器 (v2.9.5 自动加载优化)"""
    from src.utils.model_utils import fetch_remote_models
    
    cache_key = f"models_{prefix}_{url}_{key}"
    available_models = st.session_state.get(cache_key, [])
    
    # --- 核心改进：自动加载逻辑 (v2.9.5) ---
    # 如果有 URL (且非本地 prefix 时有 Key)，且缓存为空，则尝试自动加载一次
    # 为了避免无限重试，我们记录一个自动加载尝试标记
    auto_load_flag = f"auto_load_{prefix}_{hash(url + key)}"
    
    if url and not available_models and auto_load_flag not in st.session_state:
        # 只有 OpenAI 类的需要 Key，其它的（如 Ollama 在其它地方处理）视情况而定
        # 这里统一逻辑：有 URL 且缓存空，尝试拉取
        can_try = True
        if prefix in ["openai", "other"] and not key:
            can_try = False
            
        if can_try:
            with st.spinner("🔄 自动同步模型列表..."):
                models, err = fetch_remote_models(url, key)
                if models:
                    available_models = models
                    st.session_state[cache_key] = models
                    # 标记已尝试过，避免失败时反复触发
                    st.session_state[auto_load_flag] = True
                else:
                    # 即使失败也标记，防止阻塞 UI
                    st.session_state[auto_load_flag] = False

    # 刷新按钮 (保留手动刷新)
    col_select, col_refresh = st.columns([4, 1])
    
    with col_refresh:
        if st.button("🔄", key=f"refresh_{prefix}", help="刷新模型列表"):
            with st.spinner("🔄"):
                models, err = fetch_remote_models(url, key)
                if models:
                    available_models = models
                    st.session_state[cache_key] = models
                    st.toast(f"✅ 已加载 {len(models)} 个模型")
                    st.rerun()
                else:
                    st.warning(f"加载失败: {err}")

    with col_select:
        if available_models:
            if saved_model and saved_model not in available_models:
                available_models.insert(0, saved_model)
            
            return st.selectbox(
                "选择模型", 
                available_models, 
                index=available_models.index(saved_model) if saved_model in available_models else 0,
                key=f"config_{prefix}_model_select",
                label_visibility="collapsed"
            )
        else:
            return st.text_input("模型名称", saved_model, placeholder="例如: gpt-3.5-turbo", key=f"config_{prefix}_model_input", label_visibility="collapsed")


def _save_and_apply_config(config_data: dict, provider: str, model: str, key: str, url: str, defaults: dict, only_chat_settings: bool = False, **kwargs):
    """辅助函数：保存并应用配置"""
    existing_config = load_config("rag_config")
    existing_config.update(config_data)
    
    # 确保 system_prompt 被包含
    if "system_prompt" not in config_data:
        # 如果当前保存的不是聊天设置，我们需要从现有配置或 defaults 中获取 system_prompt，以防重置为空
        system_prompt = existing_config.get("system_prompt") or defaults.get("system_prompt", "")
    else:
        system_prompt = config_data["system_prompt"]

    # 同样处理 chat_history_limit (虽然它不直接影响 set_global_llm_model，但为了完整性)
    
    if save_config(existing_config, "rag_config"):
        # 如果只是保存对话设置，我们可能不需要重新初始化整个 LLM，
        # 但为了让 System Prompt 生效，通常需要重新初始化 LLM (LlamaIndex 的 LLM 对象通常是不可变的配置)
        
        # 如果是从 provider 按钮调用的，参数齐全。
        # 如果是从 chat settings 调用的，我们需要从 defaults 补全参数
        if only_chat_settings:
            # 尝试从 defaults 获取当前活动的 LLM 配置
            # 注意：这里的 provider 参数可能只是 selected_key，不一定是当前全局生效的 provider
            # 这是一个潜在问题：用户在左侧选了 Ollama，改了 System Prompt，点击保存，但当前全局生效的可能是 OpenAI。
            # 但通常用户改配置时，意图是让当前视图的配置生效。
            # 实际上，`set_global_llm_model` 会切换全局 LLM。
            # 所以，保存 Chat Settings 同时也意味着应用了当前左侧面板选中的 Provider 配置。
            # 为了避免混淆，我们可以只更新 System Prompt 而不切换 Provider？
            # 不，System Prompt 是 LLM 的属性。
            # 简单策略：应用当前面板的所有配置。
            
            # 补全缺失参数 (model, key, url)
            # 注意：config_data 里只有 chat settings，所以我们需要从 defaults 获取 provider settings
            # 但是 defaults 是旧的。我们需要从 UI 控件获取？
            # render_llm_config 里的 llm_model 等变量是当前渲染的值。
            # 我们在调用 _save_and_apply_config 时已经传入了这些值 (model, key, url)。
            pass
            
        if set_global_llm_model(provider, model, key, url, system_prompt=system_prompt, **kwargs):
            st.success(f"✅ 配置已更新并生效 (System Prompt: {'已设置' if system_prompt else '未设置'})")
            if not only_chat_settings:
                st.session_state.selected_model = model
        else:
            st.warning("⚠️ 配置已保存，但热更新失败")
            
        defaults.update(config_data)
        if only_chat_settings:
             st.rerun()
    else:
        st.error("❌ 保存失败")


def render_embedding_config(defaults: dict) -> Tuple[str, str, str, str]:
    """
    渲染 Embedding 配置表单 (优化版)
    """
    with st.container(border=True):
        st.markdown("##### 🧬 向量模型 (Embedding)")
        
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
