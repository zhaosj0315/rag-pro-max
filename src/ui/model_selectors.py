"""
模型选择器组件
Stage 3.2.1 - 中风险重构
提取自 apppro.py
"""

import streamlit as st
import ollama
from typing import List, Optional, Tuple


def render_ollama_model_selector(
    llm_url: str,
    saved_model: str,
    ollama_ok: bool
) -> Tuple[str, bool]:
    """
    渲染 Ollama 模型选择器
    
    Args:
        llm_url: Ollama API URL
        saved_model: 保存的默认模型
        ollama_ok: Ollama 连接状态
        
    Returns:
        Tuple[str, bool]: (选中的模型, 是否需要保存为默认)
    """
    save_as_default = False
    
    # 刷新按钮
    col_refresh = st.columns([3, 1])[1]
    with col_refresh:
        if st.button("🔄", key="refresh_ollama_models", help="刷新模型列表", use_container_width=True):
            if ollama_ok:
                models = _fetch_ollama_models(llm_url)
                if models:
                    st.session_state.ollama_models = models
                    st.toast(f"✅ 找到 {len(models)} 个模型")
                    st.rerun()
                else:
                    st.warning("未找到模型")
                    st.session_state.ollama_models = []
            else:
                st.warning("请先启动 Ollama")
    
    # 自动加载模型列表（首次）
    if ollama_ok and ("ollama_models" not in st.session_state or not st.session_state.ollama_models):
        models = _fetch_ollama_models(llm_url)
        st.session_state.ollama_models = models if models else []
    
    if not ollama_ok:
        st.session_state.ollama_models = []
    
    # 模型选择/输入
    if st.session_state.ollama_models:
        # 如果有模型列表，添加一个"手动输入"选项
        options = st.session_state.ollama_models + ["✏️ 手动输入..."]
        idx = st.session_state.ollama_models.index(saved_model) if saved_model in st.session_state.ollama_models else 0
        
        col1, col2 = st.columns([4, 1])
        with col1:
            selected = st.selectbox("选择/输入模型", options, index=idx, label_visibility="collapsed")
        with col2:
            if st.button("⭐ 默认", key="set_default_llm", use_container_width=True):
                if selected != "✏️ 手动输入...":
                    save_as_default = True
                else:
                    st.warning("请先输入模型名")
        
        if selected == "✏️ 手动输入...":
            llm_model = st.text_input("模型名", saved_model, label_visibility="collapsed", key="llm_manual_1")
        else:
            llm_model = selected
    else:
        llm_model = st.text_input("输入模型名", saved_model, key="llm_direct_1")
    
    return llm_model, save_as_default


def render_openai_model_selector(
    llm_url: str,
    llm_key: str,
    saved_model: str
) -> str:
    """
    渲染 OpenAI 兼容模型选择器
    
    Args:
        llm_url: API Base URL
        llm_key: API Key
        saved_model: 保存的默认模型
        
    Returns:
        str: 选中的模型
    """
    from src.utils.model_utils import fetch_remote_models
    
    if st.button("🔄 刷新列表", use_container_width=True):
        with st.spinner("正在连接模型列表..."):
            mods, err = fetch_remote_models(llm_url, llm_key)
            if mods:
                st.session_state.model_list = mods
            else:
                st.error(err)
    
    if st.session_state.model_list:
        idx = st.session_state.model_list.index(saved_model) if saved_model in st.session_state.model_list else 0
        llm_model = st.selectbox("选择模型", st.session_state.model_list, index=idx)
    else:
        llm_model = st.text_input("输入模型名", saved_model, key="llm_openai_1")
    
    return llm_model


def render_hf_embedding_selector(
    saved_model: str,
    preset_models: Optional[List[str]] = None,
    model_descriptions: Optional[dict] = None
) -> str:
    """
    渲染 HuggingFace 嵌入模型选择器
    
    Args:
        saved_model: 保存的默认模型
        preset_models: 预设模型列表
        model_descriptions: 模型描述字典
        
    Returns:
        str: 选中的模型
    """
    from src.utils.model_utils import check_hf_model_exists
    
    # 默认预设模型
    if preset_models is None:
        preset_models = [
            "BAAI/bge-small-zh-v1.5",
            "BAAI/bge-large-zh-v1.5",
            "BAAI/bge-m3",
            "BAAI/bge-base-zh-v1.5",
            "moka-ai/m3e-base",
            "shibing624/text2vec-base-chinese",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            "自定义模型..."
        ]
    
    if model_descriptions is None:
        model_descriptions = {
            "BAAI/bge-small-zh-v1.5": "🚀 小型快速版 | 90MB | 适合实时应用、资源受限场景",
            "BAAI/bge-large-zh-v1.5": "🎯 中文最强版 | 1.3GB | 最高准确度，推荐用于精准检索",
            "BAAI/bge-m3": "🌍 多语言最强 | 2GB | 支持100+语言，跨语言检索最佳",
            "BAAI/bge-base-zh-v1.5": "⚖️ 平衡版本 | 400MB | 速度与准确度的完美平衡",
            "moka-ai/m3e-base": "🔤 M3E中文优化 | 400MB | 中文语义理解优化",
            "shibing624/text2vec-base-chinese": "📝 Text2Vec中文 | 400MB | 中文文本向量化专家",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": "💡 轻量多语言 | 400MB | 资源受限时的多语言方案"
        }
    
    # 确定默认索引
    try:
        default_idx = preset_models.index(saved_model) if saved_model in preset_models else 0
    except:
        default_idx = 0
    
    col1, col2 = st.columns([5, 1])
    with col1:
        selected = st.selectbox(
            "HF 模型",
            options=preset_models,
            index=default_idx,
            help=model_descriptions.get(preset_models[default_idx], ""),
            label_visibility="collapsed"
        )
    
    # 如果选择自定义，显示输入框
    if selected == "自定义模型...":
        embed_model = st.text_input(
            "输入模型名称",
            placeholder="例如: sentence-transformers/all-MiniLM-L6-v2",
            help="输入任意 HuggingFace 模型 ID"
        )
        if not embed_model:
            embed_model = "BAAI/bge-small-zh-v1.5"  # 默认值
    else:
        embed_model = selected
    
    # 检查模型是否存在并显示状态
    model_exists = check_hf_model_exists(embed_model)
    
    with col2:
        button_label = "✅ ⭐" if model_exists else "⭐"
        if st.button(button_label, key="set_default_embed", use_container_width=True, help="设为默认模型"):
            # 返回信号，让调用者保存配置
            st.session_state.save_embed_model = embed_model
    
    # 显示模型状态
    if not model_exists:
        st.warning("⚠️ 模型未下载")
        if st.button("📥 下载模型", key="download_hf_model", type="primary", use_container_width=True):
            _download_hf_model(embed_model)
    else:
        st.success("✅ 模型已就绪")
    
    return embed_model


def _fetch_ollama_models(llm_url: str) -> List[str]:
    """
    获取 Ollama 模型列表
    
    Args:
        llm_url: Ollama API URL
        
    Returns:
        List[str]: 模型列表
    """
    try:
        from src.utils.model_manager import clean_proxy
        clean_proxy()
        client = ollama.Client(host=llm_url)
        models_resp = client.list()
        
        models = []
        if hasattr(models_resp, 'models'):
            # 新版 ollama 返回 ListResponse 对象
            for m in models_resp.models:
                if hasattr(m, 'model'):
                    models.append(m.model)
                elif isinstance(m, str):
                    models.append(m)
        elif isinstance(models_resp, dict) and 'models' in models_resp:
            # 旧版返回字典
            for m in models_resp['models']:
                if isinstance(m, dict):
                    models.append(m.get('name') or m.get('model', ''))
                else:
                    models.append(str(m))
        
        return [m for m in models if m]
    except Exception as e:
        st.error(f"获取失败: {e}")
        return []


def _download_hf_model(model_name: str) -> None:
    """
    下载 HuggingFace 模型
    
    Args:
        model_name: 模型名称
    """
    import sys
    import subprocess
    
    with st.spinner(f"正在下载 {model_name}..."):
        try:
            download_script = f"""
import os
os.environ['HF_HUB_OFFLINE'] = '0'
os.environ['TRANSFORMERS_OFFLINE'] = '0'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="{model_name}",
    cache_dir="./hf_cache",
    local_dir="./hf_cache/{model_name.replace('/', '--')}",
    local_dir_use_symlinks=False
)
print("SUCCESS")
"""
            result = subprocess.run(
                [sys.executable, "-c", download_script],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0 and "SUCCESS" in result.stdout:
                st.success(f"✅ 下载完成: {model_name}")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"下载失败: {result.stderr}")
        except Exception as e:
            st.error(f"下载失败: {e}")
