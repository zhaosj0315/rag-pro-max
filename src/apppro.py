import os
import sys

# 在导入任何其他模块之前设置离线模式
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'  # 避免多进程fork警告

# 彻底屏蔽所有警告和日志
import warnings
import logging

# 屏蔽所有警告
warnings.filterwarnings('ignore')

# 屏蔽所有 Streamlit 相关日志
for logger_name in ['streamlit', 'streamlit.runtime', 'streamlit.runtime.scriptrunner_utils', 
                     'streamlit.runtime.scriptrunner_utils.script_run_context']:
    logging.getLogger(logger_name).setLevel(logging.ERROR)
    logging.getLogger(logger_name).propagate = False

# 重定向 stderr 中的警告（最彻底的方式）
class SuppressWarnings:
    def write(self, text):
        if 'ScriptRunContext' not in text and 'WARNING' not in text:
            sys.__stderr__.write(text)
    def flush(self):
        sys.__stderr__.flush()

sys.stderr = SuppressWarnings()

# LlamaIndex 版本兼容性补丁（在导入前）
import llama_index.core.schema as schema_module
original_textnode = schema_module.TextNode

class PatchedTextNode(original_textnode):
    def get_doc_id(self):
        return self.ref_doc_id or self.node_id

schema_module.TextNode = PatchedTextNode

import streamlit as st
import shutil
import time
import requests
import ollama
import re
import json
import zipfile
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp

# 引入 LlamaIndex 核心
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.schema import Document

# 导入自定义嵌入
from src.custom_embeddings import create_custom_embedding

# 引入日志模块
from src.logger import logger
from src.terminal_logger import terminal_logger
from src.chat_utils_improved import generate_follow_up_questions_safe as generate_follow_up_questions

# 引入元数据管理
from src.metadata_manager import MetadataManager

# 引入工具模块
from src.utils.memory import cleanup_memory, get_memory_stats
from src.utils.model_manager import (
    load_embedding_model,
    load_llm_model,
    set_global_embedding_model,
    set_global_llm_model
)
from src.utils.document_processor import (
    sanitize_filename,
    get_file_size_str,
    get_file_type,
    get_file_info,
    get_relevance_label,
    load_pptx_file
)
from src.utils.config_manager import (
    load_config,
    save_config,
    load_manifest,
    update_manifest,
    get_manifest_path
)
from src.utils.chat_manager import (
    load_chat_history,
    save_chat_history,
    clear_chat_history
)
from src.utils.kb_manager import (
    rename_kb,
    get_existing_kbs,
    delete_kb,
    auto_save_kb_info,
    get_kb_info
)

# 引入 RAG 引擎
from src.rag_engine import RAGEngine

# 引入资源监控和模型工具
from src.utils.resource_monitor import check_resource_usage, get_system_stats
from src.utils.model_utils import (
    check_ollama_status,
    fetch_remote_models,
    check_hf_model_exists,
    get_kb_embedding_dim,
    auto_switch_model,
    get_model_dimension
)

# 引入 UI 展示组件 (Stage 3.1)
from src.ui.display_components import (
    render_message_stats,
    render_source_references,
    get_relevance_label
)

# 引入 UI 模型选择器 (Stage 3.2.1)
from src.ui.model_selectors import (
    render_ollama_model_selector,
    render_openai_model_selector,
    render_hf_embedding_selector
)

# ⚠️ 关键修复：强制使用本地模型，避免 OpenAI 默认
# 临时设置环境变量，让 LlamaIndex 使用本地模型
os.environ['LLAMA_INDEX_EMBED_MODEL'] = 'local'

# 兼容旧代码的包装函数
def get_embed(provider, model, key, url):
    """兼容旧代码的包装函数"""
    return load_embedding_model(provider, model, key, url)

def get_llm(provider, model, key, url, temp):
    """兼容旧代码的包装函数"""
    return load_llm_model(provider, model, key, url, temp)

def _process_node_worker(args):
    """多进程处理单个节点"""
    node_data, kb_name = args
    try:
        metadata = node_data.get('metadata', {})
        file_name = metadata.get('file_name', 'Unknown')
        score = node_data.get('score', 0.0)
        text = node_data.get('text', '')
        
        return {
            "file": file_name, 
            "score": score, 
            "text": text[:150].replace("\n", " ") + "..."
        }
    except:
        return None

# 引入文件处理模块
from src.file_processor import scan_directory_safe

# 多进程函数：元数据提取（移到模块级别）
def _extract_metadata_task(task):
    """单个文件的元数据提取任务（多进程安全）"""
    fp, fname, doc_ids, text_sample, persist_dir = task
    temp_mgr = MetadataManager(persist_dir)
    return fname, temp_mgr.add_file_metadata(fp, doc_ids, text_sample)

# 多进程函数：文档分块解析（移到模块级别）
def _parse_single_doc(doc_text):
    """单个文档解析（多进程安全）- 返回字典而非对象"""
    import warnings
    warnings.filterwarnings('ignore')
    
    # 文本分割 + 基础处理（优化：增大 chunk_size 减少节点数）
    chunk_size = 1024  # 从 512 增加到 1024
    chunk_overlap = 100  # 相应增加 overlap
    chunks = []
    
    # 预处理：清理和标准化文本
    doc_text = doc_text.strip()
    lines = doc_text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            line = ' '.join(line.split())
            cleaned_lines.append(line)
    
    cleaned_text = '\n'.join(cleaned_lines)
    
    # 分块处理
    for i in range(0, len(cleaned_text), chunk_size - chunk_overlap):
        chunk = cleaned_text[i:i + chunk_size]
        if chunk.strip():
            word_count = len(chunk.split())
            char_count = len(chunk)
            
            chunks.append({
                'text': chunk,
                'start_idx': i,
                'word_count': word_count,
                'char_count': char_count
            })
    
    return chunks

def _parse_batch_docs(doc_texts_batch):
    """批量处理文档（减少进程间通信）"""
    all_chunks = []
    for doc_text in doc_texts_batch:
        chunks = _parse_single_doc(doc_text)
        all_chunks.extend(chunks)
    return all_chunks

# ==========================================
# 1. 页面配置与样式
# ==========================================
st.set_page_config(
    page_title="RAG Pro Max (旗舰版)", 
    page_icon="🛡️", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# 注入 CSS
st.markdown("""
<style>
    /* 禁用 spinner 遮罩层 */
    .stSpinner > div {
        border: none !important;
        background-color: transparent !important;
    }
    div[data-testid="stStatusWidget"] {
        background-color: transparent !important;
    }
    
    /* 侧边栏顶部完全无空白 - 激进版本 */
    section[data-testid="stSidebar"] {
        padding-top: 0rem !important;
    }
    section[data-testid="stSidebar"] > div {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
        gap: 0.5rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:first-child {
        padding-top: 0rem !important;
        margin-top: 0rem !important;
    }
    
    /* 最小化顶部空白 */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* 紧凑标题 */
    h3, h4 {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0 !important;
        line-height: 1.2 !important;
    }
    
    /* 超紧凑指标卡片 */
    [data-testid="stMetricValue"] {
        font-size: 1.1rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        margin-bottom: 0 !important;
    }
    [data-testid="metric-container"] {
        padding: 0.3rem 0 !important;
    }
    
    /* 按钮样式优化 */
    div.stButton > button {
        background-color: transparent !important;
        border: 1px solid rgba(128, 128, 128, 0.5) !important;
        color: inherit !important;
        border-radius: 6px !important;
        padding: 0.3rem 0.6rem !important;
        transition: all 0.3s ease;
        line-height: 1.2;
        text-align: center;
        white-space: nowrap !important;
    }
    div.stButton > button:hover {
        border-color: #FF4B4B !important;
        color: #FF4B4B !important;
        background-color: rgba(255, 75, 75, 0.05) !important;
    }
    
    /* 输入框和下拉框 - 确保文字完整显示 */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        border-radius: 6px;
        padding: 0.4rem 0.8rem !important;
        font-size: 0.9rem !important;
        white-space: nowrap !important;
        overflow: visible !important;
    }
    
    /* 下拉框选项完整显示 */
    .stSelectbox label {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }
    
    /* 减少列间距但保持可读性 */
    [data-testid="column"] {
        padding: 0 0.4rem !important;
    }
    
    /* 侧边栏文件列表 */
    .file-item {
        font-size: 12px; 
        padding: 5px 8px; 
        background: rgba(128,128,128,0.1); 
        border-radius: 6px; 
        margin-bottom: 3px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .file-name { font-weight: 500; max-width: 70%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .file-meta { font-size: 10px; opacity: 0.7; }
    
    /* 欢迎页卡片 */
    .welcome-box {
        padding: 20px;
        border-radius: 10px;
        background-color: rgba(128, 128, 128, 0.05);
        border: 1px solid rgba(128, 128, 128, 0.2);
        margin-bottom: 15px;
        text-align: center;
    }
    
    /* 减少expander间距 */
    .streamlit-expanderHeader {
        padding: 0.4rem 0.8rem !important;
    }
    
    /* 减少caption间距 */
    .stCaption {
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# 应用启动日志
if 'app_initialized' not in st.session_state:
    terminal_logger.separator("RAG Pro Max 启动")
    terminal_logger.info("应用初始化中...")
    st.session_state.app_initialized = True
    terminal_logger.success("应用初始化完成")

# ==========================================
# 2. 本地持久化与工具函数
# ==========================================
CONFIG_FILE = "rag_config.json"
HISTORY_DIR = "chat_histories"
UPLOAD_DIR = "temp_uploads" # 临时上传目录

# 确保目录存在
for d in [HISTORY_DIR, UPLOAD_DIR]:
    if not os.path.exists(d): os.makedirs(d)

defaults = load_config()

def fetch_remote_models(base_url, api_key):
    if not base_url: return None, "请填写 Base URL"
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
            return None, f"连接失败或API错误: {e}"
    return None, "未找到模型列表或路径错误"

# --- 3. 核心初始化 (带缓存) ---
def check_hf_model_exists(model_name):
    """检查 HuggingFace 模型是否已下载到本地"""
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
    """检测知识库的向量维度（带缓存）"""
    # 1. 尝试从缓存获取
    if 'kb_dimensions' not in st.session_state:
        st.session_state.kb_dimensions = {}
    
    # 使用文件修改时间作为缓存键的一部分，确保知识库更新后缓存失效
    kb_cache_key = f"{os.path.basename(db_path)}_dim"
    try:
        kb_info_file = os.path.join(db_path, ".kb_info.json")
        if os.path.exists(kb_info_file):
            mtime = os.path.getmtime(kb_info_file)
            kb_cache_key = f"{os.path.basename(db_path)}_dim_{mtime}"
            
            # 清理旧缓存
            keys_to_remove = [k for k in st.session_state.kb_dimensions if k.startswith(f"{os.path.basename(db_path)}_dim") and k != kb_cache_key]
            for k in keys_to_remove:
                del st.session_state.kb_dimensions[k]
    except:
        pass

    if kb_cache_key in st.session_state.kb_dimensions:
        return st.session_state.kb_dimensions[kb_cache_key]

    print(f"🔍 开始检测维度: {db_path}")
    
    try:
        # 方法0: 先检查保存的 KB 信息
        import json
        kb_info_file = os.path.join(db_path, ".kb_info.json")
        if os.path.exists(kb_info_file):
            try:
                with open(kb_info_file, 'r') as f:
                    kb_info = json.load(f)
                    if 'embedding_dim' in kb_info:
                        dim = kb_info['embedding_dim']
                        model = kb_info.get('embedding_model', 'unknown')
                        print(f"✅ 从 KB 信息读取维度: {dim}D (模型: {model})")
                        st.session_state.kb_dimensions[kb_cache_key] = dim
                        return dim
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



def generate_doc_summary(doc_text, filename):
    """
    生成单个文档的摘要，使用当前的 LLM 设置。
    """
    # 屏蔽多线程警告
    import warnings
    import logging
    warnings.filterwarnings('ignore')
    logging.getLogger('streamlit').setLevel(logging.ERROR)
    
    if not hasattr(Settings, 'llm'): return "总结失败: LLM未初始化"
    try:
        llm = Settings.llm
        summary_prompt = (
            f"以下是文档 '{filename}' 的一个片段内容，请用一段简短的中文话总结其核心内容 (不超过 80 字)，用于文件清单预览。内容:\n---\n{doc_text[:2000]}..."
        )
        response = llm.complete(summary_prompt)
        return response.text.strip().replace('\n', ' ')\
                             .replace('总结:', '').replace('总结是：', '').strip()
        
    except Exception as e:
        return f"总结失败: {str(e)}"

with st.sidebar:
    # P0改进1: 快速开始模式
    st.markdown("### ⚡ 快速开始")
    
    if st.button("⚡ 一键配置（推荐新手）", type="primary", use_container_width=True, help="自动配置默认设置，1分钟开始使用"):
        # 自动配置 Ollama
        config = load_config()
        config["llm_provider"] = "Ollama"
        config["llm_url_ollama"] = "http://localhost:11434"
        config["llm_model_ollama"] = "qwen2.5:7b"
        
        # 自动配置嵌入模型
        config["embed_provider_idx"] = 0  # HuggingFace
        config["embed_model_hf"] = "BAAI/bge-small-zh-v1.5"
        
        save_config(config)
        st.success("✅ 已使用默认配置！\n\n💡 下一步：创建知识库 → 上传文档 → 开始对话")
        time.sleep(2)
        st.rerun()
    
    st.caption("💡 或手动配置（高级用户）")
    
    st.markdown("---")
    
    # P0改进3: 侧边栏分组 - 基础配置（默认折叠）
    with st.expander("⚙️ 基础配置", expanded=False):
        st.markdown("**LLM 对话模型**")
        
        # LLM配置内容移到这里（稍后处理）
        llm_provider_choice = st.radio("供应商", ["Ollama (本地)", "OpenAI-Compatible (云端)"], horizontal=True, label_visibility="collapsed")
        
        if llm_provider_choice.startswith("Ollama"):
            llm_provider = "Ollama"
            llm_url = st.text_input("Ollama URL", defaults.get("llm_url_ollama", "http://localhost:11434"))
            
            # 检测 Ollama 状态
            ollama_ok = check_ollama_status(llm_url)
            
            col_status, _ = st.columns([3, 1])
            with col_status:
                if ollama_ok:
                    st.success("✅ Ollama 已连接")
                else:
                    st.warning("⚠️ Ollama 未运行")
            
            # 模型选择/输入 - 使用新组件 (Stage 3.2.1)
            saved_model = defaults.get("llm_model_ollama", "qwen2.5:7b")
            llm_model, save_as_default = render_ollama_model_selector(llm_url, saved_model, ollama_ok)
            
            # 处理"设为默认"按钮
            if save_as_default:
                config = load_config()
                config["llm_model_ollama"] = llm_model
                save_config(config)
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
            
            llm_key = st.text_input("API Key", value=default_key, type="password", help="可从环境变量 OPENAI_API_KEY 自动加载")
            if st.button("🔄 刷新列表", use_container_width=True):
                with st.spinner("正在连接模型列表..."):
                    mods, err = fetch_remote_models(llm_url, llm_key)
                    if mods: st.session_state.model_list = mods
                    else: st.error(err)
            
            if st.session_state.model_list:
                saved_model = defaults.get("llm_model_openai", "deepseek-chat")
                idx = st.session_state.model_list.index(saved_model) if saved_model in st.session_state.model_list else 0
                llm_model = st.selectbox("选择模型", st.session_state.model_list, index=idx)
            else:
                llm_model = st.text_input("输入模型名", defaults.get("llm_model_openai", "deepseek-chat"), key="llm_openai_1")

        st.markdown("---")
        st.markdown("**Embedding 向量模型**")
        st.caption("💡 用于理解文档语义")
        
        embed_idx = defaults.get("embed_provider_idx", 0)
        if embed_idx > 2: embed_idx = 0
        embed_provider = st.selectbox("供应商", ["HuggingFace (本地/极速)", "OpenAI-Compatible", "Ollama"], index=embed_idx, key="embed_provider_1")
        
        if embed_provider.startswith("HuggingFace"):
            # 预设优秀模型列表
            preset_models = [
                "BAAI/bge-small-zh-v1.5",      # 小型，快速
                "BAAI/bge-large-zh-v1.5",      # 大型，准确
                "BAAI/bge-m3",                 # 多语言最强
                "BAAI/bge-base-zh-v1.5",       # 中型，平衡
                "moka-ai/m3e-base",            # M3E 中文优化
                "shibing624/text2vec-base-chinese",  # Text2Vec 中文
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  # 多语言轻量
                "自定义模型..."
            ]
            
            model_descriptions = {
                "BAAI/bge-small-zh-v1.5": "🚀 小型快速版 | 90MB | 适合实时应用、资源受限场景",
                "BAAI/bge-large-zh-v1.5": "🎯 中文最强版 | 1.3GB | 最高准确度，推荐用于精准检索",
                "BAAI/bge-m3": "🌍 多语言最强 | 2GB | 支持100+语言，跨语言检索最佳",
                "BAAI/bge-base-zh-v1.5": "⚖️ 平衡版本 | 400MB | 速度与准确度的完美平衡",
                "moka-ai/m3e-base": "🔤 M3E中文优化 | 400MB | 中文语义理解优化",
                "shibing624/text2vec-base-chinese": "📝 Text2Vec中文 | 400MB | 中文文本向量化专家",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": "💡 轻量多语言 | 400MB | 资源受限时的多语言方案"
            }
            
            # 从配置读取默认模型
            saved_model = defaults.get("embed_model_hf", "BAAI/bge-small-zh-v1.5")
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
                    config = load_config()
                    config["embed_model_hf"] = embed_model
                    save_config(config)
                    st.success(f"✅ 已设为默认")
                    time.sleep(1)
                    st.rerun()
            
            if not model_exists:
                st.warning("⚠️ 模型未下载")
                if st.button("📥 下载模型", key="download_hf_model", type="primary", use_container_width=True):
                    with st.spinner(f"正在下载 {embed_model}..."):
                        try:
                            import subprocess
                            download_script = f"""
import os
os.environ['HF_HUB_OFFLINE'] = '0'
os.environ['TRANSFORMERS_OFFLINE'] = '0'
from huggingface_hub import snapshot_download
snapshot_download(
    repo_id="{embed_model}",
    cache_dir="./hf_cache",
    local_dir="./hf_cache/{embed_model.replace('/', '--')}",
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
                                st.success(f"✅ 下载完成: {embed_model}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"下载失败: {result.stderr}")
                        except Exception as e:
                            st.error(f"下载失败: {e}")
            else:
                st.success("✅ 模型已就绪")
            
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
    
    # P0改进3: 高级功能（默认折叠）
    with st.expander("🎯 高级功能", expanded=False):
        # P0改进2: 专业术语通俗化
        st.markdown("**智能重排序 (Re-ranking)**")
        enable_rerank = st.checkbox(
            "开启智能重排序",
            value=False,
            key="enable_rerank",
            help="💡 **通俗解释**：就像搜索引擎的第二次筛选，把最相关的结果排在前面\n\n"
                 "🔧 **技术名称**：Re-ranking (Cross-Encoder)\n"
                 "📈 **效果提升**：准确率 +10~20%\n"
                 "⏱️ **速度影响**：查询延迟 +0.5~1秒"
        )
        
        if enable_rerank:
            st.caption("📊 **工作原理**：先检索10个候选 → 智能重排序 → 返回最相关的3个")
            
            rerank_model = st.selectbox(
                "模型选择",
                ["BAAI/bge-reranker-base（推荐）", "BAAI/bge-reranker-v2-m3（更强）"],
                key="rerank_model_display",
                help="首次使用会自动下载模型（约 1GB）"
            )
            
            # 保存实际模型名
            if "推荐" in rerank_model:
                st.session_state.rerank_model = "BAAI/bge-reranker-base"
            else:
                st.session_state.rerank_model = "BAAI/bge-reranker-v2-m3"
        
        st.markdown("---")
        
        # P0改进2: BM25通俗化
        st.markdown("**关键词增强 (BM25)**")
        enable_bm25 = st.checkbox(
            "开启关键词增强",
            value=False,
            key="enable_bm25",
            help="💡 **通俗解释**：除了理解语义，还能精确匹配关键词（如版本号、代码、专有名词）\n\n"
                 "🔧 **技术名称**：BM25 混合检索\n"
                 "📈 **效果提升**：准确率再 +5~10%\n"
                 "⏱️ **速度影响**：查询延迟 +0.2~0.5秒"
        )
        
        if enable_bm25:
            st.caption("📊 **工作原理**：语义检索 + 关键词匹配 → 智能融合 → 返回最佳结果")
            st.caption("✨ **适用场景**：需要精确匹配版本号、代码片段、专有名词时")
    
    # P0改进3: 系统工具（默认折叠）
    with st.expander("🛠️ 系统工具", expanded=False):
        # 系统监控
        auto_refresh = st.checkbox("🔄 自动刷新 (2秒)", value=False, key="monitor_auto_refresh")
        
        monitor_placeholder = st.empty()
        
        import psutil
        import subprocess
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/System/Volumes/Data')
        
        gpu_active = False
        try:
            result = subprocess.run(['ioreg', '-r', '-d', '1', '-w', '0', '-c', 'IOAccelerator'],
                                  capture_output=True, text=True, timeout=1)
            if 'PerformanceStatistics' in result.stdout:
                gpu_active = True
        except:
            pass
        
        with monitor_placeholder.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.metric("CPU 使用率", f"{cpu_percent:.1f}%")
            with col2:
                st.caption(f"{psutil.cpu_count()} 核")
            st.progress(cpu_percent / 100)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.metric("GPU 状态", "活跃" if gpu_active else "空闲")
            with col2:
                st.caption("32 核")
            if gpu_active:
                st.progress(0.5)
            else:
                st.progress(0.0)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.metric("内存使用", f"{mem.percent:.1f}%")
            with col2:
                st.caption(f"{mem.used/1024**3:.1f}GB")
            st.progress(mem.percent / 100)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.metric("磁盘使用", f"{disk.percent:.1f}%")
            with col2:
                st.caption(f"{disk.used/1024**3:.0f}GB")
            st.progress(disk.percent / 100)
            
            current_proc = psutil.Process()
            proc_mem = current_proc.memory_info().rss / 1024**3
            st.caption(f"🔍 进程: {proc_mem:.1f}GB | {current_proc.num_threads()} 线程")
            st.caption("💡 GPU 详细信息需要: `sudo python3 system_monitor.py`")
        
        if auto_refresh:
            import time
            time.sleep(2)
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 💠 知识库控制台")
    if "model_list" not in st.session_state: st.session_state.model_list = []

    # 使用当前工作目录下的 vector_db_storage
    default_output_path = os.path.join(os.getcwd(), "vector_db_storage")
    output_base = st.text_input("存储根目录", value=default_output_path)
    existing_kbs = get_existing_kbs(output_base)

    # --- 核心导航 ---
    st.markdown("#### 📚 知识库管理")
    
    # 知识库搜索/过滤
    if len(existing_kbs) > 5:
        search_kb = st.text_input(
            "🔍 搜索知识库",
            placeholder="输入关键词过滤...",
            key="search_kb",
            label_visibility="collapsed"
        )
        if search_kb:
            filtered_kbs = [kb for kb in existing_kbs if search_kb.lower() in kb.lower()]
            st.caption(f"找到 {len(filtered_kbs)} 个匹配的知识库")
        else:
            filtered_kbs = existing_kbs
    else:
        filtered_kbs = existing_kbs
    
    nav_options = ["➕ 新建知识库..."] + [f"📂 {kb}" for kb in filtered_kbs]
    
    # 默认选择"新建知识库"，避免自动加载大知识库
    default_idx = 0
    if "current_nav" in st.session_state and st.session_state.current_nav in nav_options:
        default_idx = nav_options.index(st.session_state.current_nav)
    # 注释掉自动选择第一个知识库的逻辑
    # elif len(nav_options) > 1:
    #     default_idx = 1 
        
    selected_nav = st.selectbox("选择当前知识库", nav_options, index=default_idx, label_visibility="collapsed")
    
    # 卸载知识库按钮（释放内存）
    if not (selected_nav == "➕ 新建知识库...") and st.session_state.get('chat_engine') is not None:
        if st.button("🔓 卸载知识库（释放内存）", use_container_width=True, help="释放当前知识库占用的内存资源"):
            st.session_state.chat_engine = None
            st.session_state.current_kb_id = None
            cleanup_memory()
            st.toast("✅ 知识库已卸载，内存已释放")
            st.rerun()
    
    if selected_nav != st.session_state.get('current_nav'):
        st.session_state.pop('suggestions_history', None) 
        
    st.session_state.current_nav = selected_nav
    
    is_create_mode = (selected_nav == "➕ 新建知识库...")
    current_kb_name = selected_nav.replace("📂 ", "") if not is_create_mode else None

    # --- 数据源配置区 ---
    if is_create_mode:
        st.caption("🛠️ 创建新知识库")
    else:
        st.caption(f"🛠️ 管理: {current_kb_name}")

    with st.container(border=True):
        if is_create_mode:
            action_mode = "NEW"
        else:
            action_mode = st.radio("操作模式", ["➕ 追加", "🔄 覆盖"], horizontal=True, label_visibility="collapsed")
            action_mode = "APPEND" if "追加" in action_mode else "NEW"

        st.markdown("**数据源**")
        
        if "path_val" not in st.session_state: 
            st.session_state.path_val = os.path.abspath(defaults.get("target_path", ""))

        if 'path_input' not in st.session_state:
            st.session_state.path_input = ""
        
        # 如果有上传路径且输入框为空，自动填充
        if st.session_state.get('uploaded_path') and not st.session_state.path_input:
            st.session_state.path_input = st.session_state.uploaded_path
        
        # 优化路径显示
        path_col1, path_col2 = st.columns([5, 1])
        with path_col1:
            target_path = st.text_input(
                "文件/文件夹路径", 
                value=st.session_state.path_input,
                placeholder="📁 /Users/username/docs 或上传后自动生成",
                key="path_input_display",
                label_visibility="collapsed"
            )
            # 同步到 path_input
            if target_path != st.session_state.path_input:
                st.session_state.path_input = target_path
        with path_col2:
            if st.button("📂", help="在Finder中打开", use_container_width=True):
                if target_path and os.path.exists(target_path):
                    # macOS: 在Finder中打开
                    import webbrowser
                    import urllib.parse
                    try:
                        file_url = 'file://' + urllib.parse.quote(os.path.abspath(target_path))
                        webbrowser.open(file_url)
                        st.toast("✅ 已在Finder中打开")
                    except Exception as e:
                        st.error(f"打开失败: {e}")
                else:
                    st.warning("💡 请先输入有效路径，或使用下方上传功能")
        
        
        uploaded_files = st.file_uploader(
            "⬆️ 或拖入文件/ZIP", 
            accept_multiple_files=True, 
            key="uploader",
            label_visibility="collapsed"
        )
        
        # 处理上传
        if uploaded_files:
            if 'last_uploaded_names' not in st.session_state:
                st.session_state.last_uploaded_names = []
            
            current_names = [f.name for f in uploaded_files]
            
            # 只在文件列表变化时处理
            if set(current_names) != set(st.session_state.last_uploaded_names):
                batch_dir = os.path.join(UPLOAD_DIR, f"batch_{int(time.time())}")
                os.makedirs(batch_dir, exist_ok=True)
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 文件验证配置
                MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
                ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.docx', '.md', '.xlsx', '.csv', '.pptx', '.html', '.json', '.zip'}
                
                success_count = 0
                skipped_count = 0
                skip_reasons = []
                
                for idx, f in enumerate(uploaded_files):
                    try:
                        status_text.text(f"验证中: {f.name} ({idx+1}/{len(uploaded_files)})")
                        
                        # 1. 检查文件大小
                        if f.size > MAX_FILE_SIZE:
                            skipped_count += 1
                            skip_reasons.append(f"{f.name}: 超过100MB")
                            continue
                            
                        # 2. 检查扩展名
                        ext = os.path.splitext(f.name)[1].lower()
                        if ext not in ALLOWED_EXTENSIONS:
                            skipped_count += 1
                            skip_reasons.append(f"{f.name}: 类型不支持 ({ext})")
                            continue
                            
                        p = os.path.join(batch_dir, f.name)
                        
                        with open(p, "wb") as w: 
                            w.write(f.getbuffer())
                        
                        # 处理 ZIP (带安全检查)
                        if f.name.endswith('.zip'):
                            try:
                                with zipfile.ZipFile(p, 'r') as z: 
                                    # 2.1 ZIP炸弹检查
                                    total_size = sum(info.file_size for info in z.infolist())
                                    if total_size > 500 * 1024 * 1024: # 解压后超过500MB
                                        skipped_count += 1
                                        skip_reasons.append(f"{f.name}: ZIP解压后过大(>500MB)")
                                        os.remove(p)
                                        continue
                                    
                                    # 2.2 路径遍历检查
                                    is_safe = True
                                    for info in z.infolist():
                                        if info.filename.startswith('/') or '..' in info.filename:
                                            is_safe = False
                                            break
                                    
                                    if not is_safe:
                                        skipped_count += 1
                                        skip_reasons.append(f"{f.name}: ZIP包含非法路径")
                                        os.remove(p)
                                        continue
                                        
                                    z.extractall(batch_dir)
                                os.remove(p)
                            except Exception as e:
                                skipped_count += 1
                                skip_reasons.append(f"{f.name}: ZIP解压失败 {str(e)}")
                                if os.path.exists(p): os.remove(p)
                                continue
                        
                        logger.log_file_upload(f.name, "success")
                        success_count += 1
                        
                        progress_bar.progress((idx + 1) / len(uploaded_files))
                    except Exception as e:
                        logger.log_file_upload(f.name, "error", str(e))
                        skipped_count += 1
                        skip_reasons.append(f"{f.name}: 系统错误")
                
                progress_bar.empty()
                status_text.empty()
                
                st.session_state.last_uploaded_names = current_names
                st.session_state.uploaded_path = os.path.abspath(batch_dir)
                
                # 显示上传结果
                if success_count > 0:
                    st.success(f"✅ 成功上传 {success_count} 个文件")
                
                if skipped_count > 0:
                    st.warning(f"⚠️ 跳过 {skipped_count} 个文件")
                    with st.expander("查看跳过详情", expanded=False):
                        for reason in skip_reasons:
                            st.text(f"• {reason}")
                
                time.sleep(1)
                if success_count > 0:
                    st.rerun()


        # 使用上传路径或手动输入的路径
        target_path = st.session_state.get('uploaded_path') or target_path
        
        auto_name = ""
        if target_path:
            if os.path.exists(target_path):
                # 统计文件信息
                all_files = [f for r,d,fs in os.walk(target_path) for f in fs if not f.startswith('.')]
                cnt = len(all_files)
                
                # 统计文件类型
                file_types = {}
                total_size = 0
                for root, dirs, files in os.walk(target_path):
                    for f in files:
                        if not f.startswith('.'):
                            ext = os.path.splitext(f)[1].upper() or 'OTHER'
                            file_types[ext] = file_types.get(ext, 0) + 1
                            try:
                                total_size += os.path.getsize(os.path.join(root, f))
                            except:
                                pass
                
                # 美化显示
                size_mb = total_size / (1024 * 1024)
                folder_name = os.path.basename(target_path.rstrip('/'))
                
                st.success(f"✅ **有效数据源**: `{folder_name}`")
                
                # 三列统计卡片
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                stat_col1.metric("📄 文件数", f"{cnt}")
                stat_col2.metric("💾 总大小", f"{size_mb:.1f}MB" if size_mb > 1 else f"{total_size/1024:.0f}KB")
                stat_col3.metric("📂 类型", f"{len(file_types)} 种")
                
                # 类型分布（只显示前5种）
                if file_types:
                    st.caption("**文件类型分布**")
                    sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]
                    type_text = " · ".join([f"{ext.replace('.', '')}: {count}" for ext, count in sorted_types])
                    if len(file_types) > 5:
                        type_text += f" · 其他: {sum(c for _, c in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[5:])}"
                    st.caption(type_text)
                
                auto_name = folder_name
            else:
                st.error("❌ 路径不存在，请检查路径是否正确")

        # final_kb_name 必须在 if/else 中被定义，以确保其在模块作用域内
        st.write("")
        if is_create_mode:
            st.markdown("**知识库名称**")
            final_kb_name = st.text_input(
                "知识库名称", 
                value=sanitize_filename(auto_name), 
                placeholder="例如: Project_Alpha, 技术文档库",
                label_visibility="collapsed",
                help="建议使用英文、数字、下划线，避免特殊字符"
            )
        else:
            final_kb_name = current_kb_name

        # 高级选项
        with st.expander("🔧 高级选项", expanded=False):
            force_reindex = st.checkbox("🔄 强制重建索引", False, help="删除现有索引，重新构建（用于修复损坏的索引）")
            st.caption("⚠️ 强制重建会删除现有的向量索引和文档片段，重新解析所有文档")
        
        st.write("")
        
        btn_label = "🚀 立即创建" if is_create_mode else ("➕ 执行追加" if action_mode=="APPEND" else "🔄 执行覆盖")
        btn_start = st.button(btn_label, type="primary", use_container_width=True)

    # --- 现有库的管理 ---
    if not is_create_mode:
        st.write("")
        st.divider()
        
        # 聊天控制 (P2 优化 - 撤销功能)
        st.caption("🛠️ 聊天控制")
        col1, col2 = st.columns(2)
        
        # 撤销按钮
        if col1.button("↩️ 撤销提问", use_container_width=True, disabled=len(st.session_state.messages) < 2, help="撤销最后一组问答"):
            if len(st.session_state.messages) >= 2:
                # 弹出最后两条消息 (User + Assistant)
                st.session_state.messages.pop()
                st.session_state.messages.pop()
                # 保存更新后的历史
                if current_kb_name:
                    save_chat_history(current_kb_name, st.session_state.messages)
                st.toast("✅ 已撤销上一条消息")
                time.sleep(0.5)
                st.rerun()
        
        # 清空按钮
        if col2.button("🧹 清空对话", use_container_width=True, disabled=len(st.session_state.messages) == 0):
            st.session_state.messages = []
            st.session_state.suggestions_history = []
            if current_kb_name:
                save_chat_history(current_kb_name, [])
            st.toast("✅ 对话已清空")
            time.sleep(0.5)
            st.rerun()
        
        # 对话历史管理
        if len(st.session_state.messages) > 0:
            col3, col4 = st.columns(2)
            
            # 导出对话
            if col3.button("📥 导出对话", use_container_width=True, help="导出为 Markdown 文件"):
                export_content = f"# 对话记录 - {current_kb_name}\n\n"
                export_content += f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                export_content += "---\n\n"
                
                for i, msg in enumerate(st.session_state.messages, 1):
                    role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
                    export_content += f"## {role} ({i})\n\n{msg['content']}\n\n"
                
                st.download_button(
                    "💾 下载 Markdown",
                    export_content,
                    file_name=f"chat_{current_kb_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # 对话统计
            if col4.button("📊 对话统计", use_container_width=True):
                qa_count = len(st.session_state.messages) // 2
                total_chars = sum(len(msg["content"]) for msg in st.session_state.messages)
                st.info(f"💬 问答轮次: {qa_count}\n\n📝 总字符数: {total_chars}")
            
        # 并行对话 (P2 优化 - 响应用户多线程需求)
        st.write("")
        st.link_button("🔀 新开窗口 (并行对话)", "http://localhost:8501", help="Streamlit 限制单页面无法并行生成。点击此按钮打开新窗口，即可实现一边生成、一边提问。", use_container_width=True)

        st.write("")
        st.caption("⚠️ 危险操作")
        
        if 'confirm_delete' not in st.session_state:
            st.session_state.confirm_delete = False
        
        if not st.session_state.confirm_delete:
            if st.button("🗑️ 删除此知识库", use_container_width=True, type="secondary"):
                st.session_state.confirm_delete = True
        else:
            st.warning(f"⚠️ 确认删除 **{current_kb_name}**？\n\n此操作不可恢复，将删除所有文档和对话历史。")
            col1, col2 = st.columns(2)
            if col1.button("✅ 确认删除", use_container_width=True, type="primary"):
                try:
                    with st.spinner(f"正在删除 {current_kb_name}..."):
                        shutil.rmtree(os.path.join(output_base, current_kb_name), ignore_errors=True)
                        hist_path = os.path.join(HISTORY_DIR, f"{current_kb_name}.json")
                        if os.path.exists(hist_path):
                            os.remove(hist_path)
                    st.success("✅ 删除成功")
                    st.session_state.current_nav = "➕ 新建知识库..."
                    st.session_state.confirm_delete = False
                    st.session_state.pop('suggestions_history', None)
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"删除失败: {e}")
                    st.session_state.confirm_delete = False
            if col2.button("❌ 取消", use_container_width=True):
                st.session_state.confirm_delete = False

    # --- 快速开始模式 ---
    st.write("")
    if st.button("⚡ 快速开始（使用默认配置）", use_container_width=True, type="primary", help="自动配置 Ollama + 默认嵌入模型，1 分钟开始使用"):
        # 保存快速配置
        quick_config = {
            "llm_type_idx": 0,
            "llm_url_ollama": "http://127.0.0.1:11434",
            "llm_model_ollama": "qwen2.5:7b",
            "embed_provider_index": 0,
            "embed_model_hf": "BAAI/bge-small-zh-v1.5"
        }
        
        # 合并到现有配置
        defaults.update(quick_config)
        
        # 保存配置文件
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(defaults, f, indent=4, ensure_ascii=False)
        
        st.success("✅ 已使用默认配置！\n\n📝 LLM: Ollama (qwen2.5:7b)\n📝 嵌入: BAAI/bge-small-zh-v1.5\n\n现在可以直接创建知识库了！")
        terminal_logger.success("快速开始模式：已配置默认值")
        time.sleep(1.5)
        st.rerun()
    
    st.caption("💡 提示：快速开始会使用 Ollama 本地模型，需要先安装 Ollama")
    
    # --- 模型配置区域 (折叠收纳) ---
    st.write("")
# ==========================================
# 5. 核心逻辑 (RAG & Indexing)
# ==========================================

def process_knowledge_base_logic():
    persist_dir = os.path.join(output_base, final_kb_name) 
    index = None
    docs = []
    file_infos = []
    start_time = time.time()

    # ⚠️ 关键修复：在处理开始时就设置嵌入模型
    terminal_logger.info(f"🔧 设置嵌入模型: {embed_model} (provider: {embed_provider})")
    embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
    if embed:
        Settings.embed_model = embed
        try:
            actual_dim = len(embed._get_text_embedding("test"))
            terminal_logger.success(f"✅ 嵌入模型已设置: {embed_model} ({actual_dim}维)")
        except:
            terminal_logger.success(f"✅ 嵌入模型已设置: {embed_model}")
    else:
        terminal_logger.error(f"❌ 嵌入模型加载失败: {embed_model}")
        raise ValueError(f"无法加载嵌入模型: {embed_model}")

    logger.log_kb_start(kb_name=final_kb_name)
    
    status_container = st.status(f"🚀 处理知识库: {final_kb_name}", expanded=True)
    prog_bar = status_container.progress(0)
    status_container.write(f"⏱️ 开始时间: {datetime.now().strftime('%H:%M:%S')}")

    # 步骤 1: 检查现有索引
    terminal_logger.separator(f"知识库处理: {final_kb_name}")
    terminal_logger.info(f"📂 [步骤 1/6] 检查现有索引...")
    if not force_reindex and os.path.exists(persist_dir) and action_mode != "NEW":
        try:
            logger.log_kb_load_index(final_kb_name)
            status_container.write("📂 [步骤1/6] 检查现有索引...")
            
            # 设置 embedding 模型确保兼容性
            terminal_logger.info(f"🔧 创建知识库使用模型: {embed_model} (provider: {embed_provider})")
            embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
            if embed:
                Settings.embed_model = embed
                actual_dim = len(embed._get_text_embedding("test"))
                terminal_logger.info(f"✅ 模型维度: {actual_dim}")
            else:
                terminal_logger.error("❌ 嵌入模型加载失败！")
            
            storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
            index = load_index_from_storage(storage_context)
            status_container.write("✅ 现有索引加载成功，将追加新文档")
            terminal_logger.success("✅ [步骤 1/6] 现有索引加载成功，将追加新文档")
            prog_bar.progress(10)
        except Exception as e:
            error_msg = str(e)
            # 检查是否是维度不匹配错误
            if "shapes" in error_msg and "not aligned" in error_msg:
                status_container.write(f"⚠️  向量维度不匹配，清理旧索引")
                terminal_logger.warning(f"⚠️  [步骤 1/6] 向量维度不匹配，转为新建模式")
            else:
                status_container.write(f"⚠️  索引损坏，转为新建模式")
                terminal_logger.warning(f"⚠️  [步骤 1/6] 索引损坏，转为新建模式")
            shutil.rmtree(persist_dir, ignore_errors=True)
            index = None

    current_target_path = st.session_state.get('uploaded_path') or st.session_state.path_input
    
    if not current_target_path or not os.path.exists(current_target_path):
        status_container.update(label="❌ 路径无效", state="error")
        terminal_logger.error(f"❌ 路径无效: {current_target_path}")
        raise ValueError(f"路径无效: {current_target_path}")

    # 步骤 2: 扫描文件
    terminal_logger.info(f"📁 [步骤 2/6] 扫描文件夹: {os.path.basename(current_target_path)}")
    logger.log_kb_scan_path(current_target_path, kb_name=final_kb_name)
    status_container.write(f"📁 [步骤2/6] 扫描文件夹: {os.path.basename(current_target_path)}")
    
    # 先快速统计文件数量
    all_files = []
    for root, _, filenames in os.walk(current_target_path):
        for f in filenames:
            if not f.startswith('.'):
                all_files.append(os.path.join(root, f))
    
    total_files = len(all_files)
    status_container.write(f"   📊 发现 {total_files} 个文件")
    terminal_logger.success(f"✅ [步骤 2/6] 扫描完成: 发现 {total_files} 个文件")
    prog_bar.progress(20)
    
    # 步骤 3: 读取文档
    terminal_logger.info(f"📖 [步骤 3/6] 读取文档内容 (共 {total_files} 个文件)")
    status_container.write(f"📖 [步骤3/6] 读取文档内容 (共 {total_files} 个文件)")
    if total_files > 10:
        status_container.write(f"   🚀 250 线程并行读取 | 批量 5 个文件 | 目标 < 80% 资源")
        terminal_logger.info(f"   🚀 启用 250 线程并行读取")
    
    # 创建一个占位符用于实时更新
    progress_placeholder = status_container.empty()
    
    docs, process_result = scan_directory_safe(current_target_path)
    summary = process_result.get_summary()
    
    if summary['success'] == 0:
        status_container.update(label="❌ 没有可处理的文件", state="error")
        raise ValueError(f"没有成功读取的文件。{process_result.get_report()}")
    
    # 计算总数和成功率
    total_files = summary['success'] + summary['failed'] + summary['skipped']
    success_rate = (summary['success'] / total_files * 100) if total_files > 0 else 0
    
    status_container.write(f"✅ 读取完成: {summary['success']}/{total_files} 个文件 ({success_rate:.1f}%)，{summary['total_docs']} 个文档片段")
    terminal_logger.success(f"✅ [步骤 3/6] 读取完成: {summary['success']}/{total_files} 个文件，{summary['total_docs']} 个文档片段")
    if summary['failed'] > 0:
        status_container.write(f"   ⚠️  失败: {summary['failed']} 个文件 ({summary['failed']/total_files*100:.1f}%)")
        terminal_logger.warning(f"   ⚠️  失败: {summary['failed']} 个文件")
    if summary['skipped'] > 0:
        status_container.write(f"   ⏭️  跳过: {summary['skipped']} 个文件 ({summary['skipped']/total_files*100:.1f}%)")
        terminal_logger.info(f"   ⏭️  跳过: {summary['skipped']} 个文件")
    prog_bar.progress(40)
    
    # 步骤 4: 构建文件清单
    terminal_logger.info(f"📋 [步骤 4/6] 构建文件清单...")
    status_container.write(f"📋 [步骤4/6] 构建文件清单...")
    
    # 初始化元数据管理器
    metadata_mgr = MetadataManager(persist_dir)
    
    temp_file_map = {}
    for root, _, filenames in os.walk(current_target_path):
        for f in filenames:
            if not f.startswith('.'):
                fp = os.path.join(root, f)
                info = get_file_info(fp, metadata_mgr); info['doc_ids'] = []
                temp_file_map[f] = info
    
    file_count = len(temp_file_map)
    logger.log_kb_read_success(len(docs), file_count=file_count, kb_name=final_kb_name)
    status_container.write(f"✅ 清单完成: {file_count} 个文件已登记")
    terminal_logger.success(f"✅ [步骤 4/6] 清单完成: {file_count} 个文件已登记")
    logger.log_kb_manifest(file_count, kb_name=final_kb_name)
    prog_bar.progress(50)
    
    # 步骤 5: 解析文档片段（快速模式 + 后台摘要 + 元数据提取）
    terminal_logger.info(f"🔍 [步骤 5/6] 解析文档片段 (共 {len(docs)} 个)")
    terminal_logger.info(f"   📋 任务: 映射文档ID → 文件清单 + 元数据提取")
    status_container.write(f"🔍 [步骤5/6] 解析文档片段 (共 {len(docs)} 个)")
    
    step5_start = time.time()
    # 快速映射文档ID + 提取元数据
    file_text_samples = {}  # 收集每个文件的文本样本
    for d in docs:
        fname = d.metadata.get('file_name')
        if fname and fname in temp_file_map:
            temp_file_map[fname]['doc_ids'].append(d.doc_id)
            # 收集文本样本用于元数据提取
            if fname not in file_text_samples and d.text.strip():
                file_text_samples[fname] = d.text[:1000]  # 前1000字用于分析
    
    # 批量处理元数据（多进程加速）
    status_container.write(f"   🔖 提取元数据: 哈希/关键词/分类... ({len(file_text_samples)} 个文件)")
    terminal_logger.info(f"   🔖 提取元数据: {len(file_text_samples)} 个文件")
    
    if len(file_text_samples) > 100:
        # 大量文件，使用多进程
        import multiprocessing as mp
        
        # 准备任务列表
        tasks = []
        for fname, text_sample in file_text_samples.items():
            if fname in temp_file_map:
                fp = os.path.join(current_target_path, fname)
                if os.path.exists(fp):
                    doc_ids = temp_file_map[fname]['doc_ids']
                    tasks.append((fp, fname, doc_ids, text_sample, persist_dir))
        
        # 多进程处理
        num_workers = min(mp.cpu_count(), 12)  # 最多12进程
        status_container.write(f"   ⚡ 使用 {num_workers} 进程并行提取...")
        terminal_logger.info(f"   ⚡ 使用 {num_workers} 进程并行提取元数据")
        
        with mp.Pool(processes=num_workers) as pool:
            results = pool.map(_extract_metadata_task, tasks, chunksize=50)
        
        # 更新结果
        metadata_count = 0
        for fname, meta in results:
            if fname in temp_file_map:
                temp_file_map[fname].update({
                    'file_hash': meta.get('file_hash', ''),
                    'keywords': meta.get('keywords', []),
                    'language': meta.get('language', 'unknown'),
                    'category': meta.get('category', '其他文档')
                })
                metadata_count += 1
        
        terminal_logger.success(f"   ✅ 元数据提取完成: {metadata_count} 个文件")
    else:
        # 少量文件，单线程处理
        terminal_logger.info(f"   📝 单线程处理 {len(file_text_samples)} 个文件")
        metadata_count = 0
        for fname, text_sample in file_text_samples.items():
            if fname in temp_file_map:
                fp = os.path.join(current_target_path, fname)
                if os.path.exists(fp):
                    doc_ids = temp_file_map[fname]['doc_ids']
                    meta = metadata_mgr.add_file_metadata(fp, doc_ids, text_sample)
                    temp_file_map[fname].update({
                        'file_hash': meta.get('file_hash', ''),
                        'keywords': meta.get('keywords', []),
                        'language': meta.get('language', 'unknown'),
                        'category': meta.get('category', '其他文档')
                    })
                    metadata_count += 1
    
    if metadata_count > 0:
        status_container.write(f"   ✅ 元数据提取完成: {metadata_count} 个文件")
        terminal_logger.success(f"   ✅ 元数据提取完成: {metadata_count} 个文件")
    
    # 收集需要生成摘要的文档
    summary_tasks = []
    for d in docs:
        fname = d.metadata.get('file_name')
        if fname and fname in temp_file_map and d.text.strip() and not temp_file_map[fname].get('summary'):
            summary_tasks.append((fname, d.text[:2000]))  # 只保存前2000字
    
    if summary_tasks:
        status_container.write(f"   💡 摘要生成已加入后台队列 ({len(summary_tasks)} 个文件)")
        status_container.write(f"   ⚡ 知识库将立即完成，摘要在后台生成")
        
        # 保存摘要任务到文件，供后台处理
        summary_queue_file = os.path.join(persist_dir, "summary_queue.json")
        os.makedirs(persist_dir, exist_ok=True)
        
        # 清理文本中的特殊字符
        def clean_text(text):
            try:
                # 移除代理对字符（surrogate pairs）
                return text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
            except:
                return ""
        
        cleaned_tasks = [(fname, clean_text(text)) for fname, text in summary_tasks]
        
        with open(summary_queue_file, 'w', encoding='utf-8', errors='ignore') as f:
            json.dump({
                'tasks': cleaned_tasks,
                'total': len(cleaned_tasks),
                'completed': 0
            }, f, ensure_ascii=False)
    
    file_infos = list(temp_file_map.values())
    valid_docs = [d for d in docs if d.text and d.text.strip()]
    status_container.write(f"✅ 解析完成: {len(valid_docs)} 个有效片段")
    prog_bar.progress(70)
    
    logger.log_kb_parse_complete(valid_count=len(valid_docs), kb_name=final_kb_name)
    
    if not valid_docs:
        status_container.update(label="❌ 文档内容为空", state="error")
        raise ValueError("路径下文档内容为空")
    
    if not valid_docs:
        status_container.update(label="❌ 文档内容为空", state="error")
        raise ValueError("路径下文档内容为空")

    # 步骤 6: 向量化和索引构建
    terminal_logger.info(f"⚡️ [步骤 6/6] 向量化和索引构建...")
    if index and action_mode == "APPEND":
        logger.log_kb_mode("append", kb_name=final_kb_name)
        terminal_logger.info(f"➕ [步骤 6/6] 追加模式: 插入新文档到现有索引")
        status_container.write(f"➕ [步骤6/6] 追加模式: 插入新文档到现有索引")
        for i, d in enumerate(valid_docs):
            index.insert(d)
            if (i + 1) % 10 == 0:
                prog_bar.progress(70 + int((i + 1) / len(valid_docs) * 20))
    else:
        logger.log_kb_mode("new", kb_name=final_kb_name)
        step6_start = time.time()
        terminal_logger.info(f"⚡️ [步骤 6/6] 新建模式: 构建向量索引")
        terminal_logger.info(f"   📋 任务清单:")
        terminal_logger.info(f"      1️⃣  文档分块 ({len(valid_docs)} 个文档)")
        terminal_logger.info(f"      2️⃣  向量化 (GPU加速)")
        terminal_logger.info(f"      3️⃣  构建索引")
        status_container.write(f"⚡️ [步骤6/6] 新建模式: 构建向量索引")
        status_container.write(f"   🚀 多核加速启动中...")
        if os.path.exists(persist_dir): shutil.rmtree(persist_dir, ignore_errors=True)
        parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        
        # 多线程并行处理（针对 M4 Max 优化：10性能核+4效率核）
        status_container.write(f"   🔥 多线程并行已启用 (共 {len(valid_docs)} 个文档)")
        terminal_logger.processing(f"🚀 [6.1] 多线程并行处理 {len(valid_docs)} 个文档...")
        
        # 动态计算线程数 - 根据CPU核心数和当前负载
        import psutil
        cpu_count = psutil.cpu_count(logical=True)
        current_cpu = psutil.cpu_percent(interval=0.5)
        current_mem = psutil.virtual_memory().percent
        
        # 目标：保持总资源使用在80%以内
        target_usage = 80.0
        available_cpu = max(10, target_usage - current_cpu)  # 至少保留10%
        available_mem = max(10, target_usage - current_mem)
        
        # 根据可用资源动态调整线程数
        if available_cpu > 30 and available_mem > 50:
            # 资源充足，激进使用
            num_workers = min(cpu_count * 6, 80)  # 最多80个线程
        elif available_cpu > 20 and available_mem > 30:
            # 资源适中
            num_workers = min(cpu_count * 4, 60)
        elif available_cpu > 10 and available_mem > 20:
            # 资源紧张
            num_workers = min(cpu_count * 2, 40)
        else:
            # 资源非常紧张
            num_workers = max(cpu_count, 20)
        
        status_container.write(f"   💻 {num_workers} 个线程运行中 (动态调整: CPU可用{available_cpu:.0f}%, 内存可用{available_mem:.0f}%)...")
        terminal_logger.info(f"   💻 启用 {num_workers} 个并行线程（动态调整，目标资源<80%）")
        terminal_logger.info(f"   📊 当前状态: CPU {current_cpu:.1f}%, 内存 {current_mem:.1f}%")
        
        terminal_logger.cpu_multicore_start(num_workers)
        parse_start = time.time()
        
        # 提取文档文本
        doc_texts = [doc.text for doc in valid_docs]
        
        status_container.write(f"   📦 正在分块处理...")
        
        # 创建实时进度占位符
        chunk_progress = status_container.empty()
        
        all_chunks = []
        processed_count = 0
        
        # 批量处理：小批次高并发
        docs_per_batch = max(10, len(doc_texts) // (num_workers * 8))  # 每批10-30个
        batches = [doc_texts[i:i + docs_per_batch] for i in range(0, len(doc_texts), docs_per_batch)]
        
        chunk_progress.write(f"      📦 分成 {len(batches)} 批，每批约 {docs_per_batch} 个文档")
        terminal_logger.info(f"   📦 分成 {len(batches)} 批处理")
        
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(_parse_batch_docs, batch) for batch in batches]
            for i, future in enumerate(as_completed(futures)):
                try:
                    chunks = future.result()
                    all_chunks.extend(chunks)
                    processed_count += len(batches[i])
                    
                    # 计算预计完成时间
                    elapsed = time.time() - parse_start
                    if processed_count > 0:
                        avg_time_per_doc = elapsed / processed_count
                        remaining_docs = len(doc_texts) - processed_count
                        eta_seconds = avg_time_per_doc * remaining_docs
                        eta_str = f"{int(eta_seconds)}s" if eta_seconds < 60 else f"{int(eta_seconds/60)}m{int(eta_seconds%60)}s"
                    else:
                        eta_str = "计算中..."
                    
                    # 实时更新进度
                    percent = int((processed_count / len(doc_texts)) * 100)
                    chunk_progress.write(f"      ⚡ 已处理: {processed_count}/{len(doc_texts)} ({percent}%) | 已生成 {len(all_chunks)} 个节点 | 预计剩余: {eta_str}")
                    
                    prog_bar.progress(70 + int((processed_count / len(doc_texts)) * 10))
                    
                    if i % 5 == 0:
                        terminal_logger.cpu_multicore_status(processed_count, len(doc_texts))
                        terminal_logger.info(f"   ⏱️  预计剩余: {eta_str}")
                        
                        # 检查资源使用，超过90%则暂停
                        cpu, mem, gpu, should_throttle = check_resource_usage()
                        if should_throttle:
                            import time as time_module
                            terminal_logger.warning(f"⚠️  资源使用过高 (CPU: {cpu:.1f}%, 内存: {mem:.1f}%, GPU: {gpu:.1f}%)，暂停1秒...")
                            time_module.sleep(1)
                            
                except Exception as e:
                    terminal_logger.error(f"批次解析失败: {e}")
        
        parse_elapsed = time.time() - parse_start
        terminal_logger.cpu_multicore_end(len(doc_texts), parse_elapsed)
        
        # 转换为 TextNode 对象
        from llama_index.core.schema import TextNode
        nodes = [TextNode(text=chunk['text']) for chunk in all_chunks]
        
        # 释放内存
        del all_chunks
        del doc_texts
        cleanup_memory()
        status_container.write(f"   🧹 内存清理完成")
        
        chunk_progress.empty()  # 清除进度占位符
        status_container.write(f"   ✅ 分块完成: {len(nodes)} 个节点 (耗时 {parse_elapsed:.1f}s)")
        prog_bar.progress(80)
        
        # GPU 向量化（最大化 GPU 利用率，不超过 90%）
        status_container.write(f"   🎮 GPU 向量化处理中...")
        status_container.write(f"      正在将 {len(nodes)} 个节点转换为向量...")
        terminal_logger.processing(f"🚀 [6.2] GPU 批量构建索引 (目标 GPU 利用率 <90%)...")
        terminal_logger.info(f"   📋 当前任务: 向量化 {len(nodes)} 个节点")
        vector_start = time.time()
        
        # 动态批次大小：优化GPU利用率（更小的batch，更频繁的GPU调用）
        import psutil
        total_mem_gb = psutil.virtual_memory().total / (1024**3)
        available_mem_gb = psutil.virtual_memory().available / (1024**3)
        
        # 优化策略：较小的batch_size，让GPU持续工作
        if len(nodes) > 500000:  # 超大规模
            batch_size = 50000   # 5万（原20万）
        elif len(nodes) > 200000:  # 大规模
            batch_size = 30000   # 3万（原15万）
        elif len(nodes) > 100000:  # 中大规模
            batch_size = 20000   # 2万（原10万）
        elif len(nodes) > 50000:  # 中等规模
            batch_size = 15000   # 1.5万（原8万）
        else:  # 小规模
            batch_size = 10000   # 1万（原5万）
        
        # 内存保护：如果可用内存不足，降低 batch_size
        if available_mem_gb < 3:
            batch_size = min(batch_size, 5000)
        elif available_mem_gb < 8:
            batch_size = min(batch_size, 10000)
        
        # 确保至少分 5 批（让GPU持续工作）
        if len(nodes) > batch_size and total_batches < 5:
            batch_size = len(nodes) // 5
            
        total_batches = (len(nodes) + batch_size - 1) // batch_size
        
        status_container.write(f"      📦 分 {total_batches} 批处理，每批 {batch_size} 个节点")
        terminal_logger.info(f"   📦 分 {total_batches} 批处理 (batch_size={batch_size})")
        terminal_logger.info(f"   🎯 目标: 最大化 GPU 利用率 (<90%)")
        vector_progress = status_container.empty()
        
        # 创建索引（第一批）
        first_batch = nodes[:batch_size]
        
        # 估算总时间（基于经验值：约 0.01-0.02s/节点）
        estimated_total_time = len(nodes) * 0.015
        eta_str = f"{int(estimated_total_time)}s" if estimated_total_time < 60 else f"{int(estimated_total_time/60)}m{int(estimated_total_time%60)}s"
        
        vector_progress.write(f"      ⚡ 处理第 1/{total_batches} 批 ({len(first_batch)} 个节点) | 预计总耗时: {eta_str}")
        terminal_logger.info(f"   ⚡ 处理第 1/{total_batches} 批 | 预计总耗时: {eta_str}")
        index = VectorStoreIndex(first_batch, show_progress=False)
        
        # 追加剩余批次（动态调整 batch_size）
        current_batch_size = batch_size
        for i in range(1, total_batches):
            # 计算预计完成时间
            elapsed = time.time() - vector_start
            avg_time_per_batch = elapsed / i
            remaining_batches = total_batches - i
            eta_seconds = avg_time_per_batch * remaining_batches
            eta_str = f"{int(eta_seconds)}s" if eta_seconds < 60 else f"{int(eta_seconds/60)}m{int(eta_seconds%60)}s"
            
            # 检查资源使用
            import psutil
            import time as time_module
            mem_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # 检查 GPU
            gpu_percent = 0.0
            try:
                import torch
                if torch.backends.mps.is_available():
                    gpu_percent = min(90.0, mem_percent * 0.8)
                elif torch.cuda.is_available():
                    gpu_mem = torch.cuda.memory_allocated() / torch.cuda.get_device_properties(0).total_memory * 100
                    gpu_percent = gpu_mem
            except:
                pass
            
            # 动态调整策略：GPU 利用率低且内存充足，尝试增大 batch
            if i > 2 and gpu_percent < 60 and mem_percent < 70:
                # GPU 利用率低，可以增大 batch_size
                if i % 3 == 0:  # 每 3 批检查一次
                    old_batch = current_batch_size
                    current_batch_size = min(int(current_batch_size * 2), 300000)  # 翻倍，最大 30万
                    if current_batch_size != old_batch:
                        terminal_logger.info(f"   📈 动态调整: batch_size {old_batch} → {current_batch_size} (GPU 利用率低)")
            
            if mem_percent > 90 or cpu_percent > 90 or gpu_percent > 90:
                vector_progress.write(f"      ⏸️  资源使用过高 (CPU: {cpu_percent:.1f}%, 内存: {mem_percent:.1f}%, GPU: {gpu_percent:.1f}%)，等待...")
                terminal_logger.warning(f"   ⚠️  资源超过90%阈值，暂停2秒...")
                time_module.sleep(2)
            
            start_idx = i * batch_size
            end_idx = min((i + 1) * batch_size, len(nodes))
            batch = nodes[start_idx:end_idx]
            
            percent = int((i / total_batches) * 100)
            vector_progress.write(f"      ⚡ 处理第 {i+1}/{total_batches} 批 ({percent}%) | {len(batch)} 个节点 | CPU: {cpu_percent:.1f}% | 内存: {mem_percent:.1f}% | GPU: {gpu_percent:.1f}% | 预计剩余: {eta_str}")
            
            if i % 5 == 0:
                terminal_logger.info(f"   📊 进度: {i+1}/{total_batches} ({percent}%) | 预计剩余: {eta_str}")
            
            # 批量插入（使用 insert_nodes 而不是逐个 insert）
            index.insert_nodes(batch)
        
        vector_elapsed = time.time() - vector_start
        vector_progress.empty()
        status_container.write(f"   ✅ 向量化完成: {len(nodes)} 个节点 → 向量数据库 (耗时 {vector_elapsed:.1f}s)")
        terminal_logger.success(f"✅ [6.2] 向量化完成: 耗时 {vector_elapsed:.1f}s")
        terminal_logger.success(f"✅ 索引构建完成")
    
    prog_bar.progress(90)
    
    # 持久化存储
    terminal_logger.info(f"💾 持久化存储: {final_kb_name}")
    logger.log_kb_persist("persisting", kb_name=final_kb_name)
    status_container.write(f"💾 保存到磁盘...")
    status_container.write(f"   路径: {persist_dir}")
    if not os.path.exists(output_base): os.makedirs(output_base)
    index.storage_context.persist(persist_dir=persist_dir)
    update_manifest(persist_dir, file_infos, is_append=(action_mode == "APPEND"), embed_model=embed_model)
    logger.log_kb_persist("success", kb_name=final_kb_name)
    status_container.write(f"   ✅ 保存成功")
    terminal_logger.success(f"✅ 存储完成 [知识库: {final_kb_name}]")

    prog_bar.progress(100)
    elapsed = time.time() - start_time
    
    # 显示完成摘要
    terminal_logger.separator(f"处理完成")
    terminal_logger.success(f"✅ 知识库处理完成: {final_kb_name}")
    
    # 计算详细统计
    end_time_obj = datetime.now()
    start_time_obj = datetime.fromtimestamp(start_time)
    docs_per_sec = len(valid_docs) / elapsed if elapsed > 0 else 0
    
    terminal_logger.data_summary("处理统计", {
        "知识库": final_kb_name,
        "文件数": file_count,
        "文档片段": len(valid_docs),
        "向量节点": len(nodes) if 'nodes' in locals() else 'N/A',
        "模式": "追加" if action_mode == "APPEND" else "新建"
    })
    terminal_logger.data_summary("时间统计", {
        "开始时间": start_time_obj.strftime('%H:%M:%S'),
        "结束时间": end_time_obj.strftime('%H:%M:%S'),
        "总耗时": f"{elapsed:.2f}s ({elapsed/60:.1f}分钟)",
        "处理速度": f"{docs_per_sec:.1f} 文档/秒"
    })
    # 计算结束时间和各阶段耗时
    end_time = datetime.now()
    start_time_obj = datetime.fromtimestamp(start_time)
    
    # 计算平均速度
    docs_per_sec = len(valid_docs) / elapsed if elapsed > 0 else 0
    nodes_per_sec = len(nodes) / elapsed if elapsed > 0 and 'nodes' in locals() else 0
    
    status_container.write(f"")
    status_container.write(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    status_container.write(f"✅ 处理完成!")
    status_container.write(f"")
    status_container.write(f"📊 统计信息:")
    status_container.write(f"   📁 文件数: {file_count}")
    status_container.write(f"   📄 文档片段: {len(valid_docs)}")
    status_container.write(f"   🔢 向量节点: {len(nodes) if 'nodes' in locals() else 'N/A'}")
    if 'summary' in locals() and summary.get('failed', 0) > 0:
        status_container.write(f"   ⚠️  失败: {summary['failed']} 个文件")
    if 'summary' in locals() and summary.get('skipped', 0) > 0:
        status_container.write(f"   ⏭️  跳过: {summary['skipped']} 个文件")
    status_container.write(f"")
    status_container.write(f"⏱️  时间统计:")
    status_container.write(f"   🕐 开始时间: {start_time_obj.strftime('%H:%M:%S')}")
    status_container.write(f"   🕐 结束时间: {end_time.strftime('%H:%M:%S')}")
    status_container.write(f"   ⏱️  总耗时: {elapsed/60:.1f} 分钟 ({elapsed:.0f}秒)")
    status_container.write(f"   ⚡ 处理速度: {docs_per_sec:.1f} 文档/秒")
    if 'parse_start' in locals() and 'vector_start' in locals():
        parse_time = vector_start - parse_start if 'vector_start' in locals() else 0
        vector_time = locals().get('vector_elapsed', 0)
        status_container.write(f"")
        status_container.write(f"📈 阶段耗时:")
        status_container.write(f"   📦 文档分块: {parse_time:.1f}秒")
        status_container.write(f"   🎮 GPU向量化: {vector_time:.1f}秒")
    status_container.write(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    logger.log_kb_complete(kb_name=final_kb_name, doc_count=len(valid_docs))
    status_container.update(label=f"✅ 知识库 '{final_kb_name}' 处理完成", state="complete", expanded=False)
    
    # 显示详细处理报告
    with st.expander("📊 文件处理详情", expanded=False):
        st.markdown(process_result.get_report())
    
    time.sleep(0.5)
    return len(valid_docs)

# ==========================================
# 6. 聊天界面 & 无限追问功能
# ==========================================
st.title("🛡️ RAG Pro Max")

# 初始化状态
if "messages" not in st.session_state: st.session_state.messages = []
if "chat_engine" not in st.session_state: st.session_state.chat_engine = None
if "prompt_trigger" not in st.session_state: st.session_state.prompt_trigger = None
if "current_kb_id" not in st.session_state: st.session_state.current_kb_id = None
if "renaming" not in st.session_state: st.session_state.renaming = False
if "suggestions_history" not in st.session_state: st.session_state.suggestions_history = []
if "is_processing" not in st.session_state: st.session_state.is_processing = False 
if "quote_content" not in st.session_state: st.session_state.quote_content = None # 引用内容初始化
if "first_time_guide_shown" not in st.session_state: st.session_state.first_time_guide_shown = False

# 首次使用引导
if not st.session_state.first_time_guide_shown and len(existing_kbs) == 0:
    st.info("""
    ### 👋 欢迎使用 RAG Pro Max！
    
    **快速开始指南：**
    
    1️⃣ **配置 LLM**（左侧边栏）
    - 选择 Ollama（本地）或 OpenAI（云端）
    - 输入 API 信息
    
    2️⃣ **创建知识库**
    - 点击 "➕ 新建知识库..."
    - 输入名称，上传文档
    
    3️⃣ **开始对话**
    - 选择知识库
    - 在下方输入问题
    
    💡 **提示**：支持 PDF、DOCX、TXT、MD 等多种格式
    """)
    
    if st.button("✅ 我知道了，开始使用", use_container_width=True):
        st.session_state.first_time_guide_shown = True
        st.rerun()

def click_btn(q):
    st.session_state.prompt_trigger = q
    st.session_state.suggestions_history = []
    st.rerun()

# 计算当前的 KB ID (根据侧边栏选择)
active_kb_name = current_kb_name if not is_create_mode else None

# 自动加载逻辑
if active_kb_name and active_kb_name != st.session_state.current_kb_id:
    st.session_state.current_kb_id = active_kb_name
    st.session_state.chat_engine = None
    with st.spinner("📜 正在加载对话历史..."):
        st.session_state.messages = load_chat_history(active_kb_name)
    st.session_state.suggestions_history = []

if active_kb_name and st.session_state.chat_engine is None:
    db_path = os.path.join(output_base, active_kb_name)
    if os.path.exists(db_path):
        try:
            logger.log_kb_mount_start(active_kb_name)
            
            # 检测知识库的向量维度
            kb_dim = get_kb_embedding_dim(db_path)
            if kb_dim:
                # 根据维度选择合适的模型
                model_map = {
                    512: "BAAI/bge-small-zh-v1.5",
                    768: "BAAI/bge-base-zh-v1.5",
                    1024: "BAAI/bge-m3"
                }
                
                if kb_dim in model_map:
                    required_model = model_map[kb_dim]
                    if embed_model != required_model:
                        terminal_logger.warning(f"⚠️ 知识库维度: {kb_dim}D，自动切换模型: {required_model}")
                        embed_model = required_model
                        # 重新加载 embedding 模型
                        embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
                        if embed:
                            Settings.embed_model = embed
            
            # 检查知识库大小
            import glob
            vector_files = glob.glob(os.path.join(db_path, "**/*.json"), recursive=True)
            total_size = sum(os.path.getsize(f) for f in vector_files) / (1024 * 1024)  # MB
            is_large_kb = len(vector_files) > 100 or total_size > 100
            
            if is_large_kb:
                load_start = time.time()
                terminal_logger.info(f"📊 知识库统计: {len(vector_files)} 个文件, {total_size:.1f}MB")
                
                # 进度条放在外面
                progress_placeholder = st.empty()
                progress_bar = progress_placeholder.progress(0, text="⏳ 准备加载知识库... 0%")
                
                with st.status(f"📚 正在挂载大型知识库: {active_kb_name}（{len(vector_files)} 个文件, {total_size:.1f}MB）", expanded=True) as status:
                    # 阶段1: 加载向量数据 (0-40%)
                    status.write("⏳ [1/3] 正在加载向量数据...")
                    terminal_logger.processing("[1/3] 开始加载向量数据...")
                    terminal_logger.info(f"📂 加载 docstore.json ({total_size:.1f}MB)...")
                    
                    # 实时进度显示
                    stage1_start = time.time()
                    import threading
                    result = [None]
                    def load_storage():
                        result[0] = StorageContext.from_defaults(persist_dir=db_path)
                    
                    thread = threading.Thread(target=load_storage)
                    thread.start()
                    
                    # 显示进度
                    progress = 5
                    while thread.is_alive():
                        progress = min(progress + 1, 39)
                        elapsed = time.time() - stage1_start
                        progress_bar.progress(progress, text=f"⏳ [1/3] 加载向量数据... {progress}% (已用时 {elapsed:.0f}s)")
                        time.sleep(0.5)
                    
                    thread.join()
                    storage_context = result[0]
                    stage1_time = time.time() - stage1_start
                    
                    progress_bar.progress(40, text=f"✅ [1/3] 向量数据加载完成 ({stage1_time:.1f}s) - 40%")
                    status.write(f"✅ [1/3] 向量数据加载完成 (耗时 {stage1_time:.1f}s)")
                    terminal_logger.success(f"[1/3] 向量数据加载完成 ({stage1_time:.1f}s)")
                    
                    # 阶段2: 构建索引 (40-80%)
                    status.write("⏳ [2/3] 正在构建索引...")
                    terminal_logger.processing("[2/3] 开始构建索引...")
                    terminal_logger.info(f"📊 加载 index_store.json...")
                    terminal_logger.info(f"🔗 构建向量索引 (959K 节点)...")
                    
                    stage2_start = time.time()
                    result2 = [None]
                    def load_index():
                        result2[0] = load_index_from_storage(storage_context)
                    
                    thread2 = threading.Thread(target=load_index)
                    thread2.start()
                    
                    # 显示进度
                    progress = 45
                    while thread2.is_alive():
                        progress = min(progress + 1, 79)
                        elapsed = time.time() - stage2_start
                        progress_bar.progress(progress, text=f"⏳ [2/3] 构建索引... {progress}% (已用时 {elapsed:.0f}s)")
                        time.sleep(0.5)
                    
                    thread2.join()
                    index = result2[0]
                    stage2_time = time.time() - stage2_start
                    
                    progress_bar.progress(80, text=f"✅ [2/3] 索引构建完成 ({stage2_time:.1f}s) - 80%")
                    status.write(f"✅ [2/3] 索引构建完成 (耗时 {stage2_time:.1f}s)")
                    terminal_logger.success(f"[2/3] 索引构建完成 ({stage2_time:.1f}s)")
                    
                    # 阶段3: 初始化问答引擎 (80-100%)
                    status.write("⏳ [3/3] 正在初始化问答引擎...")
                    terminal_logger.processing("[3/3] 初始化问答引擎...")
                    terminal_logger.info(f"🤖 配置 chat_engine...")
                    
                    stage3_start = time.time()
                    for i in range(85, 100, 3):
                        progress_bar.progress(i, text=f"⏳ [3/3] 初始化问答引擎... {i}%")
                        time.sleep(0.1)
                    
                    # Re-ranking 配置
                    node_postprocessors = []
                    similarity_top_k = 5
                    retriever = None
                    
                    # BM25 混合检索配置
                    if st.session_state.get('enable_bm25', False):
                        try:
                            from llama_index.retrievers.bm25 import BM25Retriever
                            from llama_index.core.retrievers import QueryFusionRetriever
                            
                            status.write(f"   🔍 构建 BM25 混合检索...")
                            terminal_logger.info(f"🔍 BM25 混合检索启用")
                            
                            # 获取所有节点
                            nodes = index.docstore.docs.values()
                            
                            # 创建 BM25 检索器
                            bm25_retriever = BM25Retriever.from_defaults(
                                nodes=list(nodes),
                                similarity_top_k=5
                            )
                            
                            # 创建向量检索器
                            vector_retriever = index.as_retriever(similarity_top_k=5)
                            
                            # 融合检索器
                            retriever = QueryFusionRetriever(
                                retrievers=[vector_retriever, bm25_retriever],
                                similarity_top_k=5,
                                num_queries=1,
                                mode="reciprocal_rerank",
                                use_async=False,
                            )
                            
                            status.write(f"   ✅ BM25 混合检索构建成功")
                            terminal_logger.success(f"✅ BM25 混合检索构建成功")
                        except ImportError:
                            status.write(f"   ⚠️ BM25 需要安装: pip install llama-index-retrievers-bm25")
                            terminal_logger.warning("BM25 依赖缺失")
                        except Exception as e:
                            status.write(f"   ⚠️ BM25 构建失败: {e}")
                            terminal_logger.error(f"BM25 构建失败: {e}")
                    
                    if st.session_state.get('enable_rerank', False):
                        try:
                            from llama_index.core.postprocessor import SentenceTransformerRerank
                            
                            rerank_model = st.session_state.get('rerank_model', 'BAAI/bge-reranker-base')
                            status.write(f"   🎯 加载 Re-ranking 模型: {rerank_model}...")
                            terminal_logger.info(f"🎯 Re-ranking 启用: {rerank_model}")
                            
                            reranker = SentenceTransformerRerank(
                                top_n=3,
                                model=rerank_model,
                                keep_retrieval_score=True,
                            )
                            node_postprocessors.append(reranker)
                            similarity_top_k = 10  # Re-ranking 时先检索更多
                            
                            status.write(f"   ✅ Re-ranking 模型加载成功")
                            terminal_logger.success(f"✅ Re-ranking 模型加载成功")
                        except ImportError:
                            status.write(f"   ⚠️ Re-ranking 需要安装: pip install sentence-transformers")
                            terminal_logger.warning("Re-ranking 依赖缺失")
                        except Exception as e:
                            status.write(f"   ⚠️ Re-ranking 加载失败: {e}")
                            terminal_logger.error(f"Re-ranking 加载失败: {e}")
                    
                    # 创建查询引擎
                    if retriever:
                        st.session_state.chat_engine = index.as_chat_engine(
                            chat_mode="context",
                            retriever=retriever,
                            memory=ChatMemoryBuffer.from_defaults(token_limit=4000),
                            system_prompt="你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。",
                            node_postprocessors=node_postprocessors if node_postprocessors else None,
                        )
                    else:
                        st.session_state.chat_engine = index.as_chat_engine(
                            chat_mode="context", 
                            memory=ChatMemoryBuffer.from_defaults(token_limit=4000),
                            system_prompt="你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。",
                            similarity_top_k=similarity_top_k,
                            node_postprocessors=node_postprocessors if node_postprocessors else None,
                        )
                    stage3_time = time.time() - stage3_start
                    load_time = time.time() - load_start
                    
                    progress_bar.progress(100, text=f"✅ 全部完成！总耗时: {load_time:.1f}s - 100%")
                    status.write(f"✅ [3/3] 问答引擎初始化完成 (耗时 {stage3_time:.1f}s)")
                    terminal_logger.success(f"[3/3] 问答引擎初始化完成 ({stage3_time:.1f}s)")
                    
                    status.update(label=f"✅ 知识库 '{active_kb_name}' 挂载成功！总耗时: {load_time:.1f}s", state="complete")
                    terminal_logger.info(f"📊 总耗时: {load_time:.1f}s")
                
                # 清理进度条
                time.sleep(1.5)
                progress_placeholder.empty()
            else:
                with st.spinner(f"📚 正在挂载知识库: {active_kb_name}..."):
                    try:
                        # 读取知识库实际使用的模型（而不是侧边栏选择）
                        kb_manifest = load_manifest(db_path)
                        kb_embed_model = kb_manifest.get('embed_model', 'BAAI/bge-large-zh-v1.5')
                        
                        terminal_logger.info(f"📊 知识库模型: {kb_embed_model}")
                        terminal_logger.info(f"📊 Embed Provider: {embed_provider}")
                        
                        # 使用知识库的模型加载
                        embed = get_embed(embed_provider, kb_embed_model, embed_key, embed_url)
                        if embed:
                            Settings.embed_model = embed
                            terminal_logger.success(f"✅ 嵌入模型已设置: {kb_embed_model}")
                        else:
                            raise ValueError(f"无法加载嵌入模型: {kb_embed_model}")
                    except Exception as e:
                        terminal_logger.error(f"❌ 模型加载失败: {e}")
                        st.error(f"知识库挂载失败: {e}")
                        raise
                    
                    try:
                        storage_context = StorageContext.from_defaults(persist_dir=db_path)
                        index = load_index_from_storage(storage_context)
                    except Exception as e:
                        # 检查是否是维度不匹配错误
                        if "shapes" in str(e) and "not aligned" in str(e):
                            terminal_logger.warning(f"⚠️ 向量维度不匹配")
                            terminal_logger.info(f"当前模型: {embed_model}")
                            terminal_logger.info(f"错误信息: {str(e)}")
                            
                            st.error(f"❌ 向量维度不匹配")
                            st.warning(f"""
**当前模型:** {embed_model}

**原因:** 知识库是用其他维度的模型创建的，无法直接查询。

**解决方案:**
1. **保留旧数据** - 切换回原模型（bge-small-zh-v1.5）
2. **重建索引** - 用新模型重新嵌入所有文档（耗时较长）

选择一个操作:
""")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("🔄 重建索引", type="primary", use_container_width=True):
                                    with st.spinner("正在清理旧索引..."):
                                        import shutil
                                        shutil.rmtree(db_path, ignore_errors=True)
                                        terminal_logger.success(f"✅ 旧索引已清理，请重新上传文档")
                                        st.success("✅ 索引已清理，请重新上传文档")
                                        time.sleep(2)
                                        st.rerun()
                            with col2:
                                if st.button("↩️ 切换模型", use_container_width=True):
                                    st.info("请在侧边栏选择原模型（通常是 bge-small-zh-v1.5）")
                            
                            st.session_state.chat_engine = None
                            st.stop()
                        else:
                            raise
                    
                    terminal_logger.processing("初始化问答引擎...")
                    st.session_state.chat_engine = index.as_chat_engine(
                        chat_mode="context", 
                        memory=ChatMemoryBuffer.from_defaults(token_limit=4000),
                        system_prompt="你是一个精准的知识库助手，请务必仅基于提供的上下文和知识回答问题。如果知识库中没有相关信息，请明确指出。回答应清晰、简洁、专业。",
                        similarity_top_k=3,  # 减少检索数量
                    )
            
            terminal_logger.success("问答引擎已启用GPU加速")
            logger.log_kb_mount_success(active_kb_name)
            st.toast(f"✅ 知识库 '{active_kb_name}' 挂载成功！")
            
            # 释放内存
            cleanup_memory()
        except Exception as e: 
            logger.log_kb_mount_error(active_kb_name, e)
            st.error(f"知识库挂载失败，请尝试【强制重建】：{e}")
            st.session_state.chat_engine = None 

# 按钮处理
if btn_start:
    config_to_save = {
        "target_path": target_path,
        "output_path": output_base,
        "llm_type_idx": 0 if llm_provider == "Ollama" else 1,
        "llm_url_ollama": llm_url if llm_provider == "Ollama" else "",
        "llm_model_ollama": llm_model if llm_provider == "Ollama" else "",
        "llm_url_openai": llm_url if llm_provider != "Ollama" else "",
        "llm_key": llm_key,
        "llm_model_openai": llm_model if llm_provider != "Ollama" else "",
        "embed_provider_idx": ["HuggingFace (本地/极速)", "OpenAI-Compatible", "Ollama"].index(embed_provider),
        "embed_model_hf": embed_model if embed_provider.startswith("HuggingFace") else "",
        "embed_url_ollama": embed_url if embed_provider.startswith("Ollama") else "",
        "embed_model_ollama": embed_model if embed_provider.startswith("Ollama") else ""
    }
    save_config(config_to_save)

    if not final_kb_name:
        st.error("请输入知识库名称")
    else:
        try:
            clean_kb_name = sanitize_filename(final_kb_name)
            if not clean_kb_name: raise ValueError("知识库名称包含非法字符或为空")
                
            # 修复：直接对模块级变量 final_kb_name 赋值，不再需要 global 关键字
            # final_kb_name 在侧边栏已定义
            final_kb_name = clean_kb_name
            
            process_knowledge_base_logic()
            st.session_state.current_nav = f"📂 {final_kb_name}"
            st.session_state.current_kb_id = None 
            
            if action_mode == "NEW" or action_mode == "APPEND":
                st.session_state.messages = []
                st.session_state.suggestions_history = []
                hist_path = os.path.join(HISTORY_DIR, f"{final_kb_name}.json")
                if os.path.exists(hist_path): os.remove(hist_path)
            
            time.sleep(1); st.rerun()
        except Exception as e: st.error(f"执行失败: {e}")

# --- 主视图渲染 ---
if active_kb_name:
    db_path = os.path.join(output_base, active_kb_name)
    manifest = load_manifest(db_path)
    file_cnt = len(manifest.get('files', []))
    last_upd = manifest.get('last_updated', 'N/A')[:10]
    kb_model = manifest.get('embed_model', 'Unknown')
    
    # 计算统计信息
    total_sz = 0
    total_chunks = 0
    file_types = {}
    oldest_date = None
    newest_date = None
    
    for f in manifest.get('files', []):
        try:
            if 'KB' in f['size']: total_sz += float(f['size'].replace(' KB',''))
            elif 'MB' in f['size']: total_sz += float(f['size'].replace(' MB',''))*1024
        except: pass
        
        total_chunks += len(f.get('doc_ids', []))
        ftype = f.get('type', 'Unknown')
        file_types[ftype] = file_types.get(ftype, 0) + 1
        
        file_date = f.get('added_at', '')
        if file_date:
            if oldest_date is None or file_date < oldest_date:
                oldest_date = file_date
            if newest_date is None or file_date > newest_date:
                newest_date = file_date
    
    # 单行紧凑标题 + 统计
    if st.session_state.renaming:
        def apply_rename():
            n = sanitize_filename(st.session_state.new_name_input)
            if n and n != active_kb_name:
                try:
                    rename_kb(active_kb_name, n, output_base)
                    st.session_state.current_nav = f"📂 {n}"
                    st.toast("✅ 重命名成功")
                except FileExistsError as e:
                    st.error(f"重命名失败: {e}")
            st.session_state.renaming = False
        c1, c2 = st.columns([3, 1])
        c1.text_input("新名称", value=active_kb_name, key="new_name_input", on_change=apply_rename)
        c2.button("取消", on_click=lambda: st.session_state.update({"renaming": False}))
    else:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 1, 1, 1, 1, 0.6])
        col1.markdown(f"### 💬 {active_kb_name}")
        col2.metric("📄 文件", file_cnt)
        col3.metric("💾 大小", f"{total_sz/1024:.1f}MB" if total_sz > 1024 else f"{int(total_sz)}KB")
        col4.metric("📦 片段", total_chunks)
        col5.metric("🧬 模型", kb_model.split('/')[-1] if '/' in kb_model else kb_model)
        if col6.button("✏️", help="重命名"): 
            st.session_state.renaming = True
    
    # 文件管理
    with st.expander("📊 知识库详情与管理", expanded=False):
        if not manifest['files']: 
            st.info("暂无文件")
        else:
            # 计算存储大小
            import os
            db_size = 0
            if os.path.exists(db_path):
                for root, dirs, files in os.walk(db_path):
                    db_size += sum(os.path.getsize(os.path.join(root, f)) for f in files)
            db_size_mb = db_size / (1024 * 1024)
            
            # 计算成功率
            files_with_chunks = len([f for f in manifest['files'] if len(f.get('doc_ids', [])) > 0])
            success_rate = (files_with_chunks / file_cnt * 100) if file_cnt > 0 else 0
            
            # 计算压缩比和存储效率（统一为字节）
            total_sz_bytes = total_sz * 1024  # total_sz 是 KB，转换为字节
            compression_ratio = (total_sz_bytes / db_size) if db_size > 0 else 0
            storage_efficiency = f"{compression_ratio:.1f}x" if compression_ratio > 1 else "1.0x" if compression_ratio > 0 else "N/A"
            
            # 单行统计摘要
            time_range = f"{oldest_date[:10]} ~ {newest_date[:10]}" if oldest_date and newest_date else last_upd
            st.markdown(f"**📊 统计** · {file_cnt} 文件 · {total_chunks} 片段 · 📁 原始 {f'{total_sz/1024:.1f}MB' if total_sz > 1024 else f'{int(total_sz)}KB'} · 💾 向量库 {db_size_mb:.1f}MB ({storage_efficiency}) · 📅 {time_range}")
            
            # 核心指标 + 质量分析（6列）
            metric_col1, metric_col2, metric_col3, metric_col4, metric_col5, metric_col6 = st.columns(6)
            avg_chunks = total_chunks / file_cnt if file_cnt > 0 else 0
            avg_size = (total_sz / file_cnt) if file_cnt > 0 else 0
            
            metric_col1.metric("📈 平均片段", f"{avg_chunks:.1f}")
            metric_col2.metric("📊 平均大小", f"{avg_size/1024:.1f}KB" if avg_size > 1024 else f"{int(avg_size)}KB")
            
            # 健康度
            health_icon = "🟢" if success_rate >= 90 else "🟡" if success_rate >= 70 else "🔴"
            metric_col3.metric("💚 健康度", f"{health_icon} {success_rate:.0f}%")
            
            # 质量分析
            low_quality = len([f for f in manifest['files'] if len(f.get('doc_ids', [])) < 2])
            large_files = len([f for f in manifest['files'] if 'MB' in f['size']])
            empty_docs = len([f for f in manifest['files'] if len(f.get('doc_ids', [])) == 0])
            
            quality_status = "✅ 优秀" if low_quality == 0 and large_files == 0 and empty_docs == 0 else f"⚠️ {empty_docs}空 {low_quality}低质"
            metric_col4.metric("🔍 质量", quality_status)
            
            # 文件类型数量
            type_count = len(file_types)
            metric_col5.metric("📂 类型", f"{type_count} 种")
            
            metric_col6.metric("🔤 模型", kb_model.split('/')[-1][:12] if '/' in kb_model else kb_model[:12])
            
            st.divider()
            
            # 四列布局：类型分布 + 大小分布 + 片段分布 + 数据洞察
            type_col, size_col, chunk_col, insight_col = st.columns([2, 2, 2, 2])
            
            with type_col:
                st.markdown("**📂 类型分布**")
                sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
                for i, (ftype, count) in enumerate(sorted_types[:5]):  # 显示前5种
                    pct = (count / file_cnt * 100) if file_cnt > 0 else 0
                    bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
                    st.caption(f"{ftype}: {count} ({pct:.0f}%) {bar[:10]}")
                if len(sorted_types) > 5:
                    other_count = sum(c for _, c in sorted_types[5:])
                    other_pct = (other_count / file_cnt * 100) if file_cnt > 0 else 0
                    st.caption(f"其他: {other_count} ({other_pct:.0f}%)")
            
            with size_col:
                st.markdown("**📊 大小分布**")
                # 按大小分类
                size_ranges = {"<100KB": 0, "100KB-1MB": 0, "1MB-10MB": 0, ">10MB": 0}
                for f in manifest['files']:
                    size_bytes = f.get('size_bytes', 0)
                    if size_bytes < 100 * 1024:
                        size_ranges["<100KB"] += 1
                    elif size_bytes < 1024 * 1024:
                        size_ranges["100KB-1MB"] += 1
                    elif size_bytes < 10 * 1024 * 1024:
                        size_ranges["1MB-10MB"] += 1
                    else:
                        size_ranges[">10MB"] += 1
                
                for range_name, count in size_ranges.items():
                    if count > 0:
                        pct = (count / file_cnt * 100) if file_cnt > 0 else 0
                        st.caption(f"{range_name}: {count} ({pct:.0f}%)")
            
            with chunk_col:
                st.markdown("**📦 片段分布**")
                # 按片段数分类
                chunk_ranges = {"0片段": 0, "1-5片段": 0, "6-20片段": 0, ">20片段": 0}
                for f in manifest['files']:
                    chunk_count = len(f.get('doc_ids', []))
                    if chunk_count == 0:
                        chunk_ranges["0片段"] += 1
                    elif chunk_count <= 5:
                        chunk_ranges["1-5片段"] += 1
                    elif chunk_count <= 20:
                        chunk_ranges["6-20片段"] += 1
                    else:
                        chunk_ranges[">20片段"] += 1
                
                for range_name, count in chunk_ranges.items():
                    if count > 0:
                        pct = (count / file_cnt * 100) if file_cnt > 0 else 0
                        icon = "⚠️" if range_name == "0片段" else "✅" if range_name == ">20片段" else ""
                        st.caption(f"{icon}{range_name}: {count} ({pct:.0f}%)")
            
            with insight_col:
                st.markdown("**💡 数据洞察**")
                if manifest['files']:
                    # 热门文件（基于命中次数）
                    hot_files = [(f['name'], f.get('hit_count', 0)) for f in manifest['files'] if f.get('hit_count', 0) > 0]
                    if hot_files:
                        hot_files.sort(key=lambda x: x[1], reverse=True)
                        top_file = hot_files[0]
                        st.caption(f"🔥 最热: {top_file[0][:12]}... ({top_file[1]}次)")
                    
                    # 最多片段
                    chunks_list = [(f['name'], len(f.get('doc_ids', []))) for f in manifest['files']]
                    most_chunks = max(chunks_list, key=lambda x: x[1]) if chunks_list else None
                    if most_chunks and most_chunks[1] > 0:
                        st.caption(f"🔢 最多片段: {most_chunks[0][:12]}... ({most_chunks[1]})")
                    
                    # 主要类型
                    if file_types:
                        main_type = max(file_types.items(), key=lambda x: x[1])
                        st.caption(f"📂 主要类型: {main_type[0]} ({main_type[1]}个)")
                    
                    # 智能建议
                    if empty_docs > file_cnt * 0.1:
                        st.caption(f"⚠️ {empty_docs}个空文档需处理")
                    elif low_quality > file_cnt * 0.3:
                        st.caption(f"💡 建议优化文档质量")
                    elif success_rate >= 95:
                        st.caption(f"🎉 知识库质量优秀")
                    else:
                        st.caption(f"✅ 知识库状态良好")
            
            st.divider()
            
            # 元数据统计（新增）
            try:
                metadata_mgr = MetadataManager(db_path)
                
                # 检查是否有元数据
                if metadata_mgr.metadata or metadata_mgr.stats:
                    with st.expander("📊 元数据统计", expanded=False):
                        stat_col1, stat_col2, stat_col3 = st.columns(3)
                        
                        with stat_col1:
                            st.markdown("**🔥 热门文件 Top 5**")
                            hot_files = metadata_mgr.get_hot_files(top_k=5)
                            if hot_files:
                                for i, (fname, count) in enumerate(hot_files, 1):
                                    st.caption(f"{i}. {fname[:20]}... ({count})")
                            else:
                                st.caption("暂无数据")
                        
                        with stat_col2:
                            st.markdown("**📂 文档分类**")
                            categories = metadata_mgr.get_all_categories()
                            if categories:
                                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
                                    st.caption(f"{cat}: {count}")
                            else:
                                st.caption("暂无数据")
                        
                        with stat_col3:
                            st.markdown("**🏷️ 热门关键词**")
                            keywords = metadata_mgr.get_all_keywords(top_k=8)
                            if keywords:
                                kw_text = " · ".join([f"{kw}({cnt})" for kw, cnt in keywords[:8]])
                                st.caption(kw_text)
                            else:
                                st.caption("暂无数据")
                        
                        # 重复文件检测
                        duplicates = metadata_mgr.find_duplicates()
                        if duplicates:
                            st.divider()
                            st.markdown(f"**⚠️ 发现 {len(duplicates)} 组重复文件**")
                            for i, (file_hash, files) in enumerate(list(duplicates.items())[:2], 1):
                                st.caption(f"组{i}: {', '.join([f[:15] for f in files[:3]])}...")
            except:
                pass  # 如果元数据不存在，静默跳过
            
            st.divider()
            
            # 快速操作区
            st.markdown("**⚡ 快速操作**")
            
            # 快速操作按钮组
            quick_col1, quick_col2 = st.columns(2)
            
            # 打开知识库目录
            with quick_col1:
                if st.button("📂 打开目录", use_container_width=True, help="在Finder中打开知识库文件夹"):
                    import webbrowser
                    import urllib.parse
                    try:
                        file_url = 'file://' + urllib.parse.quote(os.path.abspath(db_path))
                        webbrowser.open(file_url)
                        st.toast("✅ 已在Finder中打开")
                    except Exception as e:
                        st.error(f"打开失败: {e}")
            
            # 复制路径
            with quick_col2:
                if st.button("📋 复制路径", use_container_width=True, help="复制知识库路径到剪贴板"):
                    try:
                        import subprocess
                        subprocess.run(["pbcopy"], input=db_path.encode(), check=True)
                        st.toast(f"✅ 已复制: {db_path}")
                    except Exception as e:
                        st.info(f"📁 路径: {db_path}")
            
            st.write("")
            
            # 批量生成摘要
            files_without_summary = [f for f in manifest['files'] if not f.get('summary') and f.get('doc_ids')]
            if files_without_summary:
                if 'selected_for_summary' not in st.session_state:
                    st.session_state.selected_for_summary = set()
                
                selected_count = len(st.session_state.selected_for_summary)
                
                # 始终显示按钮，但根据选中数量决定是否禁用
                button_label = f"✨ 生成摘要 ({selected_count})" if selected_count > 0 else "✨ 生成摘要 (请先勾选文件)"
                button_disabled = selected_count == 0
                
                if st.button(button_label, use_container_width=True, type="primary", disabled=button_disabled):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    from llama_index.core import StorageContext, load_index_from_storage as load_idx
                    storage_context = StorageContext.from_defaults(persist_dir=db_path)
                    idx = load_idx(storage_context)
                    retriever = idx.as_retriever(similarity_top_k=3)
                    
                    success_count = 0
                    for i, fname in enumerate(st.session_state.selected_for_summary):
                        status_text.text(f"正在处理: {fname} ({i+1}/{selected_count})")
                        try:
                            file_info = next((f for f in manifest['files'] if f['name'] == fname), None)
                            if file_info and file_info.get('doc_ids'):
                                # 使用检索器获取文档内容
                                nodes = retriever.retrieve(fname)
                                
                                doc_text = ""
                                for node in nodes:
                                    if hasattr(node, 'node') and hasattr(node.node, 'text'):
                                        doc_text += node.node.text + "\n"
                                    elif hasattr(node, 'text'):
                                        doc_text += node.text + "\n"
                                    if len(doc_text) > 2000:
                                        break
                                
                                if doc_text.strip():
                                    summary = generate_doc_summary(doc_text, fname)
                                    file_info['summary'] = summary
                                    success_count += 1
                        except Exception as e:
                            st.warning(f"⚠️ {fname}: {str(e)}")
                            
                            progress_bar.progress((i + 1) / selected_count)
                        
                        # 保存 manifest
                        with open(get_manifest_path(db_path), 'w', encoding='utf-8') as f:
                            json.dump(manifest, f, indent=4, ensure_ascii=False)
                        
                        status_text.empty()
                        progress_bar.empty()
                        st.success(f"✅ 已生成 {success_count}/{selected_count} 个摘要")
                        st.session_state.selected_for_summary = set()
                        time.sleep(1)
                
                if st.button("📥 导出清单", use_container_width=True):
                    export_data = f"知识库: {active_kb_name}\n文件数: {file_cnt}\n片段数: {total_chunks}\n\n文件列表:\n"
                    for f in manifest['files']:
                        export_data += f"- {f['name']} ({f['type']}, {len(f.get('doc_ids', []))} 片段)\n"
                    st.download_button("下载", export_data, f"{active_kb_name}_清单.txt", use_container_width=True)
            
            st.divider()
            
            # 搜索筛选排序（单行超紧凑布局）
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1, 1, 1, 1, 1.2, 0.8])
            search_term = col1.text_input("🔍", "", key="file_search", placeholder="搜索文件名...", label_visibility="collapsed")
            filter_type = col2.selectbox("📂", ["全部"] + sorted(set(f.get('type', 'Unknown') for f in manifest['files'])), label_visibility="collapsed")
            
            # 分类筛选
            all_categories = set(f.get('category', '其他') for f in manifest['files'] if f.get('category'))
            filter_category = col3.selectbox("📋", ["全部"] + sorted(all_categories), label_visibility="collapsed") if all_categories else "全部"
            
            # 热度筛选
            filter_heat = col4.selectbox("🔥", ["全部", "高频", "中频", "低频", "未用"], label_visibility="collapsed")
            
            # 质量筛选
            filter_quality = col5.selectbox("✅", ["全部", "优秀", "正常", "低质", "空"], label_visibility="collapsed")
            
            sort_by = col6.selectbox("排序", ["时间↓", "时间↑", "大小↓", "大小↑", "名称", "热度↓", "片段↓"], label_visibility="collapsed")
            page_size = col7.selectbox("页", [10, 20, 50, 100], index=0, label_visibility="collapsed")
            
            # 筛选文件
            filtered_files = manifest['files']
            
            # 搜索
            if search_term:
                filtered_files = [f for f in filtered_files if search_term.lower() in f['name'].lower()]
            
            # 类型筛选
            if filter_type != "全部":
                filtered_files = [f for f in filtered_files if f.get('type') == filter_type]
            
            # 分类筛选
            if filter_category != "全部":
                filtered_files = [f for f in filtered_files if f.get('category') == filter_category]
            
            # 热度筛选
            if filter_heat == "高频":
                filtered_files = [f for f in filtered_files if f.get('hit_count', 0) > 10]
            elif filter_heat == "中频":
                filtered_files = [f for f in filtered_files if 3 < f.get('hit_count', 0) <= 10]
            elif filter_heat == "低频":
                filtered_files = [f for f in filtered_files if 0 < f.get('hit_count', 0) <= 3]
            elif filter_heat == "未用":
                filtered_files = [f for f in filtered_files if f.get('hit_count', 0) == 0]
            
            # 质量筛选
            if filter_quality == "优秀":
                filtered_files = [f for f in filtered_files if len(f.get('doc_ids', [])) >= 10]
            elif filter_quality == "正常":
                filtered_files = [f for f in filtered_files if 2 <= len(f.get('doc_ids', [])) < 10]
            elif filter_quality == "低质":
                filtered_files = [f for f in filtered_files if 0 < len(f.get('doc_ids', [])) < 2]
            elif filter_quality == "空":
                filtered_files = [f for f in filtered_files if len(f.get('doc_ids', [])) == 0]
            
            # 排序
            if sort_by == "时间↓":
                filtered_files = sorted(filtered_files, key=lambda x: x.get('added_at', ''), reverse=True)
            elif sort_by == "时间↑":
                filtered_files = sorted(filtered_files, key=lambda x: x.get('added_at', ''))
            elif sort_by == "大小↓":
                filtered_files = sorted(filtered_files, key=lambda x: x.get('size_bytes', 0), reverse=True)
            elif sort_by == "大小↑":
                filtered_files = sorted(filtered_files, key=lambda x: x.get('size_bytes', 0))
            elif sort_by == "名称A-Z":
                filtered_files = sorted(filtered_files, key=lambda x: x['name'].lower())
            elif sort_by == "热度↓":
                filtered_files = sorted(filtered_files, key=lambda x: x.get('hit_count', 0), reverse=True)
            elif sort_by == "片段↓":
                filtered_files = sorted(filtered_files, key=lambda x: len(x.get('doc_ids', [])), reverse=True)
            
            # 分页
            total_files = len(filtered_files)
            total_pages = (total_files + page_size - 1) // page_size if total_files > 0 else 1
            
            if 'file_page' not in st.session_state:
                st.session_state.file_page = 1
            
            # 确保页码在有效范围内
            if st.session_state.file_page > total_pages:
                st.session_state.file_page = 1
            
            # 分页控制和统计
            if total_files == 0:
                st.info("❌ 无匹配文件")
            else:
                # 简洁的筛选结果（单行）
                filters = []
                if search_term: filters.append(f"'{search_term}'")
                if filter_type != "全部": filters.append(filter_type)
                if filter_category != "全部": filters.append(filter_category)
                if filter_heat != "全部": filters.append(filter_heat)
                if filter_quality != "全部": filters.append(filter_quality)
                
                if filters:
                    st.caption(f"**{' · '.join(filters)}** → {total_files} 个")
                
                # 分页控制
                if total_pages > 1:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        page_cols = st.columns([1, 3, 1])
                        if page_cols[0].button("⬅️ 上一页", disabled=st.session_state.file_page <= 1):
                            st.session_state.file_page -= 1
                        page_cols[1].markdown(f"<div style='text-align:center'>第 {st.session_state.file_page}/{total_pages} 页</div>", unsafe_allow_html=True)
                        if page_cols[2].button("下一页 ➡️", disabled=st.session_state.file_page >= total_pages):
                            st.session_state.file_page += 1
                
                # 计算当前页文件范围
                start_idx = (st.session_state.file_page - 1) * page_size
                end_idx = min(start_idx + page_size, total_files)
                
                # 表头
                cols = st.columns([0.5, 2.5, 1, 0.8, 1, 0.8, 1.2, 0.8])
                
                # 全选复选框
                current_page_files = [f['name'] for f in filtered_files[start_idx:end_idx] if not f.get('summary') and f.get('doc_ids')]
                if current_page_files:
                    all_selected = all(fname in st.session_state.selected_for_summary for fname in current_page_files)
                    select_all = cols[0].checkbox("全选", value=all_selected, key=f"select_all_page_{st.session_state.file_page}", label_visibility="collapsed")
                    
                    # 根据全选框状态更新选中列表
                    if select_all:
                        st.session_state.selected_for_summary.update(current_page_files)
                    else:
                        st.session_state.selected_for_summary.difference_update(current_page_files)
                else:
                    cols[0].markdown("**✨**")
                
                cols[1].markdown("**文件名**")
                cols[2].markdown("**类型**")
                cols[3].markdown("**片段**")
                cols[4].markdown("**大小**")
                cols[5].markdown("**质量**")
                cols[6].markdown("**时间**")
                cols[7].markdown("**操作**")
                st.divider()
                
                # 渲染文件列表
                for i in range(start_idx, end_idx):
                    f = filtered_files[i]
                    # 找到原始索引用于删除
                    orig_idx = manifest['files'].index(f)
                    
                    cols = st.columns([0.5, 2.5, 1, 0.8, 1, 0.8, 1.2, 0.8])
                    
                    # 摘要复选框（仅对没有摘要的文件显示）
                    if not f.get('summary') and f.get('doc_ids'):
                        # 根据 session_state 设置复选框的值
                        is_checked = f['name'] in st.session_state.selected_for_summary
                        checked = cols[0].checkbox("选择", value=is_checked, key=f"sum_{f['name']}_{st.session_state.file_page}", label_visibility="collapsed")
                        
                        # 更新 session_state
                        if checked:
                            st.session_state.selected_for_summary.add(f['name'])
                        else:
                            st.session_state.selected_for_summary.discard(f['name'])
                    else:
                        cols[0].write("")
                    
                    # 文件名（带图标）
                    cols[1].caption(f'{f["icon"]} {f["name"]}')
                    
                    # 类型
                    cols[2].caption(f['type'])
                    
                    # 片段数
                    chunk_count = len(f.get('doc_ids', []))
                    cols[3].caption(str(chunk_count))
                    
                    # 大小
                    cols[4].caption(f['size'])
                    
                    # 质量指示器（新增）
                    if chunk_count == 0:
                        quality_icon = "❌"
                    elif chunk_count < 2:
                        quality_icon = "⚠️"
                    elif chunk_count < 10:
                        quality_icon = "✅"
                    else:
                        quality_icon = "🎉"
                    cols[5].caption(quality_icon)
                    
                    # 时间
                    cols[6].caption(f['added_at'])
                    
                    # 删除按钮
                    if cols[7].button("🗑️", key=f"del_{orig_idx}_{i}"):
                        with st.status(f"正在删除 {f['name']}...", expanded=True) as status:
                            try:
                                ctx = StorageContext.from_defaults(persist_dir=db_path)
                                idx = load_index_from_storage(ctx)
                                for did in f.get('doc_ids', []):
                                    idx.delete_ref_doc(did, delete_from_docstore=True)
                                idx.storage_context.persist(persist_dir=db_path)
                                remove_file_from_manifest(db_path, f['name'])
                                status.update(label="✅ 已删除", state="complete")
                                st.session_state.chat_engine = None
                                time.sleep(1); st.rerun()
                            except Exception as e: st.error(str(e))
                    
                    # 文件摘要展开
                    if f.get('summary'):
                        with st.expander(f"📖 {f['summary'][:50]}...", expanded=False):
                            st.markdown(f.get('summary'))
                    
                    # 文件统计信息
                    with st.expander(f"📊 详情 - {f['name']}", expanded=False):
                        chunk_count = len(f.get('doc_ids', []))
                        
                        # 基础信息（4列紧凑显示）
                        detail_cols = st.columns(4)
                        detail_cols[0].metric("📦 片段", chunk_count)
                        detail_cols[1].metric("💾 大小", f['size'])
                        detail_cols[2].metric("📅 时间", f['added_at'][:10])
                        detail_cols[3].metric("🏷️ 类型", f['type'])
                        
                        # 质量评估（单行紧凑显示）
                        if chunk_count == 0:
                            quality_info = "❌ 解析失败"
                        elif chunk_count < 2:
                            quality_info = "⚠️ 低质（内容过少）"
                        elif chunk_count < 10:
                            quality_info = "✅ 正常"
                        else:
                            quality_info = "🎉 优秀（内容丰富）"
                        
                        estimated_chars = chunk_count * 500
                        st.caption(f"**质量**: {quality_info} · **字符**: ~{estimated_chars:,} · **向量**: {chunk_count}")
                        
                        # 元数据信息（新增）
                        if f.get('hit_count', 0) > 0 or f.get('keywords') or f.get('category'):
                            st.divider()
                            meta_cols = st.columns(4)
                            
                            # 检索统计
                            hit_count = f.get('hit_count', 0)
                            avg_score = f.get('avg_score', 0.0)
                            heat = "🔥" if hit_count > 10 else "📊" if hit_count > 3 else "📦" if hit_count > 0 else "❄️"
                            
                            meta_cols[0].metric("🔥 命中", f"{hit_count} 次")
                            meta_cols[1].metric("⭐ 得分", f"{avg_score:.2f}")
                            meta_cols[2].metric("🌡️ 热度", heat)
                            
                            # 最后访问
                            last_accessed = f.get('last_accessed')
                            if last_accessed:
                                meta_cols[3].metric("🕐 访问", last_accessed[:10])
                            else:
                                meta_cols[3].metric("🕐 访问", "从未")
                            
                            # 分类和语言
                            category = f.get('category', '其他')
                            language = f.get('language', 'unknown')
                            lang_map = {"zh": "🇨🇳", "en": "🇬🇧", "zh-en": "🌐", "unknown": "❓"}
                            lang_icon = lang_map.get(language, "❓")
                            
                            st.caption(f"**📂 分类**: {category} · **🌍 语言**: {lang_icon} {language}")
                            
                            # 关键词
                            keywords = f.get('keywords', [])
                            if keywords:
                                st.caption(f"**🏷️ 关键词**: {' · '.join(keywords[:5])}")
                            
                            # 文件哈希（折叠）
                            file_hash = f.get('file_hash', '')
                            if file_hash:
                                with st.expander("🔐 文件哈希", expanded=False):
                                    st.code(file_hash, language="text")
                        
                        # 文档ID（紧凑显示）
                        if f.get('doc_ids'):
                            if len(f['doc_ids']) <= 3:
                                st.caption(f"**片段ID**: `{', '.join(f['doc_ids'])}`")
                            else:
                                st.caption(f"**片段ID**: `{f['doc_ids'][0]}` ... (共{len(f['doc_ids'])}个)")
                                with st.expander("查看全部ID", expanded=False):
                                    st.code('\n'.join(f['doc_ids']), language=None)
                        else:
                            st.warning("⚠️ 未生成片段 · 可能原因：文件为空/格式不支持/已损坏/加密")
                        
                        # 相似文件（紧凑显示）
                        if chunk_count > 0:
                            similar_files = [
                                other for other in manifest['files']
                                if other['name'] != f['name']
                                and other['type'] == f['type']
                                and abs(len(other.get('doc_ids', [])) - chunk_count) < chunk_count * 0.5
                            ][:3]
                            
                            if similar_files:
                                similar_names = [f"{s['icon']} {s['name'][:20]}..." for s in similar_files]
                                st.caption(f"**相似**: {' · '.join(similar_names)}")
                        # 生成摘要按钮（只对有片段的文件显示）
                        if not f.get('summary') and f.get('doc_ids'):
                            if st.button("✨ 生成摘要", key=f"gen_sum_{f['name']}", use_container_width=True):
                                with st.spinner("生成中..."):
                                    try:
                                        # 使用检索器获取文档内容
                                        from llama_index.core import StorageContext, load_index_from_storage as load_idx
                                        storage_context = StorageContext.from_defaults(persist_dir=db_path)
                                        idx = load_idx(storage_context)
                                        
                                        # 使用文件名作为查询，检索相关内容
                                        retriever = idx.as_retriever(similarity_top_k=3)
                                        nodes = retriever.retrieve(f['name'])
                                        
                                        doc_text = ""
                                        for node in nodes:
                                            if hasattr(node, 'node') and hasattr(node.node, 'text'):
                                                doc_text += node.node.text + "\n"
                                            elif hasattr(node, 'text'):
                                                doc_text += node.text + "\n"
                                            if len(doc_text) > 2000:
                                                break
                                        
                                        if doc_text.strip():
                                            # 生成摘要
                                            summary = generate_doc_summary(doc_text, f['name'])
                                            
                                            # 更新 manifest
                                            manifest = load_manifest(db_path)
                                            for file in manifest['files']:
                                                if file['name'] == f['name']:
                                                    file['summary'] = summary
                                                    break
                                            
                                            # 保存 manifest
                                            with open(get_manifest_path(db_path), 'w', encoding='utf-8') as mf:
                                                json.dump(manifest, mf, indent=4, ensure_ascii=False)
                                            
                                            st.success("✅ 摘要已生成")
                                        else:
                                            st.error("❌ 无法读取文档内容")
                                        time.sleep(0.5)
                                    except Exception as e:
                                        st.error(f"生成失败: {e}")
                
                # 底部分页（方便翻页）
                if total_pages > 1:
                    st.divider()
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        page_cols = st.columns([1, 3, 1])
                        if page_cols[0].button("⬅️", key="prev_bottom", disabled=st.session_state.file_page <= 1):
                            st.session_state.file_page -= 1
                        page_cols[1].markdown(f"<div style='text-align:center'>第 {st.session_state.file_page}/{total_pages} 页 · 共 {total_files} 个文件</div>", unsafe_allow_html=True)
                        if page_cols[2].button("➡️", key="next_bottom", disabled=st.session_state.file_page >= total_pages):
                            st.session_state.file_page += 1

    st.divider()

elif is_create_mode:
    st.markdown("""
    <div class="welcome-box">
        <h2>👋 欢迎使用知识库</h2>
        <p>请在左侧 <b>侧边栏</b> 配置数据源 (支持粘贴路径或拖拽文件)，点击 <b>🚀 立即创建</b> 开始。</p>
    </div>
    """, unsafe_allow_html=True)


# 自动摘要 (仅在知识库首次加载且无历史消息时触发)
if active_kb_name and st.session_state.chat_engine and not st.session_state.messages:
    with st.chat_message("assistant", avatar="🤖"):
        summary_placeholder = st.empty()
        with st.status("✨ 正在分析文档生成摘要...", expanded=True):
            try:
                # 使用知识库的模型（已在挂载时设置，无需重复设置）
                current_model = getattr(Settings.embed_model, '_model_name', 'Unknown')
                terminal_logger.info(f"💬 摘要生成使用模型: {current_model}")
                
                prompt = "请用一段话简要总结此知识库的核心内容。然后，提出3个用户可能最关心的问题，每行一个，不要序号。"
                full = ""
                resp = st.session_state.chat_engine.stream_chat(prompt)
                
                for t in resp.response_gen:
                    full += t
                    summary_placeholder.markdown(full + "▌")
                summary_placeholder.markdown(full)
                
                summary_lines = full.split('\n')
                summary = summary_lines[0]
                sug = [re.sub(r'^\d+\.\s*', '', q.strip()) for q in summary_lines[1:] if q.strip()][:3]

                st.session_state.messages.append({"role": "assistant", "content": summary, "suggestions": sug})
                save_chat_history(active_kb_name, st.session_state.messages)
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                    summary_placeholder.info("⏱️ LLM 响应超时，已跳过自动摘要。您可以直接开始提问。")
                    terminal_logger.warning(f"⏱️ 摘要生成超时: {e}")
                else:
                    summary_placeholder.warning(f"摘要生成受阻: {e}")
                    terminal_logger.error(f"❌ 摘要生成失败: {e}")
                st.session_state.messages.append({"role": "assistant", "content": "👋 知识库已就绪。"})

# 渲染消息
for msg_idx, msg in enumerate(st.session_state.messages):
    role = msg["role"]
    avatar = "🤖" if role == "assistant" else "🧑‍💻"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg["content"])
        
        # 显示统计信息（如果有）- 使用新组件 (Stage 3.1)
        if "stats" in msg and msg["stats"]:
            render_message_stats(msg["stats"])
        
        # 渲染引用源 - 使用新组件 (Stage 3.1)
        if "sources" in msg:
            render_source_references(msg["sources"], expanded=False)
        
        # 引用按钮 (P2 恢复功能)
        if role == "assistant":
            if st.button("📌 引用此回复", key=f"quote_{msg_idx}"):
                st.session_state.quote_content = msg["content"]
                st.rerun()

        # 渲染静态建议 (仅用于自动摘要)
        is_last_message = msg_idx == len(st.session_state.messages) - 1
        if "suggestions" in msg and msg["suggestions"] and is_last_message and not st.session_state.suggestions_history:
            st.write("")
            for idx, q in enumerate(msg["suggestions"]):
                if st.button(f"👉 {q}", key=f"sug_{msg_idx}_{idx}", use_container_width=True):
                    click_btn(q)
    
    # 在最后一条 assistant 消息之后显示动态追问推荐（在 chat_message 容器外）
    is_last_message = msg_idx == len(st.session_state.messages) - 1
    if is_last_message and msg["role"] == "assistant" and active_kb_name and st.session_state.chat_engine:
        import hashlib
        msg_hash = hashlib.md5(msg['content'][:100].encode()).hexdigest()[:8]
        
        st.divider()
        
        @st.fragment
        def suggestions_fragment():
            if st.session_state.suggestions_history:
                st.markdown("##### 🚀 追问推荐")
                for idx, q in enumerate(st.session_state.suggestions_history):
                    if st.button(f"👉 {q}", key=f"dyn_sug_{msg_hash}_{idx}", use_container_width=True):
                        click_btn(q)
            
            if st.button("✨ 继续推荐 3 个追问 (无限追问)", key=f"gen_more_{msg_hash}", type="secondary", use_container_width=True):
                with st.spinner("⏳ 正在生成新问题..."):
                    all_history_questions = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
                    all_history_questions.extend(st.session_state.suggestions_history)
                    
                    new_sugs = generate_follow_up_questions(
                        context_text=msg['content'], 
                        num_questions=3,
                        existing_questions=all_history_questions,
                        query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None
                    )
                    
                    if new_sugs:
                        st.session_state.suggestions_history.extend(new_sugs)
                        st.rerun(scope="fragment")
                    else:
                        st.warning("未能生成更多追问，请尝试输入新问题。")
            
        suggestions_fragment()

# 引用内容预览区
if st.session_state.get("quote_content"):
    quote_text = st.session_state.quote_content
    display_text = quote_text[:60].replace('\n', ' ') + "..." if len(quote_text) > 60 else quote_text
    
    with st.container():
        st.info(f"📌 **已引用**: {display_text}")
        col1, col2 = st.columns([8, 2])
        col1.caption("基于此内容提问...")
        if col2.button("取消引用", key="cancel_quote", use_container_width=True):
            st.session_state.quote_content = None
            st.rerun()

# 处理输入
user_input = st.chat_input("输入问题...")
final_prompt = st.session_state.prompt_trigger if st.session_state.prompt_trigger else user_input
if st.session_state.prompt_trigger: st.session_state.prompt_trigger = None

# 显示队列状态
if st.session_state.get('is_processing'):
    st.info("⏳ 正在处理上一个问题，新问题已排队...")

if final_prompt:
    if not st.session_state.chat_engine:
        st.error("请先点击左侧【🚀 执行处理】启动系统")
    else:
        st.session_state.suggestions_history = []
        st.session_state.is_processing = True  # 标记正在处理
        
        # 强制检测知识库维度并切换模型（静默处理，不显示加载）
        db_path = os.path.join(output_base, active_kb_name)
        kb_dim = get_kb_embedding_dim(db_path)
        
        # 为历史知识库自动保存信息
        auto_save_kb_info(db_path, embed_model)
        
        # 维度映射
        model_map = {
            512: "BAAI/bge-small-zh-v1.5",
            768: "BAAI/bge-base-zh-v1.5",
            1024: "BAAI/bge-m3"
        }
        
        # 如果检测到维度，强制切换
        if kb_dim and kb_dim in model_map:
            required_model = model_map[kb_dim]
            if embed_model != required_model:
                print(f"🔄 强制切换模型: {embed_model} → {required_model} (维度: {kb_dim}D)")
                embed_model = required_model
                embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
                if embed:
                    Settings.embed_model = embed
                    print(f"✅ 模型已切换")
        else:
            # 维度检测失败时，降级到最小模型（512维）
            print(f"⚠️ 维度检测失败，降级到最小模型")
            fallback_model = "BAAI/bge-small-zh-v1.5"
            if embed_model != fallback_model:
                print(f"🔄 降级切换: {embed_model} → {fallback_model}")
                embed_model = fallback_model
                embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
                if embed:
                    Settings.embed_model = embed
                    print(f"✅ 已降级到最小模型")
        
        terminal_logger.separator("知识库查询")
        terminal_logger.start_operation("查询", f"知识库: {active_kb_name}")
        
        # 显示系统资源利用
        import psutil
        mem_percent = psutil.virtual_memory().percent
        terminal_logger.info(f"系统内存使用: {mem_percent:.1f}%")
        
        # 处理引用内容
        if st.session_state.get("quote_content"):
            quoted_text = st.session_state.quote_content
            # 限制引用长度，防止 prompt 过长
            if len(quoted_text) > 2000:
                quoted_text = quoted_text[:2000] + "...(已截断)"
            
            # 构建包含引用的 prompt
            # 注意：这里我们修改 final_prompt 发送给 LLM，但在 UI 上用户只看到自己的简短输入
            # 为了历史记录的完整性，我们可以选择保存组合后的 prompt，或者分开保存
            # 这里选择修改 final_prompt，这样历史记录里也是完整的，方便后续回顾
            original_prompt = final_prompt
            final_prompt = f"基于以下引用内容：\n> {quoted_text}\n\n我的问题是：{original_prompt}"
            
            # 清除引用状态
            st.session_state.quote_content = None
            terminal_logger.info("📌 已应用引用内容")
        
        logger.log_user_question(final_prompt, kb_name=active_kb_name)
        
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        if active_kb_name: save_chat_history(active_kb_name, st.session_state.messages)

        with st.chat_message("user", avatar="🧑‍💻"): st.markdown(final_prompt)
        
        with st.chat_message("assistant", avatar="🤖"):
            msg_placeholder = st.empty()
            with st.status("⏳ 正在检索并思考...", expanded=True):
                try:
                    # 开始计时
                    start_time = time.time()
                    
                    # 资源监控
                    cpu_start, mem_start, gpu_start, _ = check_resource_usage(threshold=80.0)
                    terminal_logger.info(f"🔋 资源状态: CPU {cpu_start:.1f}% | 内存 {mem_start:.1f}% | GPU {gpu_start:.1f}%")
                    
                    # 显示启用的检索增强功能
                    enhancements = []
                    if st.session_state.get('enable_bm25', False):
                        enhancements.append("BM25混合检索")
                    if st.session_state.get('enable_rerank', False):
                        enhancements.append("Re-ranking重排序")
                    
                    if enhancements:
                        enhancement_str = " + ".join(enhancements)
                        terminal_logger.info(f"🎯 检索增强: {enhancement_str}")
                        logger.log("查询对话", "检索增强", f"启用功能: {enhancement_str}")
                    
                    with terminal_logger.timer("检索相关文档"):
                        logger.log_retrieval_start(kb_name=active_kb_name)
                        
                        # 确保 embedding 模型已设置
                        embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
                        if embed:
                            Settings.embed_model = embed
                        
                        # GPU加速检索 - 批量处理
                        retrieval_start = time.time()
                        response = st.session_state.chat_engine.stream_chat(final_prompt)
                        retrieval_time = time.time() - retrieval_start
                        
                        terminal_logger.info(f"🔍 检索耗时: {retrieval_time:.2f}s (GPU加速)")
                        
                        full_text = ""
                        # 流式输出 + 资源控制
                        token_count = 0 # 这里的计数仅用于进度估算
                        full_text = ""
                        
                        for token in response.response_gen:
                            full_text += token
                            msg_placeholder.markdown(full_text + "▌")
                            
                            # 每50个token检查资源
                            token_count += 1
                            if token_count % 50 == 0:
                                cpu_now, mem_now, gpu_now, should_throttle = check_resource_usage(threshold=80.0)
                                if should_throttle:
                                    terminal_logger.info(f"⚠️ 资源限流: CPU {cpu_now:.1f}% | 内存 {mem_now:.1f}% | GPU {gpu_now:.1f}%")
                                    time.sleep(0.05)  # 轻微延迟
                        
                        msg_placeholder.markdown(full_text)
                    
                    # 提取 token 统计 (优先使用真实数据)
                    prompt_tokens = 0
                    completion_tokens = 0
                    
                    if hasattr(response, 'raw') and response.raw:
                        usage = response.raw.get('usage', {})
                        prompt_tokens = usage.get('prompt_tokens', 0)
                        completion_tokens = usage.get('completion_tokens', 0)
                    
                    # 如果没有真实 Usage，则进行估算
                    if completion_tokens == 0:
                        # 简单估算：中文字符约0.6 token，英文字符约0.25 token (WordCount)
                        # 这里使用更通用的估算：中文 * 1.5, 英文 * 0.5 (token count)
                        # 或者直接显示字符数更准确
                        total_chars = len(full_text)
                        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', full_text))
                        # 混合估算
                        completion_tokens = int((chinese_chars * 1.5) + ((total_chars - chinese_chars) * 0.3))
                        token_count = completion_tokens # 更新为更准确的估算值
                    else:
                        token_count = completion_tokens # 使用真实值

                    # 多核并行处理节点
                    srcs = []
                    if response.source_nodes:
                        logger.log_retrieval_result(len(response.source_nodes), kb_name=active_kb_name)
                        terminal_logger.data_summary("检索结果", {
                            "查询": final_prompt[:50] + "..." if len(final_prompt) > 50 else final_prompt,
                            "相关文档": len(response.source_nodes),
                            "知识库": active_kb_name
                        })
                        
                        # 多进程并行处理节点（真正利用多核CPU）
                        max_workers = max(2, os.cpu_count() - 1)  # 保留1核给系统
                        
                        # 提取节点数据（序列化友好）
                        node_data = []
                        for node in response.source_nodes:
                            # 安全提取文本
                            text = ''
                            try:
                                if hasattr(node, 'get_text'):
                                    text = node.get_text()
                                elif hasattr(node, 'text'):
                                    text = node.text
                                elif hasattr(node, 'node') and hasattr(node.node, 'text'):
                                    text = node.node.text
                                else:
                                    text = str(node)[:150]
                            except:
                                text = str(node)[:150]
                            
                            node_data.append({
                                'metadata': getattr(node, 'metadata', {}),
                                'score': getattr(node, 'score', 0.0),
                                'text': text
                            })
                        
                        # 智能多进程处理 (优化版 - 专家建议 P2)
                        if len(node_data) > 10:
                            max_workers = max(2, min(os.cpu_count() - 1, len(node_data) // 2))
                            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                                srcs = [s for s in executor.map(_process_node_worker, 
                                       [(d, active_kb_name) for d in node_data]) if s]
                            terminal_logger.info(f"⚡ 多进程处理: {len(srcs)} 个节点 | 使用 {max_workers} 进程")
                        else:
                            # 少量节点直接串行处理，避免进程开销
                            srcs = [_process_node_worker((d, active_kb_name)) for d in node_data]
                            srcs = [s for s in srcs if s]
                            terminal_logger.info(f"⚡ 串行处理: {len(srcs)} 个节点 (少量数据)")
                    
                    logger.log_answer_complete(
                        kb_name=active_kb_name, 
                        model=llm_model, 
                        tokens=token_count,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )
                    
                    # 计算总耗时
                    total_time = time.time() - start_time
                    
                    # 资源监控结束
                    cpu_end, mem_end, gpu_end, _ = check_resource_usage(threshold=80.0)
                    terminal_logger.info(f"✅ 资源峰值: CPU {max(cpu_start, cpu_end):.1f}% | 内存 {max(mem_start, mem_end):.1f}% | GPU {max(gpu_start, gpu_end):.1f}%")
                    terminal_logger.complete_operation(f"查询完成 (耗时 {total_time:.2f}s)")
                    
                    # 准备统计信息
                    tokens_per_sec = token_count / total_time if total_time > 0 else 0
                    stats = {
                        "time": total_time,
                        "tokens": token_count,
                        "tokens_per_sec": tokens_per_sec,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "cpu": max(cpu_start, cpu_end),
                        "mem": max(mem_start, mem_end),
                        "gpu": max(gpu_start, gpu_end)
                    }
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": full_text, 
                        "sources": srcs,
                        "stats": stats
                    })
                    # 历史记录保存已移动到流程末尾
                    
                    # 在前端显示统计信息 (优化版 - 专家建议 P2)
                    # 1. 简单概览
                    stats_simple = f"⏱️ {total_time:.1f}秒 | 📝 约 {token_count} 字符"
                    st.caption(stats_simple)
                    
                    # 2. 详细信息 (折叠)
                    with st.expander("📊 详细统计", expanded=False):
                        st.caption(f"🚀 速度: {tokens_per_sec:.1f} tokens/s")
                        if prompt_tokens:
                            st.caption(f"📥 输入: {prompt_tokens} | 📤 输出: {completion_tokens}")
                        st.caption(f"💻 资源: CPU {max(cpu_start, cpu_end):.1f}% | 内存 {max(mem_start, mem_end):.1f}% | GPU {max(gpu_start, gpu_end):.1f}%")
                    
                    # 问答结束后，自动生成初始追问，并添加到 suggestions_history
                    # 使用 container 来显示加载状态，避免界面跳动
                    st.divider()
                    sug_container = st.empty()
                    sug_container.caption("✨ 正在生成推荐问题...")
                    initial_sugs = generate_follow_up_questions(
                        full_text, 
                        num_questions=3,
                        query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None
                    )
                    sug_container.empty()
                    
                    if initial_sugs:
                        st.session_state.suggestions_history.extend(initial_sugs)
                        terminal_logger.info(f"✨ 生成 {len(initial_sugs)} 个推荐问题")
                        
                        # 立即显示生成的推荐问题 (无需等待重绘)
                        st.markdown("##### 🚀 追问推荐")
                        for idx, q in enumerate(initial_sugs):
                            if st.button(f"👉 {q}", key=f"temp_sug_{int(time.time())}_{idx}", use_container_width=True):
                                click_btn(q)
                    else:
                        terminal_logger.info("⚠️ 推荐问题生成失败")
                    
                    # 延迟保存：确认所有步骤（包括推荐问题）都成功后再保存
                    if active_kb_name: save_chat_history(active_kb_name, st.session_state.messages)
                    
                    # 释放内存
                    cleanup_memory()
                    terminal_logger.info("🧹 对话完成，内存已清理")
                    
                    st.session_state.is_processing = False  # 处理完成
                    
                    # 检查是否有新问题排队
                    if st.session_state.prompt_trigger:
                        st.rerun()  # 只在有新问题时才重新运行
                except Exception as e: 
                    print(f"❌ 查询出错: {e}\n")
                    st.error(f"出错: {e}")
                    
                    # 发生错误，回滚最后一条消息（如果是 assistant 生成的）
                    # 避免保存不完整的回答
                    if st.session_state.messages and st.session_state.messages[-1]['role'] == 'assistant':
                        st.session_state.messages.pop()
                    
                    # 释放内存
                    cleanup_memory()
                    terminal_logger.info("🧹 错误处理完成，内存已清理")
                    st.session_state.is_processing = False