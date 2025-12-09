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
from concurrent.futures import ThreadPoolExecutor, as_completed
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

# 引入 UI 高级配置 (Stage 3.2.3)
from src.ui.advanced_config import render_advanced_features

# 引入 UI 配置表单 (Stage 3.2.2)
from src.ui.config_forms import render_basic_config

# 引入状态管理器 (Stage 3.3)
from src.core.state_manager import state

# 引入文档处理器 (Stage 4.1)
from src.processors import UploadHandler, IndexBuilder

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

# 引入文件处理模块
from src.file_processor import scan_directory_safe

# 引入并行执行模块
from src.utils.parallel_executor import ParallelExecutor
from src.utils.parallel_tasks import process_node_worker, extract_metadata_task

# 引入聊天模块 (Stage 7)
from src.chat import ChatEngine, SuggestionManager

# 引入配置模块 (Stage 8)
from src.config import ConfigLoader, ConfigValidator

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

# 使用新的配置加载器 (Stage 8)
defaults = ConfigLoader.load()

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
        # 使用新的配置加载器快速配置 (Stage 8)
        ConfigLoader.quick_setup()
        st.success("✅ 已使用默认配置！\n\n💡 下一步：创建知识库 → 上传文档 → 开始对话")
        time.sleep(2)
        st.rerun()
    
    st.caption("💡 或手动配置（高级用户）")
    
    st.markdown("---")
    
    # P0改进3: 侧边栏分组 - 基础配置（默认折叠）- 使用新组件 (Stage 3.2.2)
    config_values = render_basic_config(defaults)
    
    # 提取配置值
    llm_provider = config_values['llm_provider']
    llm_url = config_values['llm_url']
    llm_model = config_values['llm_model']
    llm_key = config_values['llm_key']
    embed_provider = config_values['embed_provider']
    embed_model = config_values['embed_model']
    embed_url = config_values['embed_url']
    embed_key = config_values['embed_key']
    
    # P0改进3: 高级功能（默认折叠）- 使用新组件 (Stage 3.2.3)
    advanced_config = render_advanced_features()
    
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
        
        # 处理上传 (Stage 4.1 - 使用 UploadHandler)
        if uploaded_files:
            if 'last_uploaded_names' not in st.session_state:
                st.session_state.last_uploaded_names = []
            
            current_names = [f.name for f in uploaded_files]
            
            # 只在文件列表变化时处理
            if set(current_names) != set(st.session_state.last_uploaded_names):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # 使用 UploadHandler 处理上传
                handler = UploadHandler(UPLOAD_DIR, logger)
                
                for idx, f in enumerate(uploaded_files):
                    status_text.text(f"验证中: {f.name} ({idx+1}/{len(uploaded_files)})")
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                result = handler.process_uploads(uploaded_files)
                
                progress_bar.empty()
                status_text.empty()
                
                st.session_state.last_uploaded_names = current_names
                st.session_state.uploaded_path = os.path.abspath(result.batch_dir)
                
                # 显示上传结果
                if result.success_count > 0:
                    st.success(f"✅ 成功上传 {result.success_count} 个文件")
                
                if result.skipped_count > 0:
                    st.warning(f"⚠️ 跳过 {result.skipped_count} 个文件")
                    with st.expander("查看跳过详情", expanded=False):
                        for reason in result.skip_reasons:
                            st.text(f"• {reason}")
                
                time.sleep(1)
                if result.success_count > 0:
                    st.rerun()


        # 使用上传路径或手动输入的路径
        target_path = st.session_state.get('uploaded_path') or target_path
        
        auto_name = ""
        if target_path:
            if os.path.exists(target_path):
                # 使用 UploadHandler 统计文件信息 (Stage 4.1)
                cnt, file_types, total_size = UploadHandler.get_folder_stats(target_path)
                
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
            st.markdown("**⚡ 性能选项**")
            extract_metadata = st.checkbox(
                "提取元数据（关键词、分类等）", 
                value=False,
                help="开启后提取文件分类、关键词等信息，但会降低 30% 处理速度"
            )
            if extract_metadata:
                st.caption("📊 完整模式：提取元数据，可查看分类和关键词")
        
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
        if col1.button("↩️ 撤销提问", use_container_width=True, disabled=len(state.get_messages()) < 2, help="撤销最后一组问答"):
            if len(state.get_messages()) >= 2:
                # 弹出最后两条消息 (User + Assistant)
                st.session_state.messages.pop()
                st.session_state.messages.pop()
                # 保存更新后的历史
                if current_kb_name:
                    save_chat_history(current_kb_name, state.get_messages())
                st.toast("✅ 已撤销上一条消息")
                time.sleep(0.5)
                st.rerun()
        
        # 清空按钮
        if col2.button("🧹 清空对话", use_container_width=True, disabled=len(state.get_messages()) == 0):
            st.session_state.messages = []
            st.session_state.suggestions_history = []
            if current_kb_name:
                save_chat_history(current_kb_name, [])
            st.toast("✅ 对话已清空")
            time.sleep(0.5)
            st.rerun()
        
        # 对话历史管理
        if len(state.get_messages()) > 0:
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
                qa_count = len(state.get_messages()) // 2
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
    """处理知识库逻辑 (Stage 4.2 - 使用 IndexBuilder)"""
    persist_dir = os.path.join(output_base, final_kb_name)
    start_time = time.time()

    # 设置嵌入模型
    terminal_logger.info(f"🔧 设置嵌入模型: {embed_model} (provider: {embed_provider})")
    embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
    if not embed:
        terminal_logger.error(f"❌ 嵌入模型加载失败: {embed_model}")
        raise ValueError(f"无法加载嵌入模型: {embed_model}")
    
    Settings.embed_model = embed
    try:
        actual_dim = len(embed._get_text_embedding("test"))
        terminal_logger.success(f"✅ 嵌入模型已设置: {embed_model} ({actual_dim}维)")
    except:
        terminal_logger.success(f"✅ 嵌入模型已设置: {embed_model}")

    logger.log_kb_start(kb_name=final_kb_name)
    
    # UI 状态容器
    status_container = st.status(f"🚀 处理知识库: {final_kb_name}", expanded=True)
    prog_bar = status_container.progress(0)
    status_container.write(f"⏱️ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
    
    # 回调函数：更新 UI
    def status_callback(msg_type, *args):
        if msg_type == "step":
            step_num, step_desc = args
            status_container.write(f"📂 [步骤{step_num}/6] {step_desc}")
            terminal_logger.info(f"📂 [步骤 {step_num}/6] {step_desc}")
            prog_bar.progress(step_num * 15)
        elif msg_type == "info":
            info_msg = args[0]
            status_container.write(f"   {info_msg}")
            terminal_logger.info(f"   {info_msg}")
        elif msg_type == "warning":
            warn_msg = args[0]
            status_container.write(f"   ⚠️  {warn_msg}")
            terminal_logger.warning(f"   ⚠️  {warn_msg}")
    
    # 获取源路径
    current_target_path = st.session_state.get('uploaded_path') or st.session_state.path_input
    if not current_target_path or not os.path.exists(current_target_path):
        status_container.update(label="❌ 路径无效", state="error")
        terminal_logger.error(f"❌ 路径无效: {current_target_path}")
        raise ValueError(f"路径无效: {current_target_path}")
    
    # 使用 IndexBuilder 构建索引
    builder = IndexBuilder(
        kb_name=final_kb_name,
        persist_dir=persist_dir,
        embed_model=embed,
        embed_model_name=embed_model,
        extract_metadata=extract_metadata,  # 传递性能选项
        logger=logger,
        terminal_logger=terminal_logger
    )
    
    result = builder.build(
        source_path=current_target_path,
        force_reindex=force_reindex,
        action_mode=action_mode,
        status_callback=status_callback
    )
    
    if not result.success:
        status_container.update(label=f"❌ 处理失败: {result.error}", state="error")
        terminal_logger.error(f"❌ 处理失败: {result.error}")
        raise ValueError(result.error)
    
    # 保存索引
    if result.index:
        result.index.storage_context.persist(persist_dir=persist_dir)
        terminal_logger.success(f"💾 索引已保存到: {persist_dir}")
    
    # 更新进度
    prog_bar.progress(100)
    
    # 计算耗时
    duration = time.time() - start_time
    terminal_logger.separator("处理完成")
    terminal_logger.success(f"✅ 知识库 '{final_kb_name}' 处理完成")
    terminal_logger.info(f"📊 统计: {result.file_count} 个文件, {result.doc_count} 个文档片段")
    terminal_logger.info(f"⏱️  耗时: {duration:.1f} 秒")
    
    logger.log_kb_complete(
        kb_name=final_kb_name,
        doc_count=result.doc_count
    )
    
    status_container.update(label=f"✅ 知识库 '{final_kb_name}' 处理完成", state="complete", expanded=False)
    
    time.sleep(0.5)
    return result.doc_count

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
if "question_queue" not in st.session_state: st.session_state.question_queue = []  # 问题队列

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
    """点击追问按钮，将问题加入队列（去重）"""
    if st.session_state.chat_engine:
        # 检查队列中是否已存在相同问题
        if q not in st.session_state.question_queue:
            st.session_state.question_queue.append(q)
        else:
            st.toast("⚠️ 该问题已在队列中")
    st.rerun()

# ==========================================
# Stage 7+8: 新的聊天引擎和配置管理
# ==========================================
# 新模块已创建并测试通过:
# - src/chat/chat_engine.py: ChatEngine 类
# - src/chat/suggestion_manager.py: SuggestionManager 类
# - src/config/config_loader.py: ConfigLoader 类
# - src/config/config_validator.py: ConfigValidator 类
#
# 使用示例 (未来可替换现有逻辑):
# 
# # 使用 ChatEngine 处理问题
# chat_engine = ChatEngine(st.session_state.chat_engine, active_kb_name)
# for result in chat_engine.process_question(question, llm_model, quoted_text):
#     if result['type'] == 'token':
#         # 流式输出
#         pass
#     elif result['type'] == 'complete':
#         # 完成处理
#         full_text = result['content']
#         sources = result['sources']
#         stats = result['stats']
#
# # 使用 SuggestionManager 生成追问
# suggestions = SuggestionManager.generate_initial_suggestions(
#     context_text=full_text,
#     messages=st.session_state.messages,
#     question_queue=st.session_state.question_queue,
#     query_engine=st.session_state.chat_engine
# )
# SuggestionManager.add_suggestions(suggestions)
# ==========================================

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
                        # 读取知识库信息（优先使用 .kb_info.json）
                        kb_info_file = os.path.join(db_path, ".kb_info.json")
                        if os.path.exists(kb_info_file):
                            with open(kb_info_file, 'r') as f:
                                kb_info = json.load(f)
                                kb_embed_model = kb_info.get('embedding_model', 'BAAI/bge-large-zh-v1.5')
                        else:
                            # 兼容旧版本，使用 manifest
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
    # 读取知识库模型信息（优先使用 .kb_info.json）
    kb_info_file = os.path.join(db_path, ".kb_info.json")
    if os.path.exists(kb_info_file):
        try:
            with open(kb_info_file, 'r') as f:
                kb_info = json.load(f)
                kb_model = kb_info.get('embedding_model', 'Unknown')
        except:
            kb_model = manifest.get('embed_model', 'Unknown')
    else:
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
                        st.rerun()  # 立即刷新页面显示摘要
                
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
                    
                    # 使用默认参数捕获当前值
                    def toggle_select_all(files=current_page_files):
                        if st.session_state.get(f"select_all_page_{st.session_state.file_page}"):
                            st.session_state.selected_for_summary.update(files)
                        else:
                            st.session_state.selected_for_summary.difference_update(files)
                    
                    select_all = cols[0].checkbox(
                        "全选", 
                        value=all_selected, 
                        key=f"select_all_page_{st.session_state.file_page}", 
                        label_visibility="collapsed",
                        on_change=toggle_select_all
                    )
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
                save_chat_history(active_kb_name, state.get_messages())
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
for msg_idx, msg in enumerate(state.get_messages()):
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
        is_last_message = msg_idx == len(state.get_messages()) - 1
        if "suggestions" in msg and msg["suggestions"] and is_last_message and not st.session_state.suggestions_history:
            st.write("")
            for idx, q in enumerate(msg["suggestions"]):
                if st.button(f"👉 {q}", key=f"sug_{msg_idx}_{idx}", use_container_width=True):
                    click_btn(q)
    
    # 在最后一条 assistant 消息之后显示动态追问推荐（在 chat_message 容器外）
    is_last_message = msg_idx == len(state.get_messages()) - 1
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
                    # 排除队列中的问题
                    all_history_questions.extend(st.session_state.question_queue)
                    
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

# 如果有新输入，加入队列
if user_input:
    if not st.session_state.chat_engine:
        st.error("请先点击左侧【🚀 执行处理】启动系统")
    else:
        st.session_state.question_queue.append(user_input)

# 处理 prompt_trigger（追问按钮）
if st.session_state.prompt_trigger:
    if st.session_state.chat_engine:
        st.session_state.question_queue.append(st.session_state.prompt_trigger)
    st.session_state.prompt_trigger = None

# 显示队列状态
queue_len = len(st.session_state.question_queue)
if st.session_state.get('is_processing'):
    if queue_len > 0:
        # 显示队列中的问题
        with st.expander(f"⏳ 正在处理问题，队列中还有 {queue_len} 个问题等待...", expanded=False):
            for i, q in enumerate(st.session_state.question_queue, 1):
                # 截断过长的问题
                display_q = q[:50] + "..." if len(q) > 50 else q
                st.caption(f"{i}. {display_q}")
    else:
        st.info("⏳ 正在处理问题...")
elif queue_len > 0:
    # 显示待处理的问题列表
    with st.expander(f"📝 队列中有 {queue_len} 个问题待处理", expanded=True):
        for i, q in enumerate(st.session_state.question_queue, 1):
            display_q = q[:50] + "..." if len(q) > 50 else q
            st.caption(f"{i}. {display_q}")

# 从队列中取出问题处理
if not st.session_state.is_processing and st.session_state.question_queue:
    final_prompt = st.session_state.question_queue.pop(0)
    
    if st.session_state.chat_engine:
        # 不清空 suggestions_history，保留追问按钮
        st.session_state.is_processing = True  # 标记正在处理
        
        # 强制检测知识库维度并切换模型（静默处理，不显示加载）
        # 优化：只在首次或切换知识库时检测，避免每次问答都重复
        db_path = os.path.join(output_base, active_kb_name)
        
        # 检查是否需要重新检测（知识库切换或首次）
        last_checked_kb = st.session_state.get('_last_checked_kb')
        if last_checked_kb != active_kb_name:
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
            
            # 标记已检测
            st.session_state._last_checked_kb = active_kb_name
        
        terminal_logger.separator("知识库查询")
        terminal_logger.start_operation("查询", f"知识库: {active_kb_name}")
        
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
        if active_kb_name: save_chat_history(active_kb_name, state.get_messages())

        with st.chat_message("user", avatar="🧑‍💻"): st.markdown(final_prompt)
        
        with st.chat_message("assistant", avatar="🤖"):
            msg_placeholder = st.empty()
            with st.status("⏳ 正在检索并思考...", expanded=True):
                try:
                    # 开始计时
                    start_time = time.time()
                    
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
                            token_count += 1
                        
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
                        
                        # 使用并行执行器处理节点（自动判断串行/并行）
                        executor = ParallelExecutor()
                        tasks = [(d, active_kb_name) for d in node_data]
                        srcs = [s for s in executor.execute(process_node_worker, tasks, threshold=10) if s]
                        
                        if len(node_data) >= 10:
                            terminal_logger.info(f"⚡ 并行处理: {len(srcs)} 个节点")
                        else:
                            terminal_logger.info(f"⚡ 串行处理: {len(srcs)} 个节点")
                    
                    logger.log_answer_complete(
                        kb_name=active_kb_name, 
                        model=llm_model, 
                        tokens=token_count,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )
                    
                    # 计算总耗时
                    total_time = time.time() - start_time
                    terminal_logger.complete_operation(f"查询完成 (耗时 {total_time:.2f}s)")
                    
                    # 准备统计信息
                    tokens_per_sec = token_count / total_time if total_time > 0 else 0
                    stats = {
                        "time": total_time,
                        "tokens": token_count,
                        "tokens_per_sec": tokens_per_sec,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens
                    }
                    
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": full_text, 
                        "sources": srcs,
                        "stats": stats
                    })
                    # 历史记录保存已移动到流程末尾
                    
                    # 在前端显示统计信息
                    stats_simple = f"⏱️ {total_time:.1f}秒 | 📝 约 {token_count} 字符"
                    st.caption(stats_simple)
                    
                    # 详细信息 (折叠)
                    with st.expander("📊 详细统计", expanded=False):
                        st.caption(f"🚀 速度: {tokens_per_sec:.1f} tokens/s")
                        if prompt_tokens:
                            st.caption(f"📥 输入: {prompt_tokens} | 📤 输出: {completion_tokens}")
                    
                    # 问答结束后，自动生成初始追问，并添加到 suggestions_history
                    # 使用 container 来显示加载状态，避免界面跳动
                    st.divider()
                    sug_container = st.empty()
                    sug_container.caption("✨ 正在生成推荐问题...")
                    # 排除已有的问题（历史+队列+已生成的追问）
                    existing_questions = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
                    existing_questions.extend(st.session_state.question_queue)
                    existing_questions.extend(st.session_state.suggestions_history)  # 排除已生成的追问
                    
                    initial_sugs = generate_follow_up_questions(
                        full_text, 
                        num_questions=3,
                        existing_questions=existing_questions,
                        query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None
                    )
                    sug_container.empty()
                    
                    if initial_sugs:
                        # 去重：只添加不在 suggestions_history 中的问题
                        new_sugs = [q for q in initial_sugs if q not in st.session_state.suggestions_history]
                        if new_sugs:
                            st.session_state.suggestions_history.extend(new_sugs)
                            terminal_logger.info(f"✨ 生成 {len(new_sugs)} 个新推荐问题")
                            
                            # 立即显示新生成的推荐问题
                            st.markdown("##### 🚀 追问推荐")
                            for idx, q in enumerate(new_sugs):
                                if st.button(f"👉 {q}", key=f"temp_sug_{int(time.time())}_{idx}", use_container_width=True):
                                    click_btn(q)
                        else:
                            terminal_logger.info("⚠️ 生成的问题已存在，跳过")
                    else:
                        terminal_logger.info("⚠️ 推荐问题生成失败")
                    
                    # 延迟保存：确认所有步骤（包括推荐问题）都成功后再保存
                    if active_kb_name: save_chat_history(active_kb_name, state.get_messages())
                    
                    # 释放内存
                    cleanup_memory()
                    terminal_logger.info("🧹 对话完成，内存已清理")
                    
                    st.session_state.is_processing = False  # 处理完成
                    
                    # 检查队列中是否还有问题
                    if st.session_state.question_queue:
                        terminal_logger.info(f"📝 队列中还有 {len(st.session_state.question_queue)} 个问题，继续处理...")
                        st.rerun()  # 处理下一个问题
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
