"""
配置表单组件
Stage 3.2.2 - 中风险重构
提取自 apppro.py
使用统一配置组件
"""

import streamlit as st
from typing import Tuple
from .model_selectors import (
    render_ollama_model_selector,
    render_hf_embedding_selector
)
from src.services.unified_config_service import save_config, load_config
from src.utils.model_manager import set_global_llm_model


def render_llm_config(defaults: dict) -> Tuple[str, str, str, str, dict]:
    """
    渲染 LLM 配置表单 (v3.2 顶部导航 + 修复数据覆盖 Bug)
    """
    # 1. 准备供应商数据
    BASE_PROVIDERS = {
        "Ollama": "🦙 Ollama",
        "OpenAI": "☁️ OpenAI",
        "OpenAI-Compatible": "🔌 OpenAI-Other",
        "Azure OpenAI": "🟦 Azure",
        "Anthropic": "🧠 Anthropic",
        "Moonshot": "🌙 Moonshot",
        "Gemini": "💎 Gemini",
        "Groq": "⚡ Groq"
    }
    
    custom_providers = defaults.get("custom_llm_providers", {})
    PROVIDERS = BASE_PROVIDERS.copy()
    for cp_id, cp_info in custom_providers.items():
        PROVIDERS[cp_id] = f"🎨 {cp_info.get('name', cp_id)}"
    
    nav_keys = list(PROVIDERS.keys()) + ["ADD_CUSTOM"]
    
    # --- 核心修复 1: 使用顶部单选框模拟标签页，确保能获取选中的 Key ---
    saved_provider = defaults.get("llm_provider", "Ollama")
    if saved_provider not in nav_keys: saved_provider = "Ollama"
    
    # 在顶部显示水平选择器
    selected_key = st.radio(
        "厂商切换",
        options=nav_keys,
        format_func=lambda x: PROVIDERS.get(x, "➕ 新增自定义"),
        index=nav_keys.index(saved_provider),
        horizontal=True,
        key="top_provider_selector"
    )
    
    # 初始返回变量 (核心修复 2: 确保只从选中的厂商提取数据)
    llm_provider = selected_key
    llm_url = ""
    llm_model = ""
    llm_key = ""
    extra_params = {}

    # --- 2. 根据选中的 Key 渲染对应的配置卡片 ---
    with st.container(border=True):
        if selected_key == "ADD_CUSTOM":
            c1, c2 = st.columns(2)
            with c1:
                custom_name = st.text_input("厂商名称", placeholder="MyAI", key="new_custom_name")
                custom_url = st.text_input("Base URL", placeholder="https://api.domain.com/v1", key="new_custom_url")
            with c2:
                custom_key = st.text_input("API Key", type="password", key="new_custom_key")
                custom_model = _render_remote_model_selector(custom_url, custom_key, "", "custom_new")
            
            if st.button("✨ 立即创建并保存", type="primary", use_container_width=True):
                if custom_name and custom_url:
                    cp_id = f"custom_{hash(custom_name + custom_url) % 10000}"
                    new_cp_info = {"name": custom_name, "url": custom_url, "key": custom_key, "model": custom_model}
                    existing_custom = defaults.get("custom_llm_providers", {})
                    existing_custom[cp_id] = new_cp_info
                    config_data = {
                        "custom_llm_providers": existing_custom,
                        "llm_provider": cp_id,
                        "llm_provider_label": f"🎨 {custom_name}",
                        f"llm_url_{cp_id}": custom_url,
                        f"llm_key_{cp_id}": custom_key,
                        f"llm_model_{cp_id}": custom_model
                    }
                    _save_and_apply_config(config_data, cp_id, custom_model, custom_key, custom_url, defaults)
                    st.rerun()
                else:
                    st.error("请填写完整信息")

        elif selected_key in custom_providers:
            # 渲染已有的自定义服务商 (严格锚定数据)
            cp = custom_providers[selected_key]
            col1, col2 = st.columns([2, 1])
            with col1:
                llm_url = st.text_input("Base URL", defaults.get(f"llm_url_{selected_key}") or cp.get('url', ""), key=f"config_{selected_key}_url")
            with col2:
                llm_key = st.text_input("API Key", defaults.get(f"llm_key_{selected_key}") or cp.get('key', ""), type="password", key=f"config_{selected_key}_key")
            
            saved_model = defaults.get(f"llm_model_{selected_key}") or cp.get('model', "")
            llm_model = _render_remote_model_selector(llm_url, llm_key, saved_model, selected_key)
            
            b1, b2 = st.columns([4, 1])
            with b1:
                if st.button(f"💾 保存 {cp['name']} 修改", type="primary", use_container_width=True, key=f"save_{selected_key}"):
                    cp.update({"url": llm_url, "key": llm_key, "model": llm_model})
                    custom_providers[selected_key] = cp
                    _save_and_apply_config({"custom_llm_providers": custom_providers, "llm_provider": selected_key, f"llm_url_{selected_key}": llm_url, f"llm_key_{selected_key}": llm_key, f"llm_model_{selected_key}": llm_model}, selected_key, llm_model, llm_key, llm_url, defaults)
            with b2:
                if st.button("🗑️ 删除", key=f"del_{selected_key}", use_container_width=True):
                    del custom_providers[selected_key]
                    _save_and_apply_config({"custom_llm_providers": custom_providers}, "Ollama", "gpt-oss:20b", "", "http://localhost:11434", defaults)
                    st.rerun()

        else:
            # 内置服务商逻辑 (严格读取 defaults)
            
            if selected_key == "Ollama":
                # URL, 刷新, 状态 一行化
                c1, c2, c3 = st.columns([3, 0.8, 1.2])
                with c1:
                    cur_ollama_url = st.text_input("Ollama URL", defaults.get("llm_url_ollama") or "http://localhost:11434", key="config_ollama_url", label_visibility="collapsed")
                
                from src.utils.model_utils import check_ollama_status, fetch_remote_models
                ollama_ok = check_ollama_status(cur_ollama_url)
                
                with c2:
                    if st.button("🔄", key="refresh_ollama_btn", help="刷新 Ollama 模型列表"):
                        if ollama_ok:
                            from src.ui.model_selectors import _fetch_ollama_models
                            models = _fetch_ollama_models(cur_ollama_url)
                            if models:
                                st.session_state.ollama_models = models
                                st.toast(f"✅ 已加载 {len(models)} 个模型")
                                st.rerun()
                        else: st.warning("未运行")
                
                with c3:
                    st.caption("✅ 已连接" if ollama_ok else "⚠️ 未运行")
                
                saved_ollama_model = defaults.get("llm_model_ollama", "gpt-oss:20b")
                sel_ollama_model, _ = render_ollama_model_selector(cur_ollama_url, saved_ollama_model, ollama_ok)
                if st.button("💾 保存 Ollama 配置", type="primary", use_container_width=True, key="save_ollama"):
                    _save_and_apply_config({"llm_provider": "Ollama", "llm_url_ollama": cur_ollama_url, "llm_model_ollama": sel_ollama_model, "llm_provider_label": PROVIDERS["Ollama"]}, "Ollama", sel_ollama_model, "", cur_ollama_url, defaults)
                
                # 赋值给返回变量
                llm_url, llm_model, llm_key = cur_ollama_url, sel_ollama_model, ""

            elif selected_key == "OpenAI":
                # URL 与 刷新 一行化
                c1, c2 = st.columns([4, 1])
                with c1: cur_openai_url = st.text_input("Base URL", defaults.get("llm_url_openai") or "https://api.openai.com/v1", key="config_openai_url", help="API 基础地址")
                cur_openai_key = st.text_input("API Key", defaults.get("llm_key") or "", type="password", key="config_openai_key")
                
                with c2:
                    st.write("") # 间距对齐
                    if st.button("🔄", key="refresh_openai_btn", help="刷新 OpenAI 模型列表"):
                        from src.utils.model_utils import fetch_remote_models
                        models, err = fetch_remote_models(cur_openai_url, cur_openai_key)
                        if models:
                            cache_key = f"models_openai_{cur_openai_url}_{cur_openai_key}"
                            st.session_state[cache_key] = models
                            st.toast(f"✅ 已加载 {len(models)} 个模型")
                            st.rerun()
                        else: st.error(f"失败: {err}")

                saved_openai_model = defaults.get("llm_model_openai", "gpt-3.5-turbo")
                sel_openai_model = _render_remote_model_selector(cur_openai_url, cur_openai_key, saved_openai_model, "openai")
                if st.button("💾 保存 OpenAI 配置", type="primary", use_container_width=True, key="save_openai"):
                    _save_and_apply_config({"llm_provider": "OpenAI", "llm_url_openai": cur_openai_url, "llm_key": cur_openai_key, "llm_model_openai": sel_openai_model, "llm_provider_label": PROVIDERS["OpenAI"]}, "OpenAI", sel_openai_model, cur_openai_key, cur_openai_url, defaults)
                
                # 赋值给返回变量
                llm_url, llm_model, llm_key = cur_openai_url, sel_openai_model, cur_openai_key

            elif selected_key == "OpenAI-Compatible":
                # URL 与 刷新 一行化
                c1, c2 = st.columns([4, 1])
                with c1: cur_other_url = st.text_input("Base URL", defaults.get("llm_url_other") or "https://api.deepseek.com/v1", key="config_other_url")
                cur_other_key = st.text_input("API Key", defaults.get("llm_key_other") or "", type="password", key="config_other_key")
                
                with c2:
                    st.write("") # 间距对齐
                    if st.button("🔄", key="refresh_other_btn", help="刷新模型列表"):
                        from src.utils.model_utils import fetch_remote_models
                        models, err = fetch_remote_models(cur_other_url, cur_other_key)
                        if models:
                            cache_key = f"models_other_{cur_other_url}_{cur_other_key}"
                            st.session_state[cache_key] = models
                            st.toast(f"✅ 已加载 {len(models)} 个模型")
                            st.rerun()
                        else: st.error(f"失败: {err}")

                saved_other_model = defaults.get("llm_model_other", "")
                sel_other_model = _render_remote_model_selector(cur_other_url, cur_other_key, saved_other_model, "other")
                if st.button("💾 保存自定义配置", type="primary", use_container_width=True, key="save_other"):
                    _save_and_apply_config({"llm_provider": "OpenAI-Compatible", "llm_url_other": cur_other_url, "llm_key_other": cur_other_key, "llm_model_other": sel_other_model, "llm_provider_label": PROVIDERS["OpenAI-Compatible"]}, "OpenAI-Compatible", sel_other_model, cur_other_key, cur_other_url, defaults)
                
                llm_url, llm_model, llm_key = cur_other_url, sel_other_model, cur_other_key

            elif selected_key == "Azure OpenAI":
                c1, c2 = st.columns(2)
                with c1:
                    cur_az_url = st.text_input("Azure Endpoint", defaults.get("azure_endpoint", ""), key="config_azure_endpoint")
                    cur_az_model = st.text_input("Deployment Name", defaults.get("azure_deployment", ""), key="config_azure_deployment")
                with c2:
                    cur_az_key = st.text_input("API Key", defaults.get("azure_key", ""), type="password", key="config_azure_key")
                    cur_az_ver = st.text_input("API Version", defaults.get("azure_api_version", "2023-05-15"), key="config_azure_api_version")
                if st.button("💾 保存 Azure 配置", type="primary", use_container_width=True, key="save_azure"):
                    _save_and_apply_config({"llm_provider": "Azure OpenAI", "azure_endpoint": cur_az_url, "azure_key": cur_az_key, "azure_deployment": cur_az_model, "azure_api_version": cur_az_ver}, "Azure OpenAI", cur_az_model, cur_az_key, cur_az_url, defaults, api_version=cur_az_ver)
                
                llm_url, llm_model, llm_key = cur_az_url, cur_az_model, cur_az_key

            elif selected_key == "Anthropic":
                cur_ant_key = st.text_input("API Key", defaults.get("anthropic_key", ""), type="password", key="config_anthropic_key")
                cur_ant_model = st.selectbox("模型", ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"], key="config_anthropic_model_sel")
                if st.button("💾 保存 Anthropic 配置", type="primary", use_container_width=True, key="save_anthropic"):
                    _save_and_apply_config({"anthropic_key": cur_ant_key, "config_anthropic_model": cur_ant_model}, "Anthropic", cur_ant_model, cur_ant_key, "", defaults)
                
                llm_url, llm_model, llm_key = "", cur_ant_model, cur_ant_key

            elif selected_key == "Moonshot":
                ms_url = "https://api.moonshot.cn/v1"
                st.text_input("Base URL", ms_url, disabled=True, key="config_moonshot_url")
                cur_ms_key = st.text_input("API Key", defaults.get("moonshot_key", ""), type="password", key="config_moonshot_key")
                cur_ms_model = st.selectbox("模型", ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"], key="config_moonshot_model_sel")
                if st.button("💾 保存 Moonshot 配置", type="primary", use_container_width=True, key="save_moonshot"):
                    _save_and_apply_config({"moonshot_key": cur_ms_key, "config_moonshot_model": cur_ms_model, "llm_url": ms_url}, "Moonshot", cur_ms_model, cur_ms_key, ms_url, defaults)
                
                llm_url, llm_model, llm_key = ms_url, cur_ms_model, cur_ms_key
            
            elif selected_key == "Gemini":
                cur_gem_key = st.text_input("API Key", defaults.get("gemini_key", ""), type="password", key="config_gemini_key")
                cur_gem_model = st.selectbox("模型", ["gemini-pro", "gemini-pro-vision"], key="config_gemini_model_sel")
                if st.button("💾 保存 Gemini 配置", type="primary", use_container_width=True, key="save_gemini"):
                    _save_and_apply_config({"gemini_key": cur_gem_key, "config_gemini_model": cur_gem_model}, "Gemini", cur_gem_model, cur_gem_key, "", defaults)
                
                llm_url, llm_model, llm_key = "", cur_gem_model, cur_gem_key
            
            elif selected_key == "Groq":
                groq_url = "https://api.groq.com/openai/v1"
                st.text_input("Base URL", groq_url, disabled=True, key="config_groq_url")
                cur_groq_key = st.text_input("API Key", defaults.get("groq_key", ""), type="password", key="config_groq_key")
                cur_groq_model = st.selectbox("模型", ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"], key="config_groq_model_sel")
                if st.button("💾 保存 Groq 配置", type="primary", use_container_width=True, key="save_groq"):
                    _save_and_apply_config({"groq_key": cur_groq_key, "config_groq_model": cur_groq_model, "llm_url": groq_url}, "Groq", cur_groq_model, cur_groq_key, groq_url, defaults)
                
                llm_url, llm_model, llm_key = groq_url, cur_groq_model, cur_groq_key

    # 3. 底部通用设置 (已移至对话界面，此处仅保留参数占位)
    extra_params['chat_history_limit'] = defaults.get("chat_history_limit", 10)
    extra_params['system_prompt'] = defaults.get("system_prompt", "")

    return llm_provider, llm_url, llm_model, llm_key, extra_params


def _render_remote_model_selector(url: str, key: str, saved_model: str, prefix: str) -> str:
    """辅助函数：渲染远程模型选择器 (v2.9.5 自动加载优化)"""
    from src.utils.model_utils import fetch_remote_models
    
    cache_key = f"models_{prefix}_{url}_{key}"
    available_models = st.session_state.get(cache_key, [])
    
    # --- 核心改进：自动加载逻辑 (v2.9.5) ---
    auto_load_flag = f"auto_load_{prefix}_{hash(url + key)}"
    
    if url and not available_models and auto_load_flag not in st.session_state:
        can_try = True
        if prefix in ["openai", "other"] and not key:
            can_try = False
            
        if can_try:
            with st.spinner("🔄"):
                models, err = fetch_remote_models(url, key)
                if models:
                    available_models = models
                    st.session_state[cache_key] = models
                    st.session_state[auto_load_flag] = True
                else:
                    st.session_state[auto_load_flag] = False

    # 模型选择
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
                c1, c2 = st.columns(2)
                with c1: embed_model = st.text_input("模型名", defaults.get("embed_model_openai", "text-embedding-3-small"), key="embed_openai_model")
                with c2: embed_url = st.text_input("Base URL", defaults.get("embed_url_openai", "https://api.openai.com/v1"), key="embed_openai_url")
                embed_key = st.text_input("API Key", defaults.get("embed_key", ""), type="password", key="embed_openai_key")
            else:  # Ollama
                c1, c2 = st.columns(2)
                with c1: embed_model = st.text_input("模型名", defaults.get("embed_model_ollama", "nomic-embed-text"), key="embed_ollama_model")
                with c2: embed_url = st.text_input("URL", defaults.get("embed_url_ollama", "http://localhost:11434"), key="embed_ollama_url")
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
    
    # 增加间距，防止视觉拥挤
    st.write("")
    
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
