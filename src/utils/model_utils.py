"""
模型工具函数
提取自 apppro.py
"""

import os
import json
import requests
import streamlit as st


def check_ollama_status(url):
    """
    检查 Ollama 服务状态
    
    Args:
        url: Ollama API URL
        
    Returns:
        bool: 服务是否可用
    """
    try:
        # 清理代理设置（如果可用）
        try:
            from utils.model_manager import clean_proxy
            clean_proxy()
        except:
            pass
        
        clean = url.replace("/api/chat", "").replace("/v1", "").rstrip('/')
        # 使用 Ollama 的健康检查端点
        response = requests.get(f"{clean}/api/tags", timeout=2.0)
        return response.status_code == 200
    except:
        return False


def fetch_remote_models(base_url, api_key):
    """
    获取远程模型列表 (OpenAI 兼容接口)
    
    Args:
        base_url: API Base URL
        api_key: API Key
        
    Returns:
        tuple: (模型列表, 错误信息)
    """
    if not base_url:
        return None, "请填写 Base URL"
    
    # 自动识别 Ollama 地址
    if "localhost:11434" in base_url or "127.0.0.1:11434" in base_url:
        return fetch_ollama_models(base_url)
    
    clean_url = base_url.rstrip('/')
    endpoints = [f"{clean_url}/models", f"{clean_url}/v1/models"]
    headers = {"Authorization": f"Bearer {api_key}" if api_key else "Bearer EMPTY"}
    
    for url in endpoints:
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data and isinstance(data['data'], list):
                    return [item['id'] for item in data['data']], None
        except Exception as e:
            continue # 尝试下一个 endpoint
    
    return None, "未找到模型列表或路径错误"


def fetch_ollama_models(url):
    """
    获取 Ollama 模型列表
    
    Args:
        url: Ollama API URL
        
    Returns:
        tuple: (模型列表, 错误信息)
    """
    try:
        clean = url.replace("/api/chat", "").replace("/v1", "").rstrip('/')
        response = requests.get(f"{clean}/api/tags", timeout=3.0)
        if response.status_code == 200:
            data = response.json()
            models = []
            if "models" in data:
                for m in data["models"]:
                    models.append(m.get("name") or m.get("model", ""))
            return [m for m in models if m], None
    except Exception as e:
        return None, f"Ollama 连接失败: {e}"
    return None, "未找到 Ollama 模型"


def check_hf_model_exists(model_name):
    """
    检查 HuggingFace 模型是否已下载到本地
    
    Args:
        model_name: 模型名称
        
    Returns:
        bool: 模型是否存在
    """
    cache_dir = "./hf_cache"
    
    # 方式1: 直接目录格式 (BAAI--bge-large-zh-v1.5)
    model_dir1 = os.path.join(cache_dir, model_name.replace('/', '--'))
    if os.path.exists(os.path.join(model_dir1, "config.json")):
        return True
    
    # 方式2: HF Hub 缓存格式 (models--BAAI--bge-small-zh-v1.5)
    model_dir2 = os.path.join(cache_dir, f"models--{model_name.replace('/', '--')}")
    if os.path.exists(model_dir2):
        return True
    
    return False


def get_kb_embedding_dim(db_path):
    """
    检测知识库的向量维度（带缓存）
    
    Args:
        db_path: 知识库路径
        
    Returns:
        int or None: 向量维度
    """
    # 1. 尝试从缓存获取
    if 'kb_dimensions' not in st.session_state:
        st.session_state.kb_dimensions = {}
    
    # 使用文件修改时间作为缓存键的一部分
    kb_cache_key = f"{os.path.basename(db_path)}_dim"
    try:
        kb_info_file = os.path.join(db_path, ".kb_info.json")
        if os.path.exists(kb_info_file):
            mtime = os.path.getmtime(kb_info_file)
            kb_cache_key = f"{os.path.basename(db_path)}_dim_{mtime}"
            
            # 清理旧缓存
            keys_to_remove = [
                k for k in st.session_state.kb_dimensions 
                if k.startswith(f"{os.path.basename(db_path)}_dim") and k != kb_cache_key
            ]
            for k in keys_to_remove:
                del st.session_state.kb_dimensions[k]
    except:
        pass

    if kb_cache_key in st.session_state.kb_dimensions:
        return st.session_state.kb_dimensions[kb_cache_key]

    print(f"🔍 开始检测维度: {db_path}")
    
    try:
        # 方法0: 优先检查保存的 KB 信息 (.kb_info.json)
        # 这是最准确的来源，因为它是在构建时写入的
        kb_info_file = os.path.join(db_path, ".kb_info.json")
        if os.path.exists(kb_info_file):
            try:
                with open(kb_info_file, 'r') as f:
                    kb_info = json.load(f)
                    
                    # 优先获取明确记录的维度
                    if 'embedding_dim' in kb_info and isinstance(kb_info['embedding_dim'], int) and kb_info['embedding_dim'] > 0:
                        dim = kb_info['embedding_dim']
                        model = kb_info.get('embedding_model', 'unknown')
                        print(f"✅ 从 KB 信息读取维度: {dim}D (模型: {model})")
                        st.session_state.kb_dimensions[kb_cache_key] = dim
                        return dim
                    
                    # 如果没有维度但有模型名称，尝试推断
                    if 'embedding_model' in kb_info:
                        model_name = kb_info['embedding_model']
                        inferred_dim = get_model_dimension(model_name)
                        print(f"⚠️ 未找到明确维度，根据模型名推断: {model_name} -> {inferred_dim}D")
                        st.session_state.kb_dimensions[kb_cache_key] = inferred_dim
                        return inferred_dim
                        
            except Exception as e:
                print(f"⚠️ 读取 KB 信息失败: {e}")
        
        # 方法1: 直接从 ChromaDB 读取维度
        import chromadb
        try:
            client = chromadb.PersistentClient(path=db_path)
            collections = client.list_collections()
            print(f"📦 找到 {len(collections)} 个集合")
            
            if collections:
                col = client.get_collection(collections[0].name)
                data = col.get(limit=1, include=['embeddings'])
                if data['embeddings'] and len(data['embeddings']) > 0:
                    dim = len(data['embeddings'][0])
                    print(f"✅ ChromaDB 检测到维度: {dim}D")
                    st.session_state.kb_dimensions[kb_cache_key] = dim
                    return dim
        except Exception as e:
            print(f"⚠️ ChromaDB 检测失败: {e}")
        
        # 方法2: 检查 vector_store.json
        vector_store_path = os.path.join(db_path, "vector_store.json")
        if os.path.exists(vector_store_path):
            print(f"📄 检查 vector_store.json...")
            with open(vector_store_path, 'r') as f:
                data = json.load(f)
                if 'embedding_dict' in data and data['embedding_dict']:
                    first_embedding = next(iter(data['embedding_dict'].values()))
                    if isinstance(first_embedding, list):
                        dim = len(first_embedding)
                        print(f"✅ JSON 检测到维度: {dim}D")
                        st.session_state.kb_dimensions[kb_cache_key] = dim
                        return dim
        else:
            print(f"❌ vector_store.json 不存在")
        
    except Exception as e:
        print(f"❌ 维度检测异常: {e}")
    
    print(f"❌ 无法检测维度")
    return None


def auto_switch_model(kb_dim, current_model):
    """
    根据知识库维度自动切换模型
    
    Args:
        kb_dim: 知识库维度
        current_model: 当前模型
        
    Returns:
        str: 推荐的模型名称
    """
    model_map = {
        512: "sentence-transformers/all-MiniLM-L6-v2",
        768: "BAAI/bge-large-zh-v1.5",
        1024: "BAAI/bge-large-zh-v1.5"
    }
    
    if kb_dim in model_map:
        return model_map[kb_dim]
    
    # 默认返回当前模型
    return current_model


def get_model_dimension(model_name):
    """
    获取模型的向量维度
    
    Args:
        model_name: 模型名称
        
    Returns:
        int: 向量维度
    """
    dimension_map = {
        "sentence-transformers/all-MiniLM-L6-v2": 512,
        "BAAI/bge-large-zh-v1.5": 1024,
        "BAAI/bge-large-zh-v1.5": 1024,
        "BAAI/bge-m3": 1024,
        "text-embedding-ada-002": 1536,
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072
    }
    
    return dimension_map.get(model_name, 768)  # 默认768
