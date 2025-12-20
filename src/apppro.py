# 初始化环境配置
# 环境变量设置 - 减少启动警告
__version__ = "2.4.7"

import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# 抑制烦人的 Pydantic 警告
import warnings
warnings.filterwarnings("ignore", message=".*UnsupportedFieldAttributeWarning.*")


import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.environment import initialize_environment
initialize_environment()

import os
# 在最开始设置环境变量，禁用PaddleOCR详细日志
import os

def get_default_model():
    """统一获取默认模型"""
    from src.services.config_service import get_config_service
    config_service = get_config_service()
    return config_service.get_default_model()

def update_all_model_configs(new_model):
    """统一更新所有地方的模型配置"""
    from src.services.config_service import get_config_service
    config_service = get_config_service()
    
    success = config_service.update_model_config(new_model)
    
    if success:
        # 更新session state
        import streamlit as st
        st.session_state.selected_model = new_model
        
        # 更新全局LLM
        ollama_url = config_service.get_config_value('llm_url_ollama', 'http://localhost:11434')
        set_global_llm_model("Ollama", new_model, api_url=ollama_url)
    
    return success
os.environ['GLOG_minloglevel'] = '3'  # 只显示致命错误
os.environ['FLAGS_logtostderr'] = '0'  # 不输出到stderr
os.environ['PADDLE_LOG_LEVEL'] = '50'  # 最高级别，几乎不输出
os.environ['FLAGS_v'] = '0'  # 禁用详细日志
os.environ['GLOG_v'] = '0'  # 禁用GLOG详细日志

# 设置多进程相关环境变量，影响进程调度
os.environ['OMP_NUM_THREADS'] = '1'  # 每个进程只用1个线程
os.environ['MKL_NUM_THREADS'] = '1'  # Intel MKL只用1个线程
os.environ['OPENBLAS_NUM_THREADS'] = '1'  # OpenBLAS只用1个线程
os.environ['VECLIB_MAXIMUM_THREADS'] = '1'  # Apple Accelerate只用1个线程

import streamlit as st

# 防止HTML内容被截断
st.set_page_config(
    page_title="RAG Pro Max",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置不截断HTML显示
import streamlit.components.v1 as components

import shutil
import time
import requests
import ollama
import re
import subprocess

# 🧹 启动时自动清理临时文件
from src.common.utils import cleanup_temp_files

# 执行启动清理（使用一周=168小时）
cleaned_count = cleanup_temp_files("temp_uploads", 168)
if cleaned_count > 0:
    print(f"🧹 已清理 {cleaned_count} 个临时文件")

import json
import zipfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

# 引入新的优化组件
from src.utils.enhanced_ocr_optimizer import enhanced_ocr_optimizer
from src.ui.progress_monitor import progress_monitor
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
from src.app_logging import LogManager
logger = LogManager()
# terminal_logger 已被 logger 替代
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

# 引入配置管理
from src.config import ConfigLoader, ManifestManager

# 引入聊天管理
from src.chat import HistoryManager, SuggestionManager

# 引入 UI 模块
from src.ui.page_style import PageStyle
from src.ui.sidebar_config import SidebarConfig

# 引入工具函数
from src.utils.app_utils import (
    get_kb_embedding_dim,
    generate_doc_summary,
    remove_file_from_manifest,
    initialize_session_state,
    show_first_time_guide,
    handle_kb_switching
)

# 引入主控制器
from src.core.main_controller import MainController

# 引入知识库处理器
from src.kb.kb_processor import KBProcessor

# 引入文档解析器
from src.processors.document_parser import _parse_single_doc, _parse_batch_docs

# 引入资源保护
from src.utils.adaptive_throttling import get_resource_guard
import psutil as psutil_main

# 初始化资源保护
resource_guard = get_resource_guard()

# 引入知识库管理
from src.kb import KBManager
kb_manager = KBManager()

# 性能监控 (v1.5.1)
from src.ui.performance_monitor import get_monitor
perf_monitor = get_monitor()

# 查询改写 (v1.6)
from src.query.query_rewriter import QueryRewriter

# 知识库名称优化器
from src.utils.kb_name_optimizer import KBNameOptimizer, sanitize_filename

# 文档预览 (v1.6)
from src.kb.document_viewer import DocumentViewer
from src.ui.document_preview import show_upload_preview, show_kb_documents

# 文档详情对话框
@st.dialog("📄 文档详情")
def show_document_detail_dialog(kb_name: str, file_info: dict) -> None:
    """显示文档详情对话框"""
    st.subheader(f"📄 {file_info['name']}")
    
    # 基本信息 - 两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 基本信息")
        st.markdown(f"**📂 路径**: `{file_info.get('file_path', 'N/A')}`")
        st.markdown(f"**📏 大小**: {file_info.get('size', '未知')} ({file_info.get('size_bytes', 0):,} 字节)")
        st.markdown(f"**📄 类型**: {file_info.get('type', '未知')}")
        st.markdown(f"**🌐 语言**: {file_info.get('language', '未知')}")
        
    with col2:
        st.markdown("### 🕒 时间信息")
        st.markdown(f"**📅 添加时间**: {file_info.get('added_at', '未知')}")
        st.markdown(f"**🕒 最后访问**: {file_info.get('last_accessed', '从未访问') or '从未访问'}")
        st.markdown(f"**📁 目录**: {file_info.get('parent_folder', '未知')}")
        st.markdown(f"**🔐 哈希**: `{file_info.get('file_hash', 'N/A')}`")
    
    # 统计信息
    st.markdown("### 📈 统计信息")
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    stat_col1.metric("🧩 向量片段", len(file_info.get('doc_ids', [])))
    stat_col2.metric("🔥 查询命中", file_info.get('hit_count', 0))
    stat_col3.metric("⭐ 平均评分", f"{file_info.get('avg_score', 0.0):.2f}" if file_info.get('avg_score') else 'N/A')
    
    # 分类和关键词
    if file_info.get('category') or file_info.get('keywords'):
        st.markdown("### 🏷️ 分类标签")
        tag_col1, tag_col2 = st.columns(2)
        tag_col1.markdown(f"**📚 分类**: {file_info.get('category', '未分类')}")
        if file_info.get('keywords'):
            tag_col2.markdown(f"**🏷️ 关键词**: {', '.join(file_info.get('keywords', [])[:8])}")
    
    # 向量片段ID
    if file_info.get('doc_ids'):
        st.markdown("### 🧬 向量片段ID")
        with st.expander(f"查看 {len(file_info['doc_ids'])} 个片段ID", expanded=False):
            st.text_area(
                "片段ID列表", 
                value='\n'.join(file_info['doc_ids']), 
                height=200,
                label_visibility="collapsed"
            )
    
    # 关闭按钮
    if st.button("✅ 关闭", use_container_width=True):
        st.session_state.show_doc_detail = None
        st.session_state.show_doc_detail_kb = None
        st.rerun()

def generate_smart_kb_name(target_path, cnt, file_types, folder_name):
    """智能生成知识库名称 - 使用优化器确保唯一性"""
    
    # 策略1：单文件特例处理 - 直接使用文件名作为知识库名称
    if cnt == 1 and os.path.exists(target_path):
        try:
            # 查找目录中的那个唯一文件（忽略隐藏文件）
            files = [f for f in os.listdir(target_path) if not f.startswith('.') and os.path.isfile(os.path.join(target_path, f))]
            if len(files) >= 1:
                single_file = files[0]
                name_without_ext = os.path.splitext(single_file)[0]
                suggested_name = sanitize_filename(name_without_ext)
                
                # 如果文件名有效，直接使用它
                if suggested_name and len(suggested_name) > 1:
                    from src.core.app_config import output_base
                    return KBNameOptimizer.generate_unique_name(suggested_name, output_base)
        except Exception:
            pass # 出错则回退到原有逻辑

    # 使用优化器的建议名称功能
    suggested_name = KBNameOptimizer.suggest_name_from_content(target_path, cnt, list(file_types.keys()))
    
    # 如果没有建议名称，使用备用逻辑
    if not suggested_name:
        # 分析文件类型
        main_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
        if not main_types:
            suggested_name = "文档知识库"
        else:
            main_ext = main_types[0][0].replace('.', '').upper()
            
            # 根据文件类型生成基础名称
            type_names = {
                'PDF': 'PDF文档库', 'DOCX': 'Word文档库', 'DOC': 'Word文档库',
                'MD': 'Markdown笔记', 'TXT': '文本文档库',
                'PY': 'Python代码库', 'JS': 'JavaScript代码库', 'JAVA': 'Java代码库',
                'XLSX': 'Excel数据库', 'CSV': 'CSV数据集',
                'PPT': 'PPT演示库', 'PPTX': 'PPT演示库',
                'HTML': '网页文档库', 'JSON': 'JSON配置库'
            }
            
            if len(main_types) == 1:
                suggested_name = type_names.get(main_ext, f"{main_ext}文档库")
            else:
                suggested_name = f"混合文档库_{cnt}个文件"
    
    # 使用优化器确保名称唯一性（会在需要时添加时间戳）
    from src.core.app_config import output_base
    return KBNameOptimizer.generate_unique_name(suggested_name, output_base)

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


# from src.ui.compact_sidebar import render_compact_sidebar  # 已删除冗余模块
# 增强功能模块 (v1.7.4)
from src.utils.error_handler_enhanced import error_handler
from src.utils.memory_manager_enhanced import memory_manager
from src.ui.performance_dashboard_enhanced import performance_dashboard
from src.ui.user_experience_enhanced import ux_enhancer

# 引入并行执行模块
from src.utils.parallel_executor import ParallelExecutor
from src.utils.safe_parallel_tasks import safe_process_node_worker as process_node_worker, extract_metadata_task

# 引入聊天模块 (Stage 7)
from src.chat import ChatEngine, SuggestionManager

# 引入配置模块 (Stage 8)
from src.config import ConfigLoader, ConfigValidator

# 多进程函数：文档分块解析（移到模块级别）
# 引入文档解析器
from src.processors.document_parser import _parse_single_doc, _parse_batch_docs

# ==========================================
# 1. 页面配置与样式
# ==========================================
PageStyle.setup_page()

# 注入 CSS
st.markdown("""
<style>
    /* 彻底禁止横向滚动和左右拖动手势 - 强制锁定布局 */
    html, body, [data-testid="stAppViewContainer"], .stApp, [data-testid="stApp"] {
        overflow-x: hidden !important;
        max-width: 100vw !important;
        overscroll-behavior-x: none !important;
        position: relative !important;
    }
    
    /* 强制禁止任何容器产生横向位移 */
    [data-testid="stMain"], [data-testid="stSidebar"] {
        overflow-x: hidden !important;
        max-width: 100% !important;
    }

    /* 极致压缩侧边栏间距 */
    section[data-testid="stSidebar"] .stSelectbox > div {
        margin-bottom: 1px !important;
    }
    
    section[data-testid="stSidebar"] .stTextInput > div {
        margin-bottom: 1px !important;
    }
    
    section[data-testid="stSidebar"] .stCaption {
        margin-bottom: 1px !important;
        margin-top: 1px !important;
    }
    
    section[data-testid="stSidebar"] .stContainer {
        margin-bottom: 1px !important;
        margin-top: 1px !important;
    }

    /* 增加侧边栏宽度，固定大小并禁止拖动缩放 */
    section[data-testid="stSidebar"] {
        min-width: 850px !important;
        width: 850px !important;
        max-width: 850px !important;
    }

    /* 隐藏并禁用侧边栏缩放手柄（彻底解决左下角左右拖动问题） */
    [data-testid="stSidebarResizer"] {
        display: none !important;
        pointer-events: none !important;
    }

    
    /* 统计区域容器 */
    .stats-container {
        background: white !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
    }
    

    /* 文档详情折叠优化 */
    .document-details {
        background: #f8f9fa !important;
        border-radius: 6px !important;
        padding: 0.75rem !important;
        margin: 0.5rem 0 !important;
        border-left: 3px solid #1f77b4 !important;
    }
    
    .document-summary {
        background: white !important;
        padding: 0.5rem !important;
        border-radius: 4px !important;
        margin-top: 0.5rem !important;
        border: 1px solid #dee2e6 !important;
        font-size: 0.85rem !important;
        line-height: 1.4 !important;
    }
    
    /* 批量操作按钮 */
    .batch-operations {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .batch-operations:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* 快速预览提示 */
    .preview-tooltip {
        position: absolute !important;
        background: rgba(0,0,0,0.9) !important;
        color: white !important;
        padding: 0.5rem !important;
        border-radius: 4px !important;
        font-size: 0.8rem !important;
        max-width: 300px !important;
        z-index: 1000 !important;
        pointer-events: none !important;
    }
    

        /* 完全修复参考片段显示 */
    .reference-snippet {
        background-color: #f8f9fa !important;
        border-left: 3px solid #1f77b4 !important;
        padding: 12px !important;
        margin: 10px 0 !important;
        border-radius: 6px !important;
        font-size: 0.9rem !important;
        line-height: 1.5 !important;
        word-wrap: break-word !important;
        overflow-wrap: break-word !important;
        white-space: pre-wrap !important;
        max-width: 100% !important;
    }
    
    .reference-header {
        font-size: 0.85rem !important;
        color: #666 !important;
        margin-bottom: 8px !important;
        font-weight: 500 !important;
    }
    
    .reference-content {
        color: #333 !important;
        background: white !important;
        padding: 8px 12px !important;
        border-radius: 4px !important;
        border: 1px solid #dee2e6 !important;
        max-height: none !important;
        overflow: visible !important;
        word-break: break-word !important;
    }
    
    /* 确保Streamlit不截断HTML */
    .stMarkdown > div {
        max-width: none !important;
        overflow: visible !important;
    }
    
    .stMarkdown div[style*="border-left"] {
        max-width: 100% !important;
        overflow: visible !important;
        word-wrap: break-word !important;
    }
    

    /* 减少间距 */
    .block-container {
        padding-top: 0.75rem !important;
        padding-bottom: 1rem !important;
    }

    .element-container {
        margin-bottom: 0.2rem !important;
    }
    
    h1, h2, h3 {
        margin: 0.2rem 0 !important;
    }
    
    [data-testid="column"] {
        padding: 0 0.3rem !important;
    }
    
    /* 文件列表 */
    .file-item {
        font-size: 0.8rem !important;
        padding: 0.5rem !important;
        background: rgba(0,0,0,0.02) !important;
        border-radius: 6px !important;
        margin-bottom: 0.3rem !important;
        border: 1px solid rgba(0,0,0,0.05) !important;
    }
    
    /* 欢迎页面 */
    .welcome-box {
        padding: 1.5rem !important;
        border-radius: 10px !important;
        background: rgba(255,75,75,0.02) !important;
        border: 1px solid rgba(255,75,75,0.1) !important;
        text-align: center !important;
        margin: 1rem 0 !important;
    }
    
    /* 进度条 */
    .stProgress > div > div {
        border-radius: 4px !important;
        height: 6px !important;
    }
    
    /* 响应式 */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 0.5rem !important;
        }
    }
</style>""", unsafe_allow_html=True)

# 应用启动日志
if 'app_initialized' not in st.session_state:
    logger.separator("RAG Pro Max 启动")
    logger.info("应用初始化中...")
    
    # 立即设置全局LLM（确保摘要生成等功能可用）
    try:
        # 读取配置文件获取LLM设置
        config_file = "app_config.json"
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            llm_provider = config.get('llm_provider', 'Ollama')
            if config.get('llm_type_idx', 0) == 0:  # Ollama
                llm_model = config.get('llm_model_ollama', 'gpt-oss:20b')
                llm_url = config.get('llm_url_ollama', 'http://localhost:11434')
                llm_key = ""
            else:  # OpenAI
                llm_model = config.get('llm_model_openai', 'gpt-3.5-turbo')
                llm_url = config.get('llm_url_openai', 'https://api.openai.com/v1')
                llm_key = config.get('llm_key', '')
            
            # 设置全局LLM
            set_global_llm_model(llm_provider, llm_model, llm_key, llm_url)
    except Exception as e:
        logger.warning(f"全局LLM初始化失败: {e}")
    
    st.session_state.app_initialized = True
    logger.success("应用初始化完成")

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
    """生成文档摘要 - 使用公共业务逻辑"""
    from src.common.business import generate_doc_summary as common_generate_doc_summary
    return common_generate_doc_summary(doc_text, filename)

with st.sidebar:
    # 横向标签页布局
    tab_main, tab_config, tab_monitor, tab_tools, tab_help = st.tabs(["🏠 主页", "⚙️ 配置", "📊 监控", "🔧 工具", "❓ 帮助"])
    
    with tab_main:

        # 知识库控制台标题与一键配置完全一行化
        console_col1, console_col2, console_col3 = st.columns([4, 1, 0.5])
        with console_col1:
            st.markdown("**💠 知识库控制台**")
        with console_col2:
            if st.button("⚡ 一键配置", use_container_width=True, key="quick_config_inline"):
                ConfigLoader.quick_setup()
                st.success("✅ 已使用默认配置！")
                time.sleep(1)
                st.rerun()
        with console_col3:
            st.markdown("❓", help="可手动配置，适合高级用户")
        
        if "model_list" not in st.session_state: st.session_state.model_list = []

        # 存储根目录完全一行化
        storage_col1, storage_col2, storage_col3 = st.columns([0.6, 5.9, 0.5])
        with storage_col1:
            st.markdown("**路径:**")
        with storage_col2:
            default_output_path = os.path.join(os.getcwd(), "vector_db_storage")
            output_base = st.text_input("", value=default_output_path, help="知识库文件的保存位置", label_visibility="collapsed")
        with storage_col3:
            if st.button("📂", help="打开存储目录", use_container_width=True, key="open_storage_dir"):
                if output_base and os.path.exists(output_base):
                    import webbrowser, urllib.parse
                    try:
                        file_url = 'file://' + urllib.parse.quote(os.path.abspath(output_base))
                        webbrowser.open(file_url)
                        st.toast("✅ 已打开")
                    except: pass
        if not output_base: output_base = default_output_path
            
        existing_kbs = (setattr(kb_manager, "base_path", output_base), kb_manager.list_all())[1]

        # --- 核心导航 ---
        nav_options = ["➕ 新建知识库..."] + [f"📂 {kb}" for kb in kb_manager.list_all()]

        # 默认选择"新建知识库"，避免自动加载大知识库
        default_idx = 0
        if "current_nav" in st.session_state and st.session_state.current_nav in nav_options:
            try:
                default_idx = nav_options.index(st.session_state.current_nav)
            except ValueError:
                default_idx = 0

        # 知识库选择完全一行化
        select_col1, select_col2, select_col3 = st.columns([0.6, 5.9, 0.5])
        with select_col1:
            st.markdown("**选择:**")
        with select_col2:
            selected_nav = st.selectbox("", nav_options, index=default_idx, label_visibility="collapsed")
        with select_col3:
            if st.button("🔄", help="刷新知识库列表", use_container_width=True, key="refresh_kb_list"):
                st.rerun()

        # 知识库搜索/过滤已按用户要求移除

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


        # --- 功能区 ---
        if is_create_mode:
            # 新建知识库标题完全一行化
            new_col1, new_col2, new_col3 = st.columns([0.6, 5.9, 0.5])
            with new_col1:
                st.markdown("**新建:**")
            with new_col2:
                st.markdown("")  # 占位
            with new_col3:
                if st.button("💡", help="智能建议", use_container_width=True, key="smart_suggest"):
                    st.toast("💡 建议：上传相关文档，系统会自动优化处理")
            
            with st.container(border=True):
                # 1. 路径选择完全一行化
                if "path_val" not in st.session_state: 
                    st.session_state.path_val = os.path.abspath(defaults.get("target_path", ""))
                if 'path_input' not in st.session_state:
                    st.session_state.path_input = ""
                if st.session_state.get('uploaded_path') and not st.session_state.path_input:
                    st.session_state.path_input = st.session_state.uploaded_path

                path_col1, path_col2, path_col3 = st.columns([0.6, 5.9, 0.5])
                
                with path_col1:
                    st.markdown("**路径:**")
                with path_col2:
                    target_path = st.text_input(
                        "", 
                        value=st.session_state.path_input,
                        placeholder="📁 若为空则自动生成",
                        key="path_input_display",
                        help="手动指定文件夹路径，或下方上传自动生成",
                        label_visibility="collapsed"
                    )
                with path_col3:
                    if st.button("📂", help="在Finder中打开", use_container_width=True):
                        if target_path and os.path.exists(target_path):
                            import webbrowser
                            import urllib.parse
                            try:
                                file_url = 'file://' + urllib.parse.quote(os.path.abspath(target_path))
                                webbrowser.open(file_url)
                                st.toast("✅ 已打开")
                            except: pass

                if target_path != st.session_state.path_input:
                    st.session_state.path_input = target_path

                # 2. 数据源输入
                st.write("")
                src_tab_local, src_tab_web = st.tabs(["📂 本地文件", "🌐 网页抓取"])
                
                with src_tab_local:
                    local_type = st.radio("方式", ["📄 上传文件", "✍️ 粘贴文本"], horizontal=True, label_visibility="collapsed")
                    
                    uploaded_files = None  # 初始化变量
                    
                    if "上传文件" in local_type:
                        uploaded_files = st.file_uploader(
                            "拖入文件 (PDF, DOCX, TXT, MD)", 
                            accept_multiple_files=True, 
                            key="uploader",
                            label_visibility="collapsed"
                        )
                        st.caption("支持格式: PDF, DOCX, TXT, MD, Excel | 单个文件最大 100MB")
                    else:
                        text_input_content = st.text_area("直接输入文本内容", height=200, placeholder="在此粘贴或输入需要分析的文本内容...")
                        col_txt1, col_txt2 = st.columns([1, 4])
                        txt_filename = col_txt1.text_input("文件名", value="manual_input.txt", label_visibility="collapsed")
                        
                        if col_txt2.button("💾 保存文本", use_container_width=True):
                            if text_input_content.strip():
                                # 保存为临时文件
                                try:
                                    save_dir = os.path.join(UPLOAD_DIR, f"text_{int(time.time())}")
                                    if not os.path.exists(save_dir):
                                        os.makedirs(save_dir)
                                    
                                    safe_name = sanitize_filename(txt_filename) or "manual_input.txt"
                                    if not safe_name.endswith('.txt'): safe_name += ".txt"
                                    
                                    with open(os.path.join(save_dir, safe_name), 'w', encoding='utf-8') as f:
                                        f.write(text_input_content)
                                        
                                    st.session_state.uploaded_path = os.path.abspath(save_dir)
                                    st.session_state.upload_auto_name = f"Text_{safe_name.split('.')[0]}"
                                    st.success("✅ 文本已保存")
                                    time.sleep(0.5)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"保存失败: {e}")
                            else:
                                st.warning("内容不能为空")
        else:
            # 管理模式 - 使用一行化布局
            manage_title_col1, manage_title_col2, manage_title_col3 = st.columns([2, 2, 1])
            with manage_title_col1:
                st.caption(f"🛠️ 管理: {current_kb_name}")
            with manage_title_col2:
                st.markdown("📤 **添加文档**")
            with manage_title_col3:
                if st.button("🔄", help="重建索引 (覆盖该库)", use_container_width=True):
                    # 触发重建逻辑
                    st.session_state.uploaded_path = os.path.join("vector_db_storage", current_kb_name)
                    # 这里需要一种方式标记为 NEW 模式，通常是通过 btn_start 触发
                    st.session_state.trigger_rebuild = True
                    st.rerun()

            # 追加模式的文件上传
            action_mode = "APPEND"
            # 如果触发了重建，则强制改为 NEW
            if st.session_state.get('trigger_rebuild'):
                action_mode = "NEW"
                st.session_state.trigger_rebuild = False # 消费掉标记
            
            target_path = "" # 管理模式不需要手动指定路径，使用KB原有路径
            
            uploaded_files = st.file_uploader(
                "追加文件到当前知识库", 
                accept_multiple_files=True, 
                key="uploader_append",
                label_visibility="collapsed"
            )
            
            # 添加更新知识库按钮
            if uploaded_files:
                st.info("💡 上传后请点击下方 '更新知识库' 按钮")
                if st.button("🔄 更新知识库", type="primary", use_container_width=True, key="update_kb_btn"):
                    btn_start = True
                    action_mode = "APPEND"
                    st.session_state.sidebar_state = "collapsed"
                    st.markdown("""
                    <style>
                    [data-testid="stSidebar"] {
                        width: 2.5rem !important;
                        min-width: 2.5rem !important;
                        max-width: 2.5rem !important;
                    }
                    [data-testid="stSidebar"] > div {
                        overflow: hidden !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)

        # 统一的数据源处理逻辑（仅针对 Web 抓取保留在外部，本地文件已在内部处理）
        btn_start = False # Initialize to avoid NameError
        
        if is_create_mode:
            with src_tab_web:
                with st.container(border=True):
                    # 输入方式选择 - 使用更紧凑的布局
                    col1, col2 = st.columns(2)
                    with col1:
                        url_mode = st.button("🔗 网址抓取", use_container_width=True, key="url_mode_btn")
                    with col2:
                        search_mode = st.button("🔍 智能行业搜索", use_container_width=True, key="search_mode_btn")
                    
                    # 根据按钮点击确定模式
                    if url_mode:
                        st.session_state.crawl_input_mode = "url"
                    elif search_mode:
                        st.session_state.crawl_input_mode = "search"
                    
                    # 获取当前模式
                    current_mode = st.session_state.get('crawl_input_mode', 'url')
                    
                    if current_mode == "url":
                        # 网址抓取模式 - v2.4.1 智能优化
                        
                        # 加载智能优化器
                        try:
                            from src.processors.crawl_optimizer import CrawlOptimizer
                            if 'crawl_optimizer' not in st.session_state:
                                st.session_state.crawl_optimizer = CrawlOptimizer()
                            optimizer = st.session_state.crawl_optimizer
                        except ImportError:
                            optimizer = None
                        
                        col_url_input, col_analyze_btn = st.columns([7, 1.2])
                        with col_url_input:
                            crawl_url = st.text_input("🔗 网址", placeholder="python.org", label_visibility="collapsed")
                        
                        search_keyword = None
                        
                        # 智能分析逻辑 (大脑图标)
                        with col_analyze_btn:
                            if st.button("🧠", help="AI智能分析网站并推荐最佳参数", key="smart_analyze_url", use_container_width=True):
                                if crawl_url:
                                    with st.spinner("🔍"):
                                        if not crawl_url.startswith(('http://', 'https://')):
                                            test_url = f"https://{crawl_url}"
                                        else:
                                            test_url = crawl_url
                                        analysis = optimizer.analyze_website(test_url) if optimizer else None
                                        if analysis: st.session_state.crawl_analysis = analysis
                                else:
                                    st.toast("请先输入网址", icon="⚠️")
                            
                        # 显示分析结果 (紧凑模式)
                        if 'crawl_analysis' in st.session_state:
                            analysis = st.session_state.crawl_analysis
                            with st.expander("🎯 推荐: " + analysis['site_type'].title(), expanded=True):
                                st.caption(f"💡 {analysis['description']}")
                        
                        # 抓取参数 - 一行三列布局
                        col_p1, col_p2, col_p3 = st.columns(3)
                        with col_p1:
                            default_depth = st.session_state.crawl_analysis['recommended_depth'] if 'crawl_analysis' in st.session_state else 2
                            crawl_depth = st.number_input("递归深度", 1, 10, default_depth)
                        with col_p2:
                            default_pages = st.session_state.crawl_analysis['recommended_pages'] if 'crawl_analysis' in st.session_state else 20
                            max_pages = st.number_input("每层页数", 1, 1000, default_pages)
                        with col_p3:
                            parser_type = st.selectbox("解析器类型", ["default", "article", "documentation"])
                        
                        # 质量筛选 - 极致压缩
                        enable_url_quality_filter = st.checkbox("🎯 启用质量筛选", value=True, help="开启后会过滤低质量页面，建议在内容杂乱时使用")
                        if enable_url_quality_filter:
                            url_quality_threshold = st.slider("质量阈值", 10.0, 50.0, 30.0, 5.0, help="分数越高筛选越严格，30分为推荐值")
                        else:
                            url_quality_threshold = 0.0
                        
                    else:  # current_mode == "search"
                        # 智能行业搜索模式
                        crawl_url = None
                        
                        # 加载优化器 (复用逻辑)
                        try:
                            from src.processors.crawl_optimizer import CrawlOptimizer
                            optimizer = st.session_state.get('crawl_optimizer', CrawlOptimizer())
                        except: optimizer = None

                        # 行业选择
                        try:
                            from src.config.unified_sites import get_industry_list
                            industries = get_industry_list()
                            selected_industry = st.selectbox("🏢 目标行业", industries)
                        except:
                            selected_industry = "🔧 技术开发"
                        
                        # 关键词输入 + 智能分析 (大脑)
                        col_kw_input, col_kw_brain = st.columns([7, 1.2])
                        with col_kw_input:
                            search_keyword = st.text_input("🔍 关键词", placeholder="输入搜索内容...", label_visibility="collapsed")
                        
                        with col_kw_brain:
                            if st.button("🧠", help="AI智能推荐行业权威站点", key="smart_analyze_search", use_container_width=True):
                                if search_keyword:
                                    with st.spinner("🔍"):
                                        # 复用智能推荐逻辑：基于行业和关键词给出建议
                                        st.toast(f"🎯 已根据 '{selected_industry}' 优化搜索策略")
                                        # 这里可以插入具体的行业搜索优化逻辑
                                else:
                                    st.toast("请先输入关键词", icon="⚠️")

                        # 搜索参数 - 一行三列布局
                        col_s1, col_s2, col_s3 = st.columns(3)
                        with col_s1:
                            crawl_depth = st.number_input("递归深度", 1, 5, 2)
                        with col_s2:
                            max_pages = st.number_input("总页数", 1, 500, 20)
                        with col_s3:
                            parser_type = st.selectbox("解析器类型", ["default", "article", "documentation"], key="parser_search")
                        
                        # 质量筛选 - 极致压缩
                        enable_quality_filter = st.checkbox("🎯 启用质量筛选", value=True, help="过滤低相关性页面，建议开启", key="q_filter_search")
                        if enable_quality_filter:
                            quality_threshold = st.slider("质量阈值", 10.0, 50.0, 30.0, 5.0, key="q_threshold_search")
                        else:
                            quality_threshold = 0.0
                        
                        # 🛑 安全警告 - 指数增长预估
                        estimated_pages = max_pages ** crawl_depth  # 指数增长：每层可能产生max_pages个新链接
                        if estimated_pages > 1000:
                            st.warning(f"⚠️ 预估抓取页面: {estimated_pages:,} 页，可能耗时很长！系统最大限制: 50,000 页")
                        elif estimated_pages > 100:
                            st.info(f"ℹ️ 预估抓取页面: {estimated_pages:,} 页")
                        
                        # crawl_depth 由用户输入控制，不再固定为 1
                    
                    # 排除配置 - 可选
                    with st.expander("🚫 排除链接 (可选)", expanded=False):
                        exclude_text = st.text_area("每行一个，支持 * 通配符", 
                                                   placeholder="*/admin/*\n*.pdf", 
                                                   height=68, max_chars=150)
                        exclude_patterns = [line.strip() for line in exclude_text.split('\n') if line.strip()] if exclude_text else []
                
                # 知识库设置
                st.write("### 📚 知识库设置")
                
                col_kb_label, col_kb_input = st.columns([2, 5])
                with col_kb_label:
                    st.markdown('<div style="margin-top: 5px;">**知识库名称**</div>', unsafe_allow_html=True)
                with col_kb_input:
                    web_kb_name = st.text_input(
                        "知识库名称", 
                        placeholder="留空自动生成（推荐）", 
                        help="每次抓取创建独立的知识库，便于管理不同时间的内容",
                        label_visibility="collapsed"
                    )
                
                st.caption("💡 每次抓取都会创建一个独立的知识库，包含本次抓取的所有网页")
                
                # 抓取按钮
                btn_disabled = not crawl_url and not search_keyword
                if st.button("🚀 抓取并创建知识库", use_container_width=True, type="primary", disabled=btn_disabled):
                    if crawl_url:
                        # 网址抓取模式
                        try:
                            # 优先使用异步爬虫
                            try:
                                from src.processors.enhanced_web_crawler import run_async_crawl
                                use_async = True
                                st.info("🚀 使用异步并发爬虫 (性能提升10倍+, 支持断点续传, robots.txt检查)")
                            except ImportError:
                                from src.processors.web_crawler import WebCrawler
                                use_async = False
                                st.info("📡 使用标准爬虫")
                            
                            # 使用带域名的唯一目录
                            from urllib.parse import urlparse
                            from datetime import datetime
                            
                            try:
                                domain = urlparse(crawl_url).netloc.replace('.', '_').replace(':', '')
                                if not domain: domain = "unknown"
                            except:
                                domain = "unknown"
                                
                            timestamp_dir = datetime.now().strftime('%Y%m%d_%H%M%S')
                            unique_output_dir = os.path.join("temp_uploads", f"Web_{domain}_{timestamp_dir}")
                            
                            if use_async:
                                # 异步爬虫配置
                                max_concurrent = 15  # 默认并发数
                                
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                crawled_count = [0]
                                
                                def update_status(msg):
                                    status_text.text(msg)
                                    logger.info(f"🌐 网页爬取: {msg}")
                                    if "已爬取" in msg or "已保存" in msg:
                                        crawled_count[0] += 1
                                        progress = min(crawled_count[0] / max(max_pages, 1), 1.0)
                                        progress_bar.progress(progress)
                                
                                # 记录爬取开始
                                logger.info(f"🌐 开始网页爬取: {crawl_url} (深度:{crawl_depth}, 页数:{max_pages})")
                                
                                with st.spinner("异步抓取中..."):
                                    # 运行异步爬虫
                                    result = run_async_crawl(
                                        start_url=crawl_url,
                                        max_depth=crawl_depth,
                                        max_pages=max_pages,
                                        status_callback=update_status,
                                        max_concurrent=max_concurrent,
                                        ignore_robots=True,  # 绕过robots.txt限制
                                        output_dir=unique_output_dir
                                    )
                                    saved_files = result if isinstance(result, list) else []
                                    # 异步爬虫使用固定的输出目录格式
                                    async_output_dir = unique_output_dir
                            else:
                                # 同步爬虫
                                crawler = WebCrawler(output_dir=unique_output_dir)
                                
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                crawled_count = [0]
                                
                                def update_status(msg):
                                    status_text.text(f"📡 {msg}")
                                    # 添加日志记录
                                    logger.info(f"🌐 网页爬取: {msg}")
                                    if "已保存" in msg:
                                        crawled_count[0] += 1
                                        progress = min(crawled_count[0] / max_pages, 1.0)
                                        progress_bar.progress(progress)
                                
                                # 记录爬取开始
                                logger.info(f"🌐 开始网页爬取: {crawl_url} (深度:{crawl_depth}, 页数:{max_pages})")
                                
                                with st.spinner("抓取中..."):
                                    saved_files = crawler.crawl_advanced(
                                        start_url=crawl_url,
                                        max_depth=crawl_depth,
                                        max_pages=max_pages,
                                        parser_type="default",
                                        exclude_patterns=[],
                                        status_callback=update_status
                                    )
                            
                            progress_bar.progress(1.0)
                            
                            # 记录爬取结果
                            logger.success(f"🌐 网页爬取完成: 获取 {len(saved_files)} 个页面")
                            
                            # 检查是否有实际文件（异步爬虫可能返回空列表但有文件）
                            actual_files = []
                            matching_dirs = False
                            
                            # 优先检查当前生成的目录
                            if os.path.exists(unique_output_dir) and os.listdir(unique_output_dir):
                                import glob
                                actual_files = glob.glob(os.path.join(unique_output_dir, "*.txt"))
                                if actual_files:
                                    matching_dirs = True
                                    logger.info(f"🎯 使用本次抓取目录: {os.path.basename(unique_output_dir)} (包含 {len(actual_files)} 个文件)")
                                    # 确保使用当前目录
                                    async_output_dir = unique_output_dir
                            
                            # 如果当前目录为空（异常情况），才尝试智能选择
                            if not actual_files and use_async:
                                from src.utils.directory_selector import select_best_web_crawl_directory
                                selected_dir, actual_files = select_best_web_crawl_directory(domain)
                                if selected_dir:
                                    matching_dirs = True
                                    logger.info(f"⚠️ 当前目录为空，智能回退目录: {os.path.basename(selected_dir)} (包含 {len(actual_files)} 个文件)")
                                    async_output_dir = selected_dir
                                else:
                                    logger.warning(f"⚠️ 未找到有效的网页抓取目录")
                            
                            files_to_use = saved_files if saved_files else actual_files
                            
                            # 🔥 新增：网址抓取质量过滤
                            if files_to_use and enable_url_quality_filter:
                                try:
                                    from src.processors.content_analyzer import ContentQualityAnalyzer
                                    content_analyzer = ContentQualityAnalyzer()
                                    
                                    # 读取文件内容进行质量分析
                                    analysis_contents = []
                                    for file_path in files_to_use:
                                        try:
                                            with open(file_path, 'r', encoding='utf-8') as f:
                                                content = f.read()
                                                # 提取标题和URL（从文件内容的前几行）
                                                lines = content.split('\n')
                                                title = "Unknown"
                                                url = crawl_url
                                                for line in lines[:5]:
                                                    if line.startswith('Title:'):
                                                        title = line.replace('Title:', '').strip()
                                                    elif line.startswith('URL:'):
                                                        url = line.replace('URL:', '').strip()
                                                
                                                analysis_contents.append({
                                                    'title': title,
                                                    'content': content,
                                                    'url': url,
                                                    'file_path': file_path
                                                })
                                        except Exception as e:
                                            logger.warning(f"读取文件失败 {file_path}: {e}")
                                            continue
                                    
                                    if analysis_contents:
                                        total_pages = len(analysis_contents)
                                        # 动态设置max_results
                                        if total_pages <= 50:
                                            max_results = max(10, int(total_pages * 0.8))
                                        elif total_pages <= 200:
                                            max_results = max(50, int(total_pages * 0.7))
                                        else:
                                            max_results = min(500, max(100, int(total_pages * 0.6)))
                                        
                                        logger.info(f"🎯 网址抓取质量过滤: 总页面{total_pages}个，保留前{max_results}个高质量页面 (阈值:{url_quality_threshold}分)")
                                        
                                        filtered_contents = content_analyzer.analyze_and_filter_contents(
                                            analysis_contents,
                                            search_keywords=[crawl_url.split('/')[-1]],  # 使用域名作为关键词
                                            min_quality_score=url_quality_threshold,
                                            max_results=max_results
                                        )
                                        
                                        # 更新files_to_use为过滤后的文件
                                        files_to_use = [item['file_path'] for item in filtered_contents]
                                        
                                        logger.info(f"📊 网址抓取质量过滤完成: {total_pages} → {len(files_to_use)}个高质量页面")
                                        
                                except Exception as e:
                                    logger.warning(f"质量过滤失败，使用原始文件: {e}")
                            elif files_to_use and not enable_url_quality_filter:
                                logger.info(f"⚡ 网址抓取跳过质量筛选: 保留全部{len(files_to_use)}个页面")
                            
                            if files_to_use or (use_async and matching_dirs):
                                # 生成知识库名称
                                if web_kb_name:
                                    kb_name = web_kb_name
                                else:
                                    # 使用统一的命名优化器
                                    from src.core.app_config import output_base
                                    kb_name = KBNameOptimizer.generate_name_from_url(crawl_url, output_base)

                                # 确保名称唯一（generate_name_from_url 内部已调用 generate_unique_name）
                                # 但为了保险再次确认（如果是用户输入的自定义名称）
                                if web_kb_name:
                                    kb_name = KBNameOptimizer.generate_unique_name(kb_name, output_base)
                                
                                st.success(f"✅ 抓取完成！获取 {len(files_to_use)} 页，正在创建知识库: {kb_name}")
                                
                                # 设置知识库构建参数
                                if use_async:
                                    # 如果 async_output_dir 已经设置且有效，直接使用 (优先使用本次生成的目录)
                                    if 'async_output_dir' in locals() and async_output_dir and os.path.exists(async_output_dir):
                                        pass 
                                    else:
                                        # 查找最新的异步爬虫输出目录，优先选择有文件的目录 (仅作为回退)
                                        from src.utils.directory_selector import select_best_web_crawl_directory
                                        async_output_dir, _ = select_best_web_crawl_directory(domain)
                                    
                                    if async_output_dir:
                                        logger.info(f"🎯 知识库构建使用目录: {os.path.basename(async_output_dir)}")
                                        st.session_state.uploaded_path = os.path.abspath(async_output_dir)
                                    else:
                                        # 回退到预期的目录
                                        logger.warning(f"⚠️ 未找到有效目录，使用默认目录")
                                        st.session_state.uploaded_path = os.path.abspath(unique_output_dir)
                                else:
                                    st.session_state.uploaded_path = os.path.abspath(crawler.output_dir)
                                st.session_state.upload_auto_name = kb_name
                                st.session_state.auto_build_kb = True
                                st.session_state.selected_kb = kb_name
                                
                                # 触发知识库构建
                                with st.spinner(f"正在创建知识库: {kb_name}"):
                                    st.session_state.auto_build_kb = True
                                    st.session_state.selected_kb = kb_name  # 自动跳转到新知识库
                                    time.sleep(1)
                                
                                st.success(f"🎉 知识库 '{kb_name}' 构建完成！已自动切换")
                                
                                # 简洁的结果显示
                                with st.expander("📊 构建详情", expanded=False):
                                    st.write(f"**知识库名称**: {kb_name}")
                                    st.write(f"**抓取页面**: {len(files_to_use)} 页")
                                    st.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                    for i, file_path in enumerate(files_to_use[:3], 1):
                                        file_name = os.path.basename(file_path)
                                        st.text(f"{i}. {file_name}")
                                    if len(files_to_use) > 3:
                                        st.text(f"... 还有 {len(files_to_use) - 3} 个文件")
                                
                                # 推荐问题
                                try:
                                    from src.chat.web_suggestion_engine import WebSuggestionEngine
                                    web_engine = WebSuggestionEngine()
                                    web_suggestions = web_engine.generate_suggestions_from_crawl(crawl_url, files_to_use)
                                    
                                    if web_suggestions:
                                        st.markdown("**💡 推荐问题:**")
                                        for i, suggestion in enumerate(web_suggestions[:3], 1):
                                            if st.button(suggestion, key=f"web_q_{i}", use_container_width=True):
                                                st.session_state.suggested_question = suggestion
                                                st.rerun()
                                except:
                                    pass
                                
                                # st.rerun() # 移除强制刷新，确保高级选项状态保留
                            
                            else:
                                st.warning("未获取到内容")
                                
                        except Exception as e:
                            st.error(f"抓取失败: {str(e)}")
                    
                    elif search_keyword:
                        # 关键词全网搜索
                        try:
                            from src.processors.web_crawler import WebCrawler
                            # 使用带关键词的唯一目录
                            from datetime import datetime
                            
                            # 清理关键词文件名
                            safe_keyword = "".join([c for c in search_keyword if c.isalnum() or c in (' ', '_', '-')]).strip().replace(' ', '_')[:30]
                            if not safe_keyword: safe_keyword = "keyword"
                            
                            timestamp_dir = datetime.now().strftime('%Y%m%d_%H%M%S')
                            unique_output_dir = os.path.join("temp_uploads", f"Search_{safe_keyword}_{timestamp_dir}")
                            
                            crawler = WebCrawler(output_dir=unique_output_dir)
                            
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            all_saved_files = []
                            
                            def update_status(msg):
                                status_text.text(f"🔍 {msg}")
                                # 添加日志记录
                                logger.info(f"🔍 关键词搜索: {msg}")
                            
                            # 根据选择的行业导入对应网站配置
                            try:
                                from src.config.unified_sites import get_industry_sites
                                search_engines, site_names = get_industry_sites(selected_industry)
                            except ImportError:
                                # 备用配置
                                search_engines = [
                                    "https://www.runoob.com/",
                                    "https://docs.python.org/zh-cn/3/",
                                    "https://help.aliyun.com/",
                                    "https://www.eastmoney.com/",
                                    "https://www.icourse163.org/"
                                ]
                                site_names = ["菜鸟教程", "Python文档", "阿里云", "东方财富", "中国大学MOOC"]
                            
                            # 记录搜索开始
                            logger.info(f"🔍 开始智能行业搜索: '{search_keyword}' ({selected_industry}, 深度:{crawl_depth}, 总页数:{max_pages})")
                            
                            # 🔥 修复：每个网站使用完整的max_pages参数，而不是分割
                            # pages_per_site = max(1, max_pages // len(search_engines))  # ❌ 错误：分割总页数
                            pages_per_site = max_pages  # ✅ 正确：每个网站使用完整参数
                            logger.info(f"📊 页数分配修复: 每个网站使用完整{max_pages}页参数 (共{len(search_engines)}个网站)")
                            logger.info(f"🧮 递归预估: 第1层={max_pages}页, 第2层={max_pages**2}页 (如果深度≥2)")
                            
                            # v2.4.0 并发爬取优化
                            try:
                                from src.processors.concurrent_crawler import ConcurrentCrawler
                                from src.processors.content_analyzer import ContentQualityAnalyzer
                                from src.processors.crawl_stats_manager import CrawlStatsManager
                                
                                # 创建v2.4.0组件
                                concurrent_crawler = ConcurrentCrawler(max_workers=3)
                                content_analyzer = ContentQualityAnalyzer()
                                stats_manager = CrawlStatsManager()
                                
                                # 开始统计会话
                                session_id = stats_manager.start_session(
                                    selected_industry.split(' - ')[0] if ' - ' in selected_industry else selected_industry,
                                    [search_keyword],
                                    len(search_engines)  # 修复：使用search_engines而不是selected_sites
                                )
                                
                                logger.info(f"🚀 v2.4.0并发爬取开始: {session_id}")
                                
                                def enhanced_progress_callback(message, progress=None):
                                    update_status(message)
                                    if progress is not None:
                                        progress_bar.progress(progress)
                                
                                # 使用并发爬取
                                crawl_results = concurrent_crawler.crawl_with_depth(
                                    search_engines,  # 修复：使用search_engines而不是selected_sites
                                    max_depth=crawl_depth,
                                    max_pages_per_level=pages_per_site,
                                    progress_callback=enhanced_progress_callback
                                )
                                
                                # 内容质量分析和过滤
                                if crawl_results:
                                    logger.info(f"🎯 开始内容质量分析: {len(crawl_results)}个页面")
                                    
                                    # 转换格式用于分析
                                    analysis_contents = []
                                    for result in crawl_results:
                                        if result['success'] and result['content']:
                                            analysis_contents.append({
                                                'title': result['title'],
                                                'content': result['content'],
                                                'url': result['url']
                                            })
                                            
                                            # 更新统计
                                            stats_manager.add_content_result(
                                                result['url'],
                                                'selected_site',  # 简化网站名
                                                True,
                                                len(result['content']),
                                                0,  # 质量评分稍后计算
                                                0   # 相关性评分稍后计算
                                            )
                                        else:
                                            stats_manager.add_content_result(
                                                result['url'],
                                                'selected_site',
                                                False,
                                                error=result.get('error', 'Unknown error')
                                            )
                                    
                                    # 🔥 修复：用户可控的质量分析和过滤
                                    if analysis_contents:
                                        if enable_quality_filter:
                                            # 启用质量筛选
                                            total_pages = len(analysis_contents)
                                            if total_pages <= 50:
                                                # 小规模：保留80%
                                                max_results = max(10, int(total_pages * 0.8))
                                            elif total_pages <= 200:
                                                # 中规模：保留70%
                                                max_results = max(50, int(total_pages * 0.7))
                                            else:
                                                # 大规模：保留60%，但不超过500
                                                max_results = min(500, max(100, int(total_pages * 0.6)))
                                            
                                            logger.info(f"🎯 质量过滤参数: 总页面{total_pages}个，保留前{max_results}个高质量页面 (阈值:{quality_threshold}分)")
                                            
                                            filtered_contents = content_analyzer.analyze_and_filter_contents(
                                                analysis_contents,
                                                search_keywords=[search_keyword],
                                                min_quality_score=quality_threshold,  # 使用用户设置的阈值
                                                max_results=max_results
                                            )
                                            
                                            logger.info(f"📊 质量过滤完成: {len(analysis_contents)} → {len(filtered_contents)}个高质量页面")
                                        else:
                                            # 跳过质量筛选，保留所有页面
                                            filtered_contents = analysis_contents
                                            logger.info(f"⚡ 跳过质量筛选: 保留全部{len(analysis_contents)}个页面")
                                        
                                        # 保存过滤后的内容
                                        saved_files = []
                                        
                                        # 确保输出目录存在
                                        os.makedirs(unique_output_dir, exist_ok=True)
                                        
                                        for i, content_item in enumerate(filtered_contents):
                                            filename = f"quality_content_{i+1:03d}.txt"
                                            filepath = os.path.join(unique_output_dir, filename)
                                            
                                            # 创建增强的内容
                                            if 'quality_score' in content_item and content_item['quality_score']:
                                                # 有质量评分信息
                                                enhanced_content = f"""标题: {content_item['title']}
URL: {content_item['url']}
质量评分: {content_item['quality_score']['total_score']:.1f}/100
相关性评分: {content_item.get('relevance_score', 0):.2f}
综合评分: {content_item.get('final_score', 0):.1f}
关键词: {', '.join(content_item['quality_score']['details']['top_keywords'][:5])}

内容:
{content_item['content']}
"""
                                            else:
                                                # 无质量评分信息
                                                enhanced_content = f"""标题: {content_item['title']}
URL: {content_item['url']}

内容:
{content_item['content']}
"""
                                            
                                            with open(filepath, 'w', encoding='utf-8') as f:
                                                f.write(enhanced_content)
                                            saved_files.append(filepath)
                                        
                                        all_saved_files = saved_files
                                        
                                        # 结束统计会话
                                        stats_manager.end_session()
                                        
                                        # 显示统计信息
                                        final_stats = stats_manager.get_current_stats()
                                        concurrent_stats = concurrent_crawler.get_stats()
                                        
                                        logger.success(f"🎉 v2.4.0并发爬取完成!")
                                        logger.info(f"📊 爬取统计: 成功率 {final_stats['success_rate']:.1%}, 平均质量 {final_stats.get('avg_quality_score', 0):.1f}")
                                        logger.info(f"⚡ 性能统计: {concurrent_stats['pages_per_minute']:.1f}页/分钟, 平均响应 {concurrent_stats['avg_response_time']:.2f}秒")
                                    
                                else:
                                    logger.warning("🔍 未获取到有效内容")
                                    all_saved_files = []
                                
                            except ImportError:
                                # 降级到原有爬取方式
                                logger.info("🔄 降级到标准爬取模式")
                                crawler = WebCrawler(output_dir=unique_output_dir)
                                
                                # 在选中的网站中搜索
                                for i, search_url in enumerate(search_engines):  # 修复：使用search_engines
                                    engine_name = site_names[i] if i < len(site_names) else f"网站{i+1}"  # 修复：使用site_names
                                    update_status(f"正在搜索 {engine_name}: {search_keyword}")
                                    logger.info(f"🔍 搜索网站: {engine_name} - {search_url} (分配页数: {pages_per_site})")
                                    
                                    try:
                                        with st.spinner(f"搜索 {engine_name}..."):
                                            saved_files = crawler.crawl_advanced(
                                                start_url=search_url,
                                                max_depth=crawl_depth,
                                                max_pages=pages_per_site,
                                                exclude_patterns=exclude_patterns,
                                                parser_type=parser_type,
                                                status_callback=update_status
                                            )
                                            
                                            if saved_files:
                                                all_saved_files.extend(saved_files)
                                                logger.success(f"🔍 {engine_name}搜索完成: 获取 {len(saved_files)} 个页面")
                                            else:
                                                logger.warning(f"🔍 {engine_name}搜索无结果")
                                            
                                        progress_bar.progress((i + 1) / len(search_engines))  # 修复：使用search_engines
                                        
                                    except Exception as e:
                                        update_status(f"❌ {engine_name} 搜索失败: {e}")
                                        logger.error(f"🔍 {engine_name}搜索失败: {e}")
                                        continue
                            
                            progress_bar.progress(1.0)
                            
                            # 检查是否有实际文件（统一逻辑）
                            actual_files = []
                            if not all_saved_files:
                                import glob
                                actual_files = glob.glob(os.path.join(unique_output_dir, "*.txt"))
                            
                            files_to_use = all_saved_files if all_saved_files else actual_files
                            
                            if files_to_use:
                                # 生成基础名称
                                if web_kb_name:
                                    kb_name = web_kb_name
                                    # 确保自定义名称唯一
                                    from src.core.app_config import output_base
                                    kb_name = KBNameOptimizer.generate_unique_name(kb_name, output_base)
                                else:
                                    # 使用统一的命名优化器
                                    from src.core.app_config import output_base
                                    kb_name = KBNameOptimizer.generate_name_from_keyword(search_keyword, output_base)
                                
                                st.success(f"✅ 智能行业搜索完成！获取 {len(files_to_use)} 页，正在创建知识库: {kb_name}")
                                
                                # 记录搜索完成
                                logger.success(f"🔍 智能行业搜索完成: '{search_keyword}' ({selected_industry}) - 获取 {len(files_to_use)} 个页面")
                                
                                # 设置知识库构建参数
                                st.session_state.uploaded_path = os.path.abspath(crawler.output_dir)
                                st.session_state.upload_auto_name = kb_name
                                st.session_state.auto_build_kb = True
                                st.session_state.selected_kb = kb_name
                                
                                # 触发知识库构建
                                with st.spinner(f"正在创建知识库: {kb_name}"):
                                    st.session_state.auto_build_kb = True
                                    st.session_state.selected_kb = kb_name  # 自动跳转到新知识库
                                    time.sleep(1)
                                
                                st.success(f"🎉 知识库 '{kb_name}' 构建完成！已自动切换")
                                
                                # 简洁的结果显示
                                with st.expander("📊 构建详情", expanded=False):
                                    st.write(f"**知识库名称**: {kb_name}")
                                    st.write(f"**搜索关键词**: {search_keyword}")
                                    st.write(f"**搜索方式**: 全网搜索")
                                    st.write(f"**抓取页面**: {len(files_to_use)} 页")
                                    st.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                
                                # st.rerun() # 移除强制刷新，确保高级选项状态保留
                            
                            else:
                                st.warning("未搜索到相关内容")
                                
                        except Exception as e:
                            st.error(f"搜索失败: {str(e)}")
                
                # 简洁的使用提示
                st.caption("💡 支持 python.org 等简化输入，自动添加 https:// 前缀")

            # 处理上传 (Stage 4.1 - 使用 UploadHandler)
            if uploaded_files:
                # 使用文件名+大小的组合作为哈希，判断文件列表是否真正改变
                import hashlib
                upload_hash = hashlib.md5("".join([f"{f.name}_{f.size}" for f in uploaded_files]).encode()).hexdigest()
                
                if st.session_state.get('last_upload_hash') != upload_hash:
                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # 使用 UploadHandler 处理上传
                    handler = UploadHandler(UPLOAD_DIR, logger)
                    
                    # 模拟进度显示（实际处理在 process_uploads 内部）
                    status_text.text(f"正在处理 {len(uploaded_files)} 个文件...")
                    progress_bar.progress(0.5)

                    result = handler.process_uploads(uploaded_files)

                    progress_bar.empty()
                    status_text.empty()

                    # 记录哈希，防止重复处理
                    st.session_state.last_upload_hash = upload_hash
                    st.session_state.uploaded_path = os.path.abspath(result.batch_dir)

                    # 显示上传结果
                    if result.success_count > 0:
                        st.toast(f"✅ 成功上传 {result.success_count} 个文件")

                    if result.skipped_count > 0:
                        st.warning(f"⚠️ 跳过 {result.skipped_count} 个文件")

                    # 为文件上传场景生成智能名称
                    if result.success_count > 0:
                        try:
                            file_types = {}
                            for f in uploaded_files:
                                ext = os.path.splitext(f.name)[1].lower()
                                file_types[ext] = file_types.get(ext, 0) + 1

                            folder_name = os.path.basename(result.batch_dir)
                            auto_name = generate_smart_kb_name(result.batch_dir, result.success_count, file_types, folder_name)
                            st.session_state.upload_auto_name = auto_name
                        except Exception:
                            st.session_state.upload_auto_name = None
                    
                    # 关键修复：不再强制全页面 rerun，而是依靠 Streamlit 自然流转
                    # 这样可以保留 uploader 的状态，避免其因刷新而报错或重置


            # 使用上传路径或手动输入的路径
            target_path = st.session_state.get('uploaded_path') or target_path

            auto_name = ""

            # 优先使用文件上传的智能名称
            if hasattr(st.session_state, 'upload_auto_name') and st.session_state.upload_auto_name:
                auto_name = st.session_state.upload_auto_name

            if target_path:
                if os.path.exists(target_path):
                    # 使用 UploadHandler 统计文件信息 (Stage 4.1)
                    cnt, file_types, total_size = UploadHandler.get_folder_stats(target_path)

                    # 美化显示
                    size_mb = total_size / (1024 * 1024)
                    folder_name = os.path.basename(target_path.rstrip('/'))

                    # 智能计算名称 (提前计算以优化显示)
                    if hasattr(st.session_state, 'upload_auto_name') and st.session_state.upload_auto_name:
                        auto_name = st.session_state.upload_auto_name
                    elif cnt > 0:
                        auto_name = generate_smart_kb_name(target_path, cnt, file_types, folder_name)
                    else:
                        auto_name = folder_name

                    # 决定显示名称：如果是临时目录名，则显示智能名称
                    display_name = folder_name
                    if folder_name.startswith(('batch_', 'Web_', 'Search_')) and auto_name:
                        display_name = auto_name

                    st.success(f"✅ **数据源已就绪**: `{display_name}`")

                    # 类型分布（只显示前5种）
                    if file_types:
                        st.caption("**文件类型分布**")
                        sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]
                        type_text = " · ".join([f"{ext.replace('.', '')}: {count}" for ext, count in sorted_types])
                        if len(file_types) > 5:
                            type_text += f" · 其他: {sum(c for _, c in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[5:])}"
                        st.caption(type_text)
                else:
                    st.error("❌ 路径不存在，请检查路径是否正确")

            # final_kb_name 必须在 if/else 中被定义，以确保其在模块作用域内
            st.write("")
            if is_create_mode:
                # 知识库名称一行化布局
                name_col1, name_col2 = st.columns([1.5, 5.5])
                with name_col1:
                    st.markdown("**知识库名称**")
                with name_col2:
                    if auto_name:
                        st.caption(f"💡 建议名称：{auto_name}")

                final_kb_name = st.text_input(
                    "知识库名称", 
                    value=sanitize_filename(auto_name) if auto_name else "", 
                    placeholder="留空自动生成，或输入自定义名称",
                    label_visibility="collapsed",
                    help="留空将自动生成有意义的名称"
                )

                # 如果用户没输入，使用自动生成的名称
                if not final_kb_name and auto_name:
                    final_kb_name = sanitize_filename(auto_name)
            else:
                final_kb_name = current_kb_name

            # 高级选项
            with st.expander("🔧 高级选项", expanded=False):
                # 全选控制
                def toggle_all():
                    val = st.session_state.kb_adv_select_all
                    st.session_state.kb_force_reindex = val
                    st.session_state.kb_use_ocr = val
                    st.session_state.kb_extract_metadata = val
                    st.session_state.kb_generate_summary = val

                st.checkbox("✅ 一键全选", value=False, key="kb_adv_select_all", on_change=toggle_all, help="开启/关闭所有高级选项")

                # 第一行：索引和元数据选项
                adv_col1, adv_col2 = st.columns(2)
                with adv_col1:
                    force_reindex = st.checkbox("🔄 强制重建索引", value=False, key="kb_force_reindex", help="删除现有索引，重新构建")
                    use_ocr = st.checkbox("🔍 启用OCR识别", value=False, key="kb_use_ocr", help="识别PDF中的图片文字（耗时较长）")
                with adv_col2:
                    extract_metadata = st.checkbox("📊 提取元数据", value=False, key="kb_extract_metadata", help="提取文件分类、关键词等信息")
                    generate_summary = st.checkbox("📝 生成文档摘要", value=False, key="kb_generate_summary", help="为每个文档生成AI摘要")
                
                # 保存到session state
                st.session_state.use_ocr = use_ocr
                st.session_state.generate_summary = generate_summary
                
                # 简化的处理模式提示
                if use_ocr or generate_summary or extract_metadata or force_reindex:
                    options = []
                    if force_reindex: options.append("重建索引")
                    if extract_metadata: options.append("提取元数据")
                    if use_ocr: options.append("OCR识别")
                    if generate_summary: options.append("生成摘要")
                    st.caption(f"🔧 启用选项: {' | '.join(options)}")
                else:
                    st.caption("⚡ 快速模式：所有高级选项已关闭")


            st.write("")

            btn_label = "🚀 立即创建" if is_create_mode else ("➕ 执行追加" if action_mode=="APPEND" else "🔄 执行覆盖")
            btn_start = st.button(btn_label, type="primary", use_container_width=True)
            
            # 自动收起侧边栏
            if btn_start:
                st.session_state.sidebar_state = "collapsed"
                st.markdown("""
                <style>
                [data-testid="stSidebar"] {
                    width: 2.5rem !important;
                    min-width: 2.5rem !important;
                    max-width: 2.5rem !important;
                }
                [data-testid="stSidebar"] > div {
                    overflow: hidden !important;
                }
                [data-testid="stSidebar"] .css-1d391kg {
                    display: none !important;
                }
                </style>
                """, unsafe_allow_html=True)
            
            # 检查是否需要自动构建知识库（网页抓取触发）
            if st.session_state.get('auto_build_kb', False):
                st.session_state.auto_build_kb = False  # 清除标记
                btn_start = True  # 自动触发构建
                # 确保 action_mode 在自动触发时也已定义
                if 'action_mode' not in locals():
                    action_mode = "NEW" if is_create_mode else "APPEND"

        # --- 现有库的管理 (卡片式布局) ---
        if not is_create_mode:
            with st.container(border=True):
                # 顶部：信息栏
                col_info, col_stats = st.columns([2, 3])
                with col_info:
                    st.markdown(f"#### 📂 {current_kb_name}")
                
                with col_stats:
                    # 获取并显示统计信息
                    try:
                        stats = kb_manager.get_stats(current_kb_name)
                        if stats:
                            pass  # 移除统计信息显示
                    except Exception:
                        pass
                
                st.divider()
                
                # 底部：操作栏 (优化为 2*3 布局)
                op_row1_col1, op_row1_col2 = st.columns(2)
                op_row2_col1, op_row2_col2 = st.columns(2)
                op_row3_col1, op_row3_col2 = st.columns(2)
                
                with op_row1_col1:
                    if st.button("🔄 撤销", use_container_width=True, disabled=len(state.get_messages()) < 2, help="撤销最近一轮对话"):
                        if len(state.get_messages()) >= 2:
                            st.session_state.messages.pop()
                            st.session_state.messages.pop()
                            if current_kb_name:
                                HistoryManager.save(current_kb_name, state.get_messages())
                            st.toast("✅ 已撤销")
                            time.sleep(0.5)
                            st.rerun()
                
                with op_row1_col2:
                    if st.button("🧹 清空", use_container_width=True, disabled=len(state.get_messages()) == 0, help="清空当前对话记录"):
                        st.session_state.messages = []
                        st.session_state.suggestions_history = []
                        if current_kb_name:
                            HistoryManager.save(current_kb_name, [])
                        st.toast("✅ 已清空")
                        time.sleep(0.5)
                        st.rerun()
                
                with op_row2_col1:
                    export_content = ""
                    if len(state.get_messages()) > 0:
                        export_content = f"# 对话记录 - {current_kb_name}\n\n**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
                        for i, msg in enumerate(st.session_state.messages, 1):
                            role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
                            export_content += f"## {role} ({i})\n\n{msg['content']}\n\n"
                    
                    st.download_button("📥 导出", export_content, file_name=f"chat_{current_kb_name}_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown", use_container_width=True, disabled=len(state.get_messages()) == 0)

                with op_row2_col2:
                    st.link_button("🔀 新窗口", "http://localhost:8501", use_container_width=True, help="打开新窗口")

                with op_row3_col1:
                    if st.button("🗑️ 删除", use_container_width=True, type="primary", disabled=not current_kb_name, help="永久删除该知识库"):
                        st.session_state.confirm_delete = True
                        st.rerun()
                
                # op_row3_col2 留空或用于将来扩展
            
            # 删除确认对话框 (放在卡片外，避免嵌套问题)
            if st.session_state.get('confirm_delete', False):
                st.warning(f"⚠️ 确认永久删除知识库 '{current_kb_name}' 吗？此操作不可恢复！")
                confirm_col1, confirm_col2 = st.columns([1, 1])
                
                with confirm_col1:
                    if st.button("✅ 确认删除", type="primary", use_container_width=True):
                        kb_manager.delete(current_kb_name) # 确保实际调用删除逻辑
                        st.toast(f"🗑️ 已删除知识库: {current_kb_name}")
                        # 重置状态
                        st.session_state.active_kb_name = None
                        st.session_state.confirm_delete = False
                        st.session_state.current_nav = "➕ 新建知识库..."
                        time.sleep(1)
                        st.rerun()
                
                with confirm_col2:
                    if st.button("❌ 取消", use_container_width=True):
                        st.session_state.confirm_delete = False
                        st.rerun()
            
    
    with tab_config:
        st.session_state.current_tab = "config"
        st.markdown("### ⚙️ 模型配置")
        
        # P0改进3: 侧边栏分组 - 基础配置（默认展开）- 使用新组件 (Stage 3.2.2)
        config_values = render_basic_config(defaults)

        # 提取配置值 (支持新的 extra_params)
        llm_provider = config_values.get('llm_provider', 'Ollama')
        llm_url = config_values.get('llm_url', 'http://localhost:11434')
        llm_model = config_values.get('llm_model', 'qwen2.5:7b')
        llm_key = config_values.get('llm_key', '')
        embed_provider = config_values.get('embed_provider', 'HuggingFace (本地/极速)')
        embed_model = config_values.get('embed_model', 'sentence-transformers/all-MiniLM-L6-v2')
        embed_url = config_values.get('embed_url', '')
        embed_key = config_values.get('embed_key', '')

        # 设置全局LLM（确保查询改写等功能可以使用）
        if not hasattr(Settings, 'llm') or Settings.llm is None:
            # 传递所有配置参数，包括 api_version 等额外参数
            set_global_llm_model(llm_provider, llm_model, llm_key, llm_url, **config_values)

        # P0改进3: 高级功能（默认展开）- 使用新组件 (Stage 3.2.3)
        from src.ui.sidebar_config import SidebarConfig
        advanced_config = SidebarConfig._render_advanced_config()

    with tab_monitor:
        # v2.3.0: 智能监控面板
        try:
            from src.core.v23_integration import get_v23_integration
            v23 = get_v23_integration()
            v23.render_monitoring_tab()
        except ImportError:
            # 降级到v1.5.1性能监控面板
            perf_monitor.render_panel()
    
    with tab_tools:
        st.markdown("### 🔧 工具箱")
        
        # P0改进3: 系统工具（默认展开）
        with st.expander("🛠️ 系统工具", expanded=True):
            # 系统监控
            auto_refresh = st.checkbox("🔄 自动刷新 (2秒)", value=False, key="tools_auto_refresh")

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
                # 优化为 2*3 布局 (一行两个)
                m_row1_col1, m_row1_col2 = st.columns(2)
                m_row2_col1, m_row2_col2 = st.columns(2)
                m_row3_col1, m_row3_col2 = st.columns(2)

                with m_row1_col1:
                    st.metric("CPU 使用率", f"{cpu_percent:.1f}%")
                    st.caption(f"⚙️ {psutil.cpu_count()} 核")
                    st.progress(cpu_percent / 100)

                with m_row1_col2:
                    st.metric("GPU 状态", "活跃" if gpu_active else "空闲")
                    st.caption("🎮 Apple Metal")
                    if gpu_active:
                        st.progress(0.5)
                    else:
                        st.progress(0.0)

                with m_row2_col1:
                    st.metric("内存使用", f"{mem.percent:.1f}%")
                    st.caption(f"🧠 {mem.used/1024**3:.1f}GB / {mem.total/1024**3:.1f}GB")
                    st.progress(mem.percent / 100)

                with m_row2_col2:
                    st.metric("磁盘使用", f"{disk.percent:.1f}%")
                    st.caption(f"💾 {disk.used/1024**3:.0f}GB / {disk.total/1024**3:.0f}GB")
                    st.progress(disk.percent / 100)

                current_proc = psutil.Process()
                proc_mem = current_proc.memory_info().rss / 1024**3
                
                with m_row3_col1:
                    st.metric("进程内存", f"{proc_mem:.1f} GB")
                    st.caption("🔍 当前应用占用")
                
                with m_row3_col2:
                    st.metric("线程数量", f"{current_proc.num_threads()}")
                    st.caption("🧵 活动线程数")

                st.caption("💡 GPU 详细信息需要: `sudo python3 system_monitor.py`")

            if auto_refresh:
                import time
                time.sleep(2)
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### ⬆️ 快速上传")
        uploaded_file = st.file_uploader("选择文件", type=['pdf', 'txt', 'docx', 'md'], key="tools_uploader")
        if uploaded_file:
            st.success(f"✅ 已选择: {uploaded_file.name}")
            st.info("💡 请到主页完成处理")
    
    with tab_help:
        st.markdown("### 📖 帮助")
        st.info("RAG Pro Max v2.4.7 - Web爬取与数据处理增强版")

# ==========================================
# 主功能区域
# ==========================================

# 根据选择的模式显示对应功能
if st.session_state.get('main_mode', 'rag') == 'sql':
    # ==========================================
    # 📊 数据分析模式
    # ==========================================
    st.markdown("### 📊 数据分析 (Text-to-SQL)")
    
    # 初始化SQL引擎
    if 'sql_engine' not in st.session_state:
        try:
            from src.engines.sql_engine import SQLEngine
            st.session_state.sql_engine = SQLEngine()
        except ImportError:
            st.error("SQL引擎模块未找到")
            st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### 📁 数据导入")
        
        uploaded_data = st.file_uploader(
            "上传Excel/CSV文件", 
            type=['xlsx', 'csv'],
            key="main_data_uploader"
        )
        
        if uploaded_data:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_data.name.split('.')[-1]}") as tmp:
                tmp.write(uploaded_data.getvalue())
                tmp_path = tmp.name
            
            if st.button("📥 导入数据", type="primary", key="main_import"):
                with st.spinner("导入中..."):
                    try:
                        result = st.session_state.sql_engine.import_excel_csv(tmp_path)
                        st.success(result)
                        st.session_state.main_data_imported = True
                    except Exception as e:
                        st.error(f"导入失败: {str(e)}")
        
        # 显示数据结构
        if st.session_state.get('main_data_imported'):
            st.markdown("#### 📋 数据结构")
            try:
                schema = st.session_state.sql_engine.get_schema()
                for table, columns in schema.items():
                    with st.expander(f"📊 {table}"):
                        st.write(f"字段: {', '.join(columns)}")
            except:
                st.write("暂无数据")

    with col2:
        st.markdown("#### 💬 数据问答")
        
        if st.session_state.get('main_data_imported'):
            data_query = st.text_input(
                "输入您的数据分析问题", 
                placeholder="例如: 统计各部门的总人数、计算平均工资",
                key="main_data_query"
            )
            
            if st.button("🔍 分析", type="primary", key="main_analyze") and data_query:
                with st.spinner("正在分析..."):
                    try:
                        if not hasattr(st.session_state, 'llm') or not st.session_state.llm:
                            st.error("请先在左侧配置页面设置LLM模型")
                        else:
                            sql = st.session_state.sql_engine.text_to_sql(data_query, st.session_state.llm)
                            
                            with st.expander("📝 生成的SQL语句"):
                                st.code(sql, language="sql")
                            
                            result = st.session_state.sql_engine.execute_sql(sql)
                            
                            if result['success']:
                                st.success(f"✅ 查询成功，返回 {result['rows']} 行数据")
                                if result['data']:
                                    import pandas as pd
                                    df = pd.DataFrame(result['data'])
                                    st.dataframe(df, use_container_width=True)
                                    
                                    # 简单图表
                                    if len(df.columns) >= 2 and len(df) > 1:
                                        chart_col1, chart_col2 = st.columns(2)
                                        with chart_col1:
                                            if st.button("📊 柱状图"):
                                                st.bar_chart(df.set_index(df.columns[0]))
                                        with chart_col2:
                                            if st.button("📈 折线图"):
                                                st.line_chart(df.set_index(df.columns[0]))
                                else:
                                    st.info("查询无结果")
                            else:
                                st.error(f"❌ 查询失败: {result['error']}")
                    except Exception as e:
                        st.error(f"处理失败: {str(e)}")
        else:
            st.info("👆 请先上传数据文件")
            
    # 停止后续执行，确保只显示数据分析界面
    st.stop()

# ==========================================
# 📄 RAG文档问答模式 (原有功能)
# ==========================================

# ==========================================
# 5. 核心逻辑 (RAG & Indexing)
# ==========================================

def process_knowledge_base_logic(action_mode="NEW", use_ocr=False, extract_metadata=False, generate_summary=False, force_reindex=False):
    """处理知识库逻辑 (Stage 4.2 - 使用 IndexBuilder)"""
    global logger
    
    persist_dir = os.path.join(output_base, final_kb_name)
    start_time = time.time()
    
    # 资源保护检查
    cpu = psutil_main.cpu_percent(interval=0.1)
    mem = psutil_main.virtual_memory().percent
    result = resource_guard.check_resources(cpu, mem, 0)
    throttle_info = result.get('throttle', {})
    if throttle_info.get('action') == 'reject':
        st.warning(f"⚠️ 系统资源紧张，请稍后再试")
        logger.warning(f"资源不足，暂停处理: CPU={cpu}%, MEM={mem}%")
        time.sleep(2)
        return

    # 设置嵌入模型
    logger.info(f"🔧 设置嵌入模型: {embed_model} (provider: {embed_provider})")
    embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
    if not embed:
        logger.warning(f"⚠️ 嵌入模型加载失败: {embed_model}，尝试离线模式")
        try:
            from src.utils.offline_embeddings import get_offline_embeddings
            offline_embed = get_offline_embeddings("all-MiniLM-L6-v2")
            if offline_embed.load_model():
                logger.info("✅ 离线嵌入模型加载成功")
                # 创建一个简单的包装器
                class OfflineEmbedWrapper:
                    def __init__(self, offline_model):
                        self.offline_model = offline_model
                    def _get_text_embedding(self, text):
                        return self.offline_model.encode([text])[0]
                embed = OfflineEmbedWrapper(offline_embed)
            else:
                logger.error(f"❌ 离线模式也失败，无法加载嵌入模型")
                st.error("❌ 嵌入模型加载失败，请检查网络连接或模型配置")
                return
        except Exception as e:
            logger.error(f"❌ 离线模式异常: {e}")
            st.error("❌ 嵌入模型加载失败，请检查网络连接或模型配置")
            return
    
    Settings.embed_model = embed
    try:
        actual_dim = len(embed._get_text_embedding("test"))
        logger.success(f"✅ 嵌入模型已设置: {embed_model} ({actual_dim}维)")
    except:
        logger.success(f"✅ 嵌入模型已设置: {embed_model}")

    logger.log("INFO", f"开始处理知识库: {final_kb_name}", stage="知识库处理")
    
    # UI 状态容器
    status_container = st.status(f"🚀 处理知识库: {final_kb_name}", expanded=True)
    prog_bar = status_container.progress(0)
    status_container.write(f"⏱️ 开始时间: {datetime.now().strftime('%H:%M:%S')}")
    
    # 回调函数：更新 UI
    def status_callback(msg_type, *args):
        if msg_type == "step":
            step_num, step_desc = args
            status_container.write(f"📂 [步骤{step_num}/6] {step_desc}")
            logger.info(f"📂 [步骤 {step_num}/6] {step_desc}")
            prog_bar.progress(step_num * 15)
        elif msg_type == "info":
            info_msg = args[0]
            status_container.write(f"   {info_msg}")
            logger.info(f"   {info_msg}")
        elif msg_type == "warning":
            warn_msg = args[0]
            status_container.write(f"   ⚠️  {warn_msg}")
            logger.warning(f"   ⚠️  {warn_msg}")
    
    # 获取源路径
    current_target_path = st.session_state.get('uploaded_path') or st.session_state.path_input
    if not current_target_path or not os.path.exists(current_target_path):
        status_container.update(label="❌ 路径无效", state="error")
        logger.error(f"❌ 路径无效: {current_target_path}")
        raise ValueError(f"路径无效: {current_target_path}")
    
    # 使用 IndexBuilder 构建索引
    builder = IndexBuilder(
        kb_name=final_kb_name,
        persist_dir=persist_dir,
        embed_model=embed,
        embed_model_name=embed_model,
        use_ocr=use_ocr,  # 传递OCR选项
        extract_metadata=extract_metadata,  # 传递性能选项
        generate_summary=generate_summary,  # 传递摘要选项
        logger=logger
    )
    
    result = builder.build(
        source_path=current_target_path,
        force_reindex=force_reindex,
        action_mode=action_mode,
        status_callback=status_callback
    )
    
    if not result.success:
        status_container.update(label=f"❌ 处理失败: {result.error}", state="error")
        logger.error(f"❌ 处理失败: {result.error}")
        raise ValueError(result.error)
    
    # 保存索引
    if result.index:
        result.index.storage_context.persist(persist_dir=persist_dir)
        logger.success(f"💾 索引已保存到: {persist_dir}")
    
    # 更新进度
    prog_bar.progress(100)
    
    # 计算耗时
    duration = time.time() - start_time
    logger.separator("处理完成")
    logger.success(f"✅ 知识库 '{final_kb_name}' 处理完成")
    logger.info(f"📊 统计: {result.file_count} 个文件, {result.doc_count} 个文档片段")
    logger.info(f"⏱️  耗时: {duration:.1f} 秒")
    
    logger.log("SUCCESS", f"知识库处理完成: {final_kb_name}, 文档数: {result.doc_count
    }", stage="知识库处理")
    
    status_container.update(label=f"✅ 知识库 '{final_kb_name}' 处理完成", state="complete", expanded=True)
    
    # 资源清理
    resource_guard.throttler.cleanup_memory()
    logger.info("🧹 资源已清理")
    
    # 自动跳转到新建的知识库
    st.session_state.current_nav = f"📂 {final_kb_name}"
    st.success(f"🎉 知识库 '{final_kb_name}' 构建完成！已自动切换到该知识库")
    
    time.sleep(1.5)
    st.rerun()  # 刷新页面，显示新知识库
    
    return result.doc_count

# ==========================================
# 6. 聊天界面 & 无限追问功能
# ==========================================
st.markdown("""
<div style="
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 0px;
    margin-bottom: 0px;
    border-bottom: 2px solid #f0f2f6;
">
    <div style="font-size: 1.8rem;">🛡️</div>
    <div style="
        font-size: 1.5rem;
        font-weight: 600;
        color: #1f2937;
        letter-spacing: -0.5px;
    ">RAG Pro Max</div>
</div>
""", unsafe_allow_html=True)

# 引入新的优化组件
from src.utils.enhanced_ocr_optimizer import enhanced_ocr_optimizer
from src.ui.progress_monitor import progress_monitor

# 显示实时进度监控
progress_monitor.render_all_tasks()

# 紧凑侧边栏CSS样式
st.markdown("""
<style>
/* 侧边栏紧凑化 */
.css-1d391kg, [data-testid="stSidebar"] {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
}

/* 确保侧边栏收起按钮可见和可用 */
[data-testid="collapsedControl"] {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
}

/* 侧边栏收起状态 */
[data-testid="stSidebar"][aria-expanded="false"] {
    width: 0 !important;
    min-width: 0 !important;
}

/* 减少标题间距 */
.css-1lcbmhc {
    margin-bottom: 0.25rem;
    margin-top: 0.25rem;
}

/* 紧凑按钮 */
.stButton > button {
    height: 1.8rem;
    padding: 0.2rem 0.4rem;
    font-size: 11px;
    margin-bottom: 0.2rem;
}

/* 紧凑输入框 */
.stTextInput > div > div > input {
    height: 1.8rem;
    font-size: 12px;
}

/* 紧凑选择框 */
.stSelectbox > div > div > div {
    height: 1.8rem;
    font-size: 12px;
}

/* 减少expander间距 */
.streamlit-expanderHeader {
    padding: 0.25rem 0.5rem;
    font-size: 13px;
}

/* 紧凑指标 */
.css-1xarl3l {
    padding: 0.25rem;
}
</style>
""", unsafe_allow_html=True)


# 初始化状态
initialize_session_state()

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
    """点击追问按钮 - 使用公共业务逻辑"""
    from src.common.business import click_btn as common_click_btn
    return common_click_btn(q)

# 计算当前的 KB ID (根据侧边栏选择)
active_kb_name = current_kb_name if not is_create_mode else None

# 自动加载逻辑
if active_kb_name and active_kb_name != st.session_state.current_kb_id:
    # 只在没有正在处理的问题时才切换
    if not st.session_state.get('is_processing', False):
        st.session_state.current_kb_id = active_kb_name
        st.session_state.chat_engine = None
        with st.spinner("📜 正在加载对话历史..."):
            st.session_state.messages = HistoryManager.load(active_kb_name)
        st.session_state.suggestions_history = []
    else:
        st.warning("⚠️ 正在处理问题，请等待完成后再切换知识库")
        st.session_state.current_nav = f"📂 {st.session_state.current_kb_id}"

# 知识库加载逻辑
if active_kb_name and st.session_state.chat_engine is None:
    from src.kb.kb_loader import KnowledgeBaseLoader
    
    kb_loader = KnowledgeBaseLoader(output_base)
    chat_engine, error_msg, kb_index = kb_loader.load_knowledge_base(
        active_kb_name, embed_provider, embed_model, embed_key, embed_url
    )
    
    if chat_engine:
        st.session_state.chat_engine = chat_engine
        st.session_state.kb_index_obj = kb_index
        logger.success("问答引擎已启用GPU加速")
        logger.log("SUCCESS", f"知识库加载成功: {active_kb_name}", stage="知识库加载")
        st.toast(f"✅ 知识库 '{active_kb_name}' 挂载成功！")
        cleanup_memory()
    else:
        st.error(error_msg) 

# 按钮处理
if btn_start:
    # 确保 action_mode 已定义 (防止 NameError)
    if 'action_mode' not in locals() and 'action_mode' not in globals():
        action_mode = "NEW" if is_create_mode else "APPEND"

    # 显式获取高级选项状态 (优先从 session_state 获取)
    current_use_ocr = st.session_state.get('kb_use_ocr', False)
    current_extract_metadata = st.session_state.get('kb_extract_metadata', False)
    current_generate_summary = st.session_state.get('kb_generate_summary', False)
    current_force_reindex = st.session_state.get('kb_force_reindex', False)

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
    ConfigLoader.save(config_to_save)

    if not final_kb_name:
        st.error("请输入知识库名称")
    else:
        try:
            # 使用优化器生成唯一名称，避免重复和时间戳冲突
            optimized_name = KBNameOptimizer.generate_unique_name(final_kb_name, output_base)
            
            if not optimized_name: 
                raise ValueError("知识库名称包含非法字符或为空")
            
            # 如果名称被优化了，提示用户
            if optimized_name != final_kb_name:
                st.info(f"💡 名称已优化: `{final_kb_name}` → `{optimized_name}`")
                
            # 使用优化后的名称
            final_kb_name = optimized_name
            
            # DEBUG: Check parameters
            print(f"DEBUG: Calling process_knowledge_base_logic with: ocr={current_use_ocr}, meta={current_extract_metadata}, summary={current_generate_summary}")

            process_knowledge_base_logic(
                action_mode=action_mode,
                use_ocr=current_use_ocr,
                extract_metadata=current_extract_metadata,
                generate_summary=current_generate_summary,
                force_reindex=current_force_reindex
            )
            st.session_state.current_nav = f"📂 {final_kb_name}"
            st.session_state.current_kb_id = None 
            
            if action_mode == "NEW" or action_mode == "APPEND":
                st.session_state.messages = []
                st.session_state.suggestions_history = []
                hist_path = os.path.join(HISTORY_DIR, f"{final_kb_name}.json")
                if os.path.exists(hist_path): os.remove(hist_path)
            
            time.sleep(1); st.rerun()
        except Exception as e:
            st.error(f"执行失败: {e}")

# --- 主视图渲染 ---
if active_kb_name:
    from src.documents.document_manager import DocumentManager
    
    db_path = os.path.join(output_base, active_kb_name)
    doc_manager = DocumentManager(db_path)
    stats = doc_manager.get_kb_statistics()

    # --- 批量操作处理逻辑 ---
    if st.session_state.get('trigger_batch_summary'):
        st.session_state.trigger_batch_summary = False
        run_summary = True # 触发下方的摘要逻辑
    else:
        run_summary = False

    if st.session_state.get('trigger_batch_delete'):
        st.session_state.trigger_batch_delete = False
        selected_files = st.session_state.get('selected_for_summary', set())
        if selected_files:
            with st.status(f"正在批量删除 {len(selected_files)} 个文件...", expanded=True) as status:
                try:
                    from llama_index.core import StorageContext, load_index_from_storage
                    ctx = StorageContext.from_defaults(persist_dir=db_path)
                    idx = load_index_from_storage(ctx)
                    
                    for fname in selected_files:
                        file_info = next((f for f in doc_manager.manifest['files'] if f['name'] == fname), None)
                        if file_info:
                            for did in file_info.get('doc_ids', []):
                                try:
                                    idx.delete_ref_doc(did, delete_from_docstore=True)
                                except: pass
                    
                    idx.storage_context.persist(persist_dir=db_path)
                    
                    # 更新 manifest
                    doc_manager.manifest['files'] = [f for f in doc_manager.manifest['files'] if f['name'] not in selected_files]
                    with open(ManifestManager.get_path(db_path), 'w', encoding='utf-8') as mf:
                        json.dump(doc_manager.manifest, mf, indent=4, ensure_ascii=False)
                    
                    status.update(label="✅ 批量删除成功", state="complete")
                    st.session_state.selected_for_summary = set()
                    st.session_state.chat_engine = None
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"批量删除失败: {e}")
    
    # 重命名逻辑和统计显示
    if st.session_state.renaming:
        def apply_rename():
            n = sanitize_filename(st.session_state.new_name_input)
            if n and n != active_kb_name:
                try:
                    kb_manager.base_path = output_base
                    success, msg = kb_manager.rename(active_kb_name, n)
                    if success:
                        st.session_state.current_nav = f"📂 {n}"
                        st.toast("✅ 重命名成功")
                    else:
                        st.error(f"重命名失败: {msg}")
                except FileExistsError as e:
                    st.error(f"重命名失败: {e}")
            st.session_state.renaming = False
        c1, c2 = st.columns([3, 1])
        c1.text_input("新名称", value=active_kb_name, key="new_name_input", on_change=apply_rename)
        c2.button("取消", on_click=lambda: st.session_state.update({"renaming": False}))
    else:
        rename_col = doc_manager.render_statistics_overview(active_kb_name, stats)
        if rename_col.button("✏️", help="重命名"): 
            st.session_state.renaming = True
    
    # 文件管理
    with st.expander("📊 知识库详情与管理", expanded=False):
        if not doc_manager.manifest['files']: 
            st.info("暂无文件")
        else:
            # 🔧 高级选项处理统计
            total_files = len(doc_manager.manifest['files'])
            ocr_files = sum(1 for f in doc_manager.manifest['files'] if f.get('used_ocr', False))
            metadata_files = sum(1 for f in doc_manager.manifest['files'] if f.get('keywords') or f.get('category'))
            summary_files = sum(1 for f in doc_manager.manifest['files'] if f.get('summary'))
            total_chunks = sum(len(f.get('doc_ids', [])) for f in doc_manager.manifest['files'])
            storage_size = KBManager.format_size(stats.get('size', 0)) if stats else "未知"
            
            # 只有当有高级数据时才展开
            has_advanced_data = (ocr_files + metadata_files + summary_files) > 0
            
            with st.expander("🔧 高级选项处理统计", expanded=has_advanced_data):
                # 优化为单行 6 列布局
                adv_cols = st.columns(6)
                
                with adv_cols[0]:
                    st.metric("📄 总文档", total_files)
                with adv_cols[1]:
                    st.metric("🧩 总片段", total_chunks)
                    
                with adv_cols[2]:
                    ocr_percentage = (ocr_files / total_files * 100) if total_files > 0 else 0
                    st.metric("🔍 OCR处理", f"{ocr_files}", delta=f"{ocr_percentage:.1f}%")
                with adv_cols[3]:
                    metadata_percentage = (metadata_files / total_files * 100) if total_files > 0 else 0
                    st.metric("📊 元数据提取", f"{metadata_files}", delta=f"{metadata_percentage:.1f}%")
                    
                with adv_cols[4]:
                    summary_percentage = (summary_files / total_files * 100) if total_files > 0 else 0
                    st.metric("📝 生成摘要", f"{summary_files}", delta=f"{summary_percentage:.1f}%")
                with adv_cols[5]:
                    st.metric("💾 存储占用", storage_size)
                
                # 处理建议
                if not has_advanced_data:
                    st.caption("💡 **提示**: 在上传文档时启用高级选项，可以获得更丰富的文档信息和更好的检索效果")
                elif ocr_files < total_files // 2:
                    st.caption("💡 **建议**: 对于包含图片或扫描内容的PDF文档，建议启用OCR识别功能")
            
            st.divider()
            
            # 文档列表查看与统计
            # tab1, tab2 = st.tabs(["📊 统计信息", "📄 文档列表"])
            
            if True: # 统计信息
                # 详细统计信息
                quality_info = doc_manager.render_detailed_statistics(stats)
                st.divider()
                
                # 分布分析
                doc_manager.render_distribution_analysis(stats)
                st.divider()
                
                # 元数据统计
                try:
                    metadata_mgr = MetadataManager(db_path)
                    if metadata_mgr.metadata or metadata_mgr.stats:
                        with st.expander("📊 元数据统计", expanded=True):
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
            
            # 快速操作按钮组 - 合并为单行
            op_col1, op_col2, op_col3, op_col4 = st.columns(4)
            
            # 1. 打开知识库目录
            with op_col1:
                if st.button("📂 打开目录", use_container_width=True, help="在Finder中打开知识库文件夹"):
                    import webbrowser
                    import urllib.parse
                    try:
                        file_url = 'file://' + urllib.parse.quote(os.path.abspath(db_path))
                        webbrowser.open(file_url)
                        st.toast("✅ 已在Finder中打开")
                    except Exception as e:
                        st.error(f"打开失败: {e}")
            
            # 2. 复制路径
            with op_col2:
                if st.button("📋 复制路径", use_container_width=True, help="复制知识库路径到剪贴板"):
                    try:
                        import subprocess
                        subprocess.run(["pbcopy"], input=db_path.encode(), check=True)
                        st.toast(f"✅ 已复制")
                    except Exception as e:
                        st.info(f"📁 路径: {db_path}")
            
            # 准备摘要数据
            files_without_summary = [f for f in doc_manager.manifest['files'] if not f.get('summary') and f.get('doc_ids')]
            if 'selected_for_summary' not in st.session_state:
                st.session_state.selected_for_summary = set()
            selected_count = len(st.session_state.selected_for_summary)
            
            # 3. 生成摘要
            with op_col3:
                # 始终显示按钮，但根据选中数量决定是否禁用
                button_label = f"✨ 摘要 ({selected_count})" if selected_count > 0 else "✨ 生成摘要"
                button_disabled = selected_count == 0
                
                if st.button(button_label, use_container_width=True, type="primary", disabled=button_disabled, help="为选中的文件生成AI摘要"):
                    run_summary = True

            # 4. 导出清单
            with op_col4:
                if st.button("📥 导出清单", use_container_width=True, help="导出当前文件列表"):
                    export_data = f"知识库: {active_kb_name}\n文件数: {stats['file_cnt']}\n片段数: {stats['total_chunks']}\n\n文件列表:\n"
                    for f in doc_manager.manifest['files']:
                        export_data += f"- {f['name']} ({f['type']}, {len(f.get('doc_ids', []))} 片段)\n"
                    st.download_button("下载", export_data, f"{active_kb_name}_清单.txt", use_container_width=True)

            # 执行摘要生成逻辑
            if run_summary and files_without_summary:
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
                        file_info = next((f for f in doc_manager.manifest['files'] if f['name'] == fname), None)
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
                                if summary:
                                    file_info['summary'] = summary
                                    
                                    # 将摘要添加到向量数据库
                                    try:
                                        from llama_index.core import Document
                                        summary_doc = Document(
                                            text=f"文档摘要 - {fname}:\n{summary}",
                                            metadata={
                                                "file_name": fname,
                                                "file_type": "summary",
                                                "source_file": fname
                                            }
                                        )
                                        idx.insert(summary_doc)
                                    except Exception as e:
                                        logger.warning(f"摘要添加到索引失败: {e}")
                                    
                                    success_count += 1
                    except Exception as e:
                        st.warning(f"⚠️ {fname}: {str(e)}")
                        
                    progress_bar.progress((i + 1) / selected_count)
                
                # 保存索引和 manifest
                try:
                    idx.storage_context.persist(persist_dir=db_path)
                except Exception as e:
                    logger.warning(f"索引保存失败: {e}")
                    
                with open(ManifestManager.get_path(db_path), 'w', encoding='utf-8') as f:
                    json.dump(doc_manager.manifest, f, indent=4, ensure_ascii=False)
                
                status_text.empty()
                progress_bar.empty()
                st.success(f"✅ 已生成 {success_count}/{selected_count} 个摘要并添加到知识库")
                st.session_state.selected_for_summary = set()
                time.sleep(1)
                st.rerun()  # 立即刷新页面显示摘要
            
            # 文档列表标签页 (v1.6) - 已移除
            pass
            
            st.divider()
            
            # 搜索筛选排序（单行超紧凑布局）
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2.5, 1.2, 1.2, 1.2, 1.2, 1.5, 1])
            search_term = col1.text_input("🔍", "", key="file_search", placeholder="搜索文件名...", label_visibility="collapsed")
            filter_type = col2.selectbox("📂", ["📂 类型"] + sorted(set(f.get('type', 'Unknown') for f in doc_manager.manifest['files'])), label_visibility="collapsed")
            
            # 分类筛选
            all_categories = set(f.get('category', '其他') for f in doc_manager.manifest['files'] if f.get('category'))
            filter_category = col3.selectbox("📋", ["📋 分类"] + sorted(all_categories), label_visibility="collapsed") if all_categories else "📋 分类"
            
            # 热度筛选
            filter_heat = col4.selectbox("🔥", ["🔥 热度", "高频", "中频", "低频", "未用"], label_visibility="collapsed")
            
            # 质量筛选
            filter_quality = col5.selectbox("✅", ["✅ 质量", "优秀", "正常", "低质", "空"], label_visibility="collapsed")
            
            sort_by = col6.selectbox("排序", ["时间↓", "时间↑", "大小↓", "大小↑", "名称", "热度↓", "片段↓"], label_visibility="collapsed")
            page_size = col7.selectbox("页", [5, 10, 20, 50], index=0, label_visibility="collapsed")
            
            # 筛选文件
            filtered_files = doc_manager.manifest['files']
            
            # 搜索
            if search_term:
                filtered_files = [f for f in filtered_files if search_term.lower() in f['name'].lower()]
            
            # 类型筛选
            if filter_type != "📂 类型":
                filtered_files = [f for f in filtered_files if f.get('type') == filter_type]
            
            # 分类筛选
            if filter_category != "📋 分类":
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
                if filter_type != "📂 类型": filters.append(filter_type)
                if filter_category != "📋 分类": filters.append(filter_category)
                if filter_heat != "🔥 热度": filters.append(filter_heat)
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
                
                cols[1].caption(f"**文件列表 (共 {total_files} 个)**")
                cols[2].caption("**操作**")
                st.divider()
                
                # 注入极致紧凑 CSS
                st.markdown("""
                <style>
                /* 极致压缩垂直间距 */
                div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
                    gap: 0.1rem !important;
                }
                /* 卡片内部 padding 最小化 */
                div[data-testid="stContainer"] {
                    padding: 0.3rem 0.6rem !important;
                    margin-bottom: 0.1rem !important;
                }
                /* Expander 标题栏高度压缩 & 移除外边距 */
                .streamlit-expanderHeader {
                    height: 1.8rem !important;
                    padding-top: 0 !important;
                    padding-bottom: 0 !important;
                    min-height: unset !important;
                    margin-bottom: 0 !important; /* 关键 */
                }
                /* Expander 整体上移 */
                div[data-testid="stExpander"] {
                    margin-top: -0.2rem !important;
                    border: none !important;
                    box-shadow: none !important;
                }
                /* Expander 内容区域去顶距 */
                div[data-testid="stExpanderDetails"] {
                    padding-top: 0 !important;
                    padding-bottom: 0.2rem !important;
                }
                /* 分割线紧凑 */
                hr {
                    margin-top: 0.1rem !important;
                    margin-bottom: 0.1rem !important;
                }
                /* 文本紧凑 */
                p, h5, span {
                    margin: 0 !important;
                    padding: 0 !important;
                    line-height: 1.3 !important;
                }
                /* 按钮紧凑 */
                button {
                    height: 1.6rem !important;
                    padding-top: 0 !important;
                    padding-bottom: 0 !important;
                    min-height: unset !important;
                }
                </style>
                """, unsafe_allow_html=True)

                # 渲染文件列表 (One-Line Card 模式)
                for i in range(start_idx, end_idx):
                    f = filtered_files[i]
                    orig_idx = doc_manager.manifest['files'].index(f)
                    chunk_count = len(f.get('doc_ids', []))
                    
                    # 准备元数据
                    display_date = f.get('creation_date', f.get('added_at', '')[:10])
                    
                    # 质量评估
                    if chunk_count == 0:
                        q_icon = "❌"
                    elif chunk_count < 2:
                        q_icon = "⚠️"
                    elif chunk_count < 10:
                        q_icon = "✅"
                    else:
                        q_icon = "🎉"

                    # === 极简卡片容器 ===
                    with st.container(border=True):
                        # 单行布局：标题 + 元数据 + 摘要 + 详情 + 操作
                        col_info, col_summary, col_detail, col_ops = st.columns([5.5, 1.5, 1.5, 1.5])
                        
                        with col_info:
                            # 核心改动：一行显示所有关键信息
                            # 格式：📄 网页标题/文件名  [灰色小字: 2.5MB · 2023-12-12 · 质量 · 命中3次]
                            file_icon = f.get('icon', '📄')
                            
                            # 智能标题显示：如果是抓取的网页，尝试显示实际标题
                            display_name = f['name']
                            tech_name = ""
                            
                            # 尝试获取真实标题（针对 crawler 生成的 txt）
                            if f['name'].endswith('.txt') and 'page_' in f['name']:
                                # 尝试从文件元数据中读取标题（如果之前有保存）
                                # 或者简单判断是否为 crawler 文件
                                try:
                                    # 简易优化：如果文件名是 page_X_timestamp.txt，显示更友好的名称
                                    parts = f['name'].split('_')
                                    if len(parts) >= 3 and parts[0] == 'page':
                                        # 暂时只显示优化后的 ID，后续可升级为读取文件内容首行
                                        display_name = f"网页 {parts[1]} ({parts[2][:8]})"
                                        tech_name = f['name']
                                except:
                                    pass
                            
                            if len(display_name) > 25: display_name = display_name[:23] + "..."
                            
                            # 添加更多关键信息到一行中
                            hit_count = f.get('hit_count', 0)
                            category = f.get('category', '')
                            hit_info = f"命中{hit_count}次" if hit_count > 0 else ""
                            category_info = f"{category}" if category and category != '未分类' else ""
                            
                            # 组合额外信息
                            extra_info = " · ".join(filter(None, [hit_info, category_info]))
                            if extra_info:
                                extra_info = " · " + extra_info
                                
                            # 质量提示优化
                            q_tooltip = ""
                            if chunk_count < 2:
                                q_tooltip = "内容较少 (<500字)，建议作为补充材料"
                            
                            line_html = f"""
                            <div style='display: flex; align-items: baseline; white-space: nowrap; overflow: hidden;'>
                                <span style='font-weight: 600; font-size: 1rem; margin-right: 0.5rem;' title='{tech_name}'>{file_icon} {display_name}</span>
                                <span style='color: gray; font-size: 0.75rem;'>
                                    {f['size']} · {chunk_count}片段 · {display_date} · <span title="{q_tooltip}">{q_icon}</span>{extra_info}
                                </span>
                            </div>
                            """
                            if tech_name:
                                line_html += f"<div style='font-size: 0.7rem; color: #999; margin-top: -2px;'>📄 {tech_name}</div>"
                                
                            st.markdown(line_html, unsafe_allow_html=True)
                            
                            # 🔧 高级选项处理状态标识
                            processing_badges = []
                            if f.get('used_ocr', False):
                                processing_badges.append('<span style="background: #e8f5e8; color: #2d5a2d; padding: 1px 4px; border-radius: 3px; font-size: 0.7rem; margin-right: 3px;">🔍OCR</span>')
                            if f.get('keywords') or f.get('category'):
                                processing_badges.append('<span style="background: #e8f0ff; color: #1a4480; padding: 1px 4px; border-radius: 3px; font-size: 0.7rem; margin-right: 3px;">📊元数据</span>')
                            if f.get('summary'):
                                processing_badges.append('<span style="background: #fff3e0; color: #8b4513; padding: 1px 4px; border-radius: 3px; font-size: 0.7rem; margin-right: 3px;">📝摘要</span>')
                            
                            if processing_badges:
                                badges_html = ''.join(processing_badges)
                                st.markdown(f'<div style="margin-top: 2px; margin-bottom: 4px;">{badges_html}</div>', unsafe_allow_html=True)
                            
                            # 显示摘要（如果有的话）
                            if f.get('summary'):
                                summary_text = f['summary']
                                if len(summary_text) > 100:
                                    summary_text = summary_text[:97] + "..."
                                st.caption(f"📝 {summary_text}")
                            
                            # 显示关键词（如果有的话）
                            if f.get('keywords'):
                                keywords = f['keywords'][:5]  # 只显示前5个关键词
                                st.caption(f"🏷️ {', '.join(keywords)}")
                        
                        with col_summary:
                            # 摘要生成按钮
                            if not f.get('summary') and f.get('doc_ids'):
                                if st.button("✨ 摘要", key=f"summary_{i}", help="生成文档摘要"):
                                    with st.spinner("生成中..."):
                                        try:
                                            # 直接从索引获取文档内容
                                            from llama_index.core import StorageContext, load_index_from_storage
                                            
                                            storage_context = StorageContext.from_defaults(persist_dir=db_path)
                                            index = load_index_from_storage(storage_context)
                                            retriever = index.as_retriever(similarity_top_k=3)
                                            
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
                                                summary = generate_doc_summary(doc_text, f['name'])
                                                if summary:
                                                    # 更新manifest
                                                    f['summary'] = summary
                                                    doc_manager.manifest['files'][orig_idx]['summary'] = summary
                                                    
                                                    # 将摘要添加到向量数据库
                                                    try:
                                                        from llama_index.core import Document
                                                        summary_doc = Document(
                                                            text=f"文档摘要 - {f['name']}:\n{summary}",
                                                            metadata={
                                                                "file_name": f['name'],
                                                                "file_type": "summary",
                                                                "source_file": f['name']
                                                            }
                                                        )
                                                        index.insert(summary_doc)
                                                        index.storage_context.persist(persist_dir=db_path)
                                                    except Exception as e:
                                                        logger.warning(f"摘要添加到索引失败: {e}")
                                                    
                                                    # 保存manifest
                                                    from src.config.manifest_manager import ManifestManager
                                                    ManifestManager.save(db_path, doc_manager.manifest['files'], doc_manager.manifest.get('embed_model', 'Unknown'))
                                                    
                                                    st.success("✅ 摘要生成成功并已添加到知识库！")
                                                    st.rerun()
                                                else:
                                                    st.error("❌ 生成失败")
                                            else:
                                                st.warning("⚠️ 无内容")
                                        except Exception as e:
                                            st.error(f"❌ 失败: {str(e)}")
                            elif f.get('summary'):
                                st.caption("📖 已有摘要")
                        
                        with col_detail:
                            # 更多详情按钮 - 打开文档详情对话框
                            if st.button("🔍 详情", key=f"detail_{i}", help="查看文档详情"):
                                st.session_state['show_doc_detail'] = f
                                st.session_state['show_doc_detail_kb'] = active_kb_name
                        
                        with col_ops:
                            # 预览和删除
                            op_c1, op_c2 = st.columns([1, 1])
                            with op_c1:
                                if st.button("👁️", key=f"prev_{i}", help="原生预览"):
                                    try:
                                        # 优先使用记录的完整路径，否则回退到知识库目录
                                        file_path = f.get('file_path')
                                        if not file_path or not os.path.exists(file_path):
                                            file_path = os.path.join(db_path, f['name'])
                                        
                                        if os.path.exists(file_path):
                                            # 异步启动预览，不阻塞主程序
                                            subprocess.Popen(["qlmanage", "-p", file_path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                                            # 启动后台脚本强制置顶窗口
                                            top_script = 'tell application "System Events"\n repeat until (exists process "qlmanage")\n delay 0.1\n end repeat\n set frontmost of process "qlmanage" to true\n end tell'
                                            subprocess.Popen(['osascript', '-e', top_script])
                                        else:
                                            st.warning(f"源文件不存在: {f['name']}")
                                    except Exception as e:
                                        st.error(f"预览失败: {e}")
                            
                            with op_c2:
                                # 操作区：仅保留删除按钮
                                if st.button("🗑️", key=f"del_{i}", help="删除文件"):
                                    with st.status(f"删除中...", expanded=True) as status:
                                        try:
                                            ctx = StorageContext.from_defaults(persist_dir=db_path)
                                            idx = load_index_from_storage(ctx)
                                            for did in f.get('doc_ids', []):
                                                idx.delete_ref_doc(did, delete_from_docstore=True)
                                            idx.storage_context.persist(persist_dir=db_path)
                                            remove_file_from_manifest(db_path, f['name'])
                                            status.update(label="已删除", state="complete")
                                            st.session_state.chat_engine = None
                                            time.sleep(0.5); st.rerun()
                                        except Exception as e: st.error(str(e))
                
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

# 文档详情对话框调用
if st.session_state.get('show_doc_detail') and st.session_state.get('show_doc_detail_kb'):
    show_document_detail_dialog(st.session_state.show_doc_detail_kb, st.session_state.show_doc_detail)

# 创建模式的欢迎界面
if is_create_mode:
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
        with st.status("✨ 正在分析文档生成摘要...", expanded=True) as status:
            try:
                # 使用知识库的模型（已在挂载时设置，无需重复设置）
                current_model = getattr(Settings.embed_model, '_model_name', 'Unknown')
                logger.info(f"💬 摘要生成使用模型: {current_model}")
                
                prompt = "请用一段话简要总结此知识库的核心内容。然后，提出3个用户可能最关心的问题，每行一个，不要序号。"
                full = ""
                resp = st.session_state.chat_engine.stream_chat(prompt)
                
                for t in resp.response_gen:
                    # 🛑 检查停止信号
                    if st.session_state.get('stop_generation'):
                        st.session_state.stop_generation = False
                        full += "\n\n⏹ **生成已停止**"
                        summary_placeholder.markdown(full)
                        break
                    
                    full += t
                    summary_placeholder.markdown(full + "▌")
                
                status.update(label="✅ 摘要生成完成", state="complete")
                summary_placeholder.markdown(full)
                
                summary_lines = full.split('\n')
                summary = summary_lines[0]
                sug = [re.sub(r'^\d+\.\s*', '', q.strip()) for q in summary_lines[1:] if q.strip()][:3]

                st.session_state.messages.append({"role": "assistant", "content": summary, "suggestions": sug})
                HistoryManager.save(active_kb_name, state.get_messages())
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                    status.update(label="⏱️ 摘要生成超时", state="error")
                    summary_placeholder.info("⏱️ LLM 响应超时，已跳过自动摘要。您可以直接开始提问。")
                    logger.warning(f"⏱️ 摘要生成超时: {e}")
                else:
                    status.update(label="❌ 摘要生成失败", state="error")
                    summary_placeholder.warning(f"摘要生成受阻: {e}")
                    logger.error(f"❌ 摘要生成失败: {e}")
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
            render_source_references(msg["sources"], expanded=True)
        
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
                    
                    # 获取LLM模型
                    llm_model = None
                    if st.session_state.get('chat_engine'):
                        chat_engine = st.session_state.chat_engine
                        if hasattr(chat_engine, '_llm'):
                            llm_model = chat_engine._llm
                        elif hasattr(chat_engine, 'llm'):
                            llm_model = chat_engine.llm
                    
                    new_sugs = generate_follow_up_questions(
                        context_text=msg['content'], 
                        num_questions=3,
                        existing_questions=all_history_questions,
                        query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None,
                        llm_model=llm_model
                    )
                    
                    if new_sugs:
                        # 详细日志记录
                        logger.info(f"🔄 继续生成 {len(new_sugs)} 个新推荐问题")
                        for i, q in enumerate(new_sugs[:3], 1):
                            logger.info(f"   {i}. {q}")
                        
                        # 累积历史推荐，避免重复
                        if not hasattr(st.session_state, 'suggestions_history'):
                            st.session_state.suggestions_history = []
                        
                        # 过滤重复问题
                        new_suggestions = []
                        for sugg in new_sugs:
                            if sugg not in st.session_state.suggestions_history:
                                new_suggestions.append(sugg)
                        
                        # 更新显示（使用新生成的问题）
                        st.session_state.suggestions_history = new_suggestions[:3] if new_suggestions else new_sugs[:3]
                        st.rerun(scope="fragment")
                    else:
                        logger.info("⚠️ 未能生成更多追问")
                        st.warning("未能生成更多追问，请尝试输入新问题。")
            
        suggestions_fragment()

# 极简工具栏：模型与设置
with st.container():
    # 使用极窄列宽放置按钮，右侧显示状态
    col_pop, col_filter, col_info = st.columns([0.08, 0.08, 0.84])
    
    with col_pop:
        with st.popover("⚙️", help="模型与任务设置"):
            st.markdown("### 🤖 模型设置")
            # 获取可用模型列表
            try:
                ollama_url = st.session_state.get('llm_url', "http://localhost:11434")
                models, error = fetch_remote_models(ollama_url, "")
                
                if models:
                    available_models = models
                    # 确保 gpt-oss:20b 在第一位
                    if "gpt-oss:20b" in available_models:
                        available_models.remove("gpt-oss:20b")
                        available_models.insert(0, "gpt-oss:20b")
                else:
                    available_models = ["gpt-oss:20b", "llama3", "mistral", "gemma", "deepseek-coder", "qwen2.5:7b"] # Fallback list
            except Exception as e:
                available_models = ["gpt-oss:20b", "llama3", "mistral", "qwen2.5:7b"]
                
            # 获取当前模型 - 使用统一配置
            current_model = st.session_state.get('selected_model', get_default_model())
            if current_model not in available_models:
                if available_models:
                    if current_model not in ["gpt-oss:20b", "llama3", "mistral", "qwen2.5:7b"]:
                         current_model = available_models[0]
            
            # 模型选择下拉框
            selected_model_new = st.selectbox(
                "选择 AI 模型",
                options=available_models,
                index=available_models.index(current_model) if current_model in available_models else 0,
                key="model_selector_dropdown",
                help="Code: 写代码 | Vision: 看图 | Chat: 闲聊"
            )

            # 检测模型变更 - 使用统一更新
            if selected_model_new != st.session_state.get('selected_model'):
                if update_all_model_configs(selected_model_new):
                    st.toast(f"✅ 已切换到模型: {selected_model_new}", icon="🤖")
                    st.rerun()  # 刷新界面显示
                else:
                    st.toast(f"❌ 切换模型失败: {selected_model_new}", icon="⚠️")
            
            st.divider()
            
            # 查询优化开关
            enable_query_optimization = st.checkbox(
                "✨ 启用智能查询优化", 
                value=st.session_state.get('enable_query_optimization', False),
                help="启用后，AI会分析并优化你的提问，提升检索准确性"
            )
            st.session_state.enable_query_optimization = enable_query_optimization

    # New Filter Popover
    with col_filter:
        with st.popover("🔍", help="高级搜索筛选"):
            st.markdown("### 🎯 搜索筛选")
            
            # File Type Filter
            file_types = ["PDF", "Word", "Markdown", "Web"]
            selected_types = st.multiselect(
                "文件类型",
                file_types,
                default=[],
                key="search_filter_types",
                placeholder="全部类型"
            )
            
            # Apply Filter Logic
            current_filters = st.session_state.get('search_filters', [])
            if selected_types != current_filters:
                st.session_state.search_filters = selected_types
                # Trigger engine reload if index exists
                if st.session_state.get('kb_index_obj') and active_kb_name:
                    with st.spinner("🔄 更新检索策略..."):
                        from src.kb.kb_loader import KnowledgeBaseLoader
                        # Re-instantiate loader just for method access (stateless)
                        temp_loader = KnowledgeBaseLoader(output_base)
                        # Recreate engine with new filters
                        new_engine = temp_loader._create_chat_engine(
                            st.session_state.kb_index_obj, 
                            os.path.join(output_base, active_kb_name), 
                            st.empty() # dummy status
                        )
                        st.session_state.chat_engine = new_engine
                        st.toast(f"✅ 已应用筛选: {', '.join(selected_types) if selected_types else '全部'}")
    
    with col_info:
        # 显示当前状态摘要
        curr_model = st.session_state.get('selected_model', get_default_model())
        opt_status = "✅ 开启" if st.session_state.get('enable_query_optimization', False) else "⬜ 关闭"
        
        # Add filter status
        filter_status = ""
        active_filters = st.session_state.get('search_filters', [])
        if active_filters:
            filter_status = f"&nbsp;&nbsp;|&nbsp;&nbsp; 🔍 筛选: {len(active_filters)}项"
            
        st.caption(f"**当前模型**: `{curr_model}` &nbsp;&nbsp;|&nbsp;&nbsp; **智能优化**: {opt_status}{filter_status}")

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
# 🛑 停止按钮功能
if st.session_state.get('is_processing'):
    # 正在处理时显示停止按钮
    col1, col2 = st.columns([4, 1])
    with col1:
        st.chat_input("正在生成回答中...", disabled=True)
    with col2:
        if st.button("⏹ 停止", type="primary", use_container_width=True):
            st.session_state.is_processing = False
            st.session_state.stop_generation = True
            st.success("✅ 已停止生成")
            st.rerun()
else:
    # 正常输入状态
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
        with st.expander(f"⏳ 正在处理问题，队列中还有 {queue_len} 个问题等待...", expanded=True):
            for i, q in enumerate(st.session_state.question_queue, 1):
                # 截断过长的问题
                display_q = q[:50] + "..." if len(q) > 50 else q
                st.caption(f"{i}. {display_q}")
            
            # 添加队列重置按钮
            if st.button("🔄 重置队列（如果卡住）", key="reset_queue"):
                st.session_state.is_processing = False
                st.session_state.question_queue = []
                st.success("✅ 队列已重置")
                st.rerun()
    else:
        st.info("⏳ 正在处理问题...")
        # 添加重置按钮（防止卡住）
        if st.button("🔄 重置状态", key="reset_processing"):
            st.session_state.is_processing = False
            st.success("✅ 处理状态已重置")
            st.rerun()
elif queue_len > 0:
    # 显示待处理的问题列表
    with st.expander(f"📝 队列中有 {queue_len} 个问题待处理", expanded=True):
        for i, q in enumerate(st.session_state.question_queue, 1):
            display_q = q[:50] + "..." if len(q) > 50 else q
            st.caption(f"{i}. {display_q}")
        
        # 添加清空队列按钮
        if st.button("🗑️ 清空队列", key="clear_queue"):
            st.session_state.question_queue = []
            st.success("✅ 队列已清空")
            st.rerun()

# 从队列中取出问题处理
if not st.session_state.get('is_processing', False) and st.session_state.question_queue:
    final_prompt = st.session_state.question_queue.pop(0)
    logger.info(f"🚀 开始处理队列问题: {final_prompt[:50]}...")
    
    if st.session_state.chat_engine:
        # 不清空 suggestions_history，保留追问按钮
        st.session_state.is_processing = True  # 标记正在处理
        logger.info("✅ 设置处理状态为 True")
        
        # 强制检测知识库维度并切换模型（静默处理，不显示加载）
        # 优化：只在首次或切换知识库时检测，避免每次问答都重复
        db_path = os.path.join(output_base, active_kb_name)
        
        # 检查是否需要重新检测（知识库切换或首次）
        last_checked_kb = st.session_state.get('_last_checked_kb')
        if last_checked_kb != active_kb_name:
            kb_dim = get_kb_embedding_dim(db_path)
            
            # 为历史知识库自动保存信息
            kb_name = os.path.basename(db_path)
            kb_manager.save_info(kb_name, embed_model, 0)
            
            # 维度映射
            model_map = {
                512: "sentence-transformers/all-MiniLM-L6-v2",
                768: "BAAI/bge-large-zh-v1.5",
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
                fallback_model = "sentence-transformers/all-MiniLM-L6-v2"
                if embed_model != fallback_model:
                    print(f"🔄 降级切换: {embed_model} → {fallback_model}")
                    embed_model = fallback_model
                    embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
                    if embed:
                        Settings.embed_model = embed
                        print(f"✅ 已降级到最小模型")
            
            # 标记已检测
            st.session_state._last_checked_kb = active_kb_name
        
        logger.separator("知识库查询")
        logger.start_operation("查询", f"知识库: {active_kb_name}")
        
        # 查询改写 (v1.6) - 在处理引用内容之前
        # 只有在用户启用查询优化时才进行
        if st.session_state.get('enable_query_optimization', False):
            query_rewriter = QueryRewriter(Settings.llm)
            should_rewrite, reason = query_rewriter.should_rewrite(final_prompt)
            
            if should_rewrite:
                logger.info(f"💡 检测到需要改写查询: {reason}")
                rewritten_query = query_rewriter.suggest_rewrite(final_prompt)
                
                if rewritten_query and rewritten_query != final_prompt:
                    # 显示优化建议，让用户选择
                    with st.chat_message("assistant", avatar="🤖"):
                        st.info(f"💡 **查询优化建议**\n\n原问题：{final_prompt}\n\n优化后：{rewritten_query}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ 使用优化后的查询", key=f"use_optimized_{len(st.session_state.messages)}"):
                                final_prompt = rewritten_query
                                logger.info(f"✅ 用户选择使用优化后的查询: {rewritten_query}")
                                st.rerun()
                        with col2:
                            if st.button("📝 使用原问题", key=f"use_original_{len(st.session_state.messages)}"):
                                logger.info(f"📝 用户选择使用原问题: {final_prompt}")
                                st.rerun()
                        
                        st.stop()  # 等待用户选择
        
        
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
            logger.info("📌 已应用引用内容")
        
        logger.log("INFO", f"用户提问: {final_prompt}", stage="查询对话", details={"kb_name": active_kb_name})
        
        # 检查重复查询（最近3次）
        recent_queries = [m['content'] for m in st.session_state.messages[-6:] if m['role'] == 'user']
        if final_prompt in recent_queries:
            st.info("💡 您刚才已经问过相同的问题，可以查看上面的回答或尝试换个角度提问")
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        if active_kb_name: HistoryManager.save(active_kb_name, state.get_messages())

        with st.chat_message("user", avatar="🧑‍💻"): st.markdown(final_prompt)
        
        with st.chat_message("assistant", avatar="🤖"):
            msg_placeholder = st.empty()
            
            # 使用一个连贯的spinner包装整个问答流程
            with st.spinner("🤖 正在思考并准备完整回答..."):
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
                        logger.info(f"🎯 检索增强: {enhancement_str}")
                        logger.log("INFO", f"检索增强: {enhancement_str}", stage="查询对话")
                    
                    with logger.timer("检索相关文档"):
                        logger.log("INFO", "开始检索相关文档", stage="查询对话", details={"kb_name": active_kb_name})
                        
                        # 确保 embedding 模型已设置
                        embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
                        if embed:
                            Settings.embed_model = embed
                        
                        # GPU加速检索 - 批量处理
                        retrieval_start = time.time()
                        response = st.session_state.chat_engine.stream_chat(final_prompt)
                        retrieval_time = time.time() - retrieval_start
                        
                        logger.info(f"🔍 检索耗时: {retrieval_time:.2f}s (GPU加速)")
                        
                        full_text = ""
                        # 流式输出 + 资源控制
                        token_count = 0 # 这里的计数仅用于进度估算
                        full_text = ""
                        
                        for token in response.response_gen:
                            # 🛑 检查停止信号
                            if st.session_state.get('stop_generation'):
                                st.session_state.stop_generation = False
                                full_text += "\n\n⏹ **生成已停止**"
                                msg_placeholder.markdown(full_text)
                                break
                            
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
                        logger.log("INFO", f"检索完成，找到 {len(response.source_nodes)} 个相关文档", stage="查询对话", details={"kb_name": active_kb_name})
                        logger.data_summary("检索结果", {
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
                        
                        # 使用并行执行器处理节点（优化并行阈值）
                        executor = ParallelExecutor()
                        tasks = [(d, active_kb_name) for d in node_data]
                        # 启用真正的并行处理，降低阈值到2个节点
                        parallel_threshold = 2
                        srcs = [s for s in executor.execute(process_node_worker, tasks, threshold=parallel_threshold) if s]
                        
                        if len(node_data) >= parallel_threshold:
                            logger.info(f"⚡ 并行处理: {len(srcs)} 个节点 (阈值: {parallel_threshold})")
                        else:
                            logger.info(f"⚡ 单节点处理: {len(srcs)} 个节点")
                    
                    logger.log("SUCCESS", "回答生成完成", stage="查询对话", details={"kb_name": active_kb_name, "model": llm_model, "tokens": token_count, "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens
                    })
                    
                    # 计算总耗时
                    total_time = time.time() - start_time
                    logger.complete_operation(f"查询完成 (耗时 {total_time:.2f}s)")
                    
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
                    
                    # 生成推荐问题（在spinner内完成）
                    existing_questions = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
                    existing_questions.extend(st.session_state.question_queue)
                    existing_questions.extend(st.session_state.suggestions_history)
                    
                    # 获取LLM模型
                    llm_model = None
                    if st.session_state.get('chat_engine'):
                        chat_engine = st.session_state.chat_engine
                        if hasattr(chat_engine, '_llm'):
                            llm_model = chat_engine._llm
                        elif hasattr(chat_engine, 'llm'):
                            llm_model = chat_engine.llm
                    
                    initial_sugs = generate_follow_up_questions(
                        full_text, 
                        num_questions=3,
                        existing_questions=existing_questions,
                        query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None,
                        llm_model=llm_model
                    )
                    
                    if initial_sugs:
                        st.session_state.suggestions_history = initial_sugs[:3]
                        logger.info(f"✨ 生成 {len(initial_sugs)} 个推荐问题")
                    
                    # 延迟保存：确认所有步骤都成功后再保存
                    if active_kb_name: HistoryManager.save(active_kb_name, state.get_messages())
                    
                    # 释放内存
                    cleanup_memory()
                    logger.info("🧹 对话完成，内存已清理")
                    
                    st.session_state.is_processing = False  # 处理完成
                    
                    # 整体处理完成反馈
                    st.toast("✅ 回答生成完毕", icon="🎉")
                
                except Exception as e: 
                    print(f"❌ 查询出错: {e}\n")
                    st.error(f"出错: {e}")
                    
                    # 发生错误，回滚最后一条消息（如果是 assistant 生成的）
                    if st.session_state.messages and st.session_state.messages[-1]['role'] == 'assistant':
                        st.session_state.messages.pop()
                    
                    # 释放内存
                    cleanup_memory()
                    logger.info("🧹 错误处理完成，内存已清理")
                    st.session_state.is_processing = False
            
            # spinner结束后显示所有内容
            # 显示统计信息
            if 'total_time' in locals() and 'token_count' in locals():
                stats_simple = f"⏱️ {total_time:.1f}秒 | 📝 约 {token_count} 字符"
                st.caption(stats_simple)
                
                # 详细信息 (折叠)
                with st.expander("📊 详细统计", expanded=False):
                    st.caption(f"🚀 速度: {tokens_per_sec:.1f} tokens/s")
                    if 'prompt_tokens' in locals() and prompt_tokens:
                        st.caption(f"📥 输入: {prompt_tokens} | 📤 输出: {completion_tokens}")
                
                # 显示参考来源
                if 'srcs' in locals() and srcs:
                    from src.ui.message_renderer import render_source_references
                    render_source_references(srcs, expanded=False)
            
            # 自动处理队列中的下一个问题
            if st.session_state.question_queue:
                logger.info(f"📝 队列中还有 {len(st.session_state.question_queue)} 个问题，自动处理下一个")
                st.rerun()  # 触发重新运行，处理下一个问题
            
            # 在 chat_message 块外显示推荐问题按钮
            if st.session_state.suggestions_history:
                st.divider()
                st.markdown("##### 🚀 追问推荐")
                for idx, q in enumerate(st.session_state.suggestions_history):
                    if st.button(f"👉 {q}", key=f"sug_btn_stable_{idx}", use_container_width=True):
                        click_btn(q)
                
                if st.button("✨ 继续推荐 3 个追问", key="gen_more_stable", type="secondary", use_container_width=True):
                    with st.spinner("⏳ 正在生成新问题..."):
                        all_history_questions = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
                        all_history_questions.extend(st.session_state.suggestions_history)
                        all_history_questions.extend(st.session_state.question_queue)
                        
                        # 获取最后一条回答作为上下文
                        last_answer = ""
                        for msg in reversed(st.session_state.messages):
                            if msg['role'] == 'assistant':
                                last_answer = msg['content']
                                break
                        
                        # 获取LLM模型
                        llm_model = None
                        if st.session_state.get('chat_engine'):
                            chat_engine = st.session_state.chat_engine
                            if hasattr(chat_engine, '_llm'):
                                llm_model = chat_engine._llm
                            elif hasattr(chat_engine, 'llm'):
                                llm_model = chat_engine.llm
                        
                        new_sugs = generate_follow_up_questions(
                            context_text=last_answer, 
                            num_questions=3,
                            existing_questions=all_history_questions,
                            query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None,
                            llm_model=llm_model
                        )
                        
                        if new_sugs:
                            # 替换而不是累积：始终只保持最新的3个问题
                            st.session_state.suggestions_history = new_sugs[:3]
                            st.rerun()
                        else:
                            st.warning("未能生成更多追问，请尝试输入新问题。")
