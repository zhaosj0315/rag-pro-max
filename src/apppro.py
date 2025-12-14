# 初始化环境配置
# 环境变量设置 - 减少启动警告
import os
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.environment import initialize_environment
initialize_environment()

import os
# 在最开始设置环境变量，禁用PaddleOCR详细日志
import os
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
from src.kb.kb_processor import KnowledgeBaseProcessor

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


from src.ui.compact_sidebar import render_compact_sidebar
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
                        /* 修复统计卡片显示 */
    [data-testid="metric-container"] {
        background: rgba(248, 249, 251, 0.8) !important;
        border: 1px solid rgba(0, 0, 0, 0.08) !important;
        border-radius: 8px !important;
        padding: 0.75rem !important;
        margin: 0.25rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
        min-height: 80px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
        border-color: rgba(31, 119, 180, 0.3) !important;
    }
    
    /* 统计数值样式 */
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: #1f77b4 !important;
        line-height: 1.2 !important;
        margin-bottom: 0.25rem !important;
    }
    
    /* 统计标签样式 */
    [data-testid="metric-container"] [data-testid="metric-label"] {
        font-size: 0.85rem !important;
        color: #6c757d !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    /* 确保统计区域布局正常 */
    .stMetric {
        background: transparent !important;
    }
    
    /* 修复可能的布局问题 */
    div[data-testid="column"] > div {
        height: auto !important;
    }
    
    /* 修复下拉框文字截断问题 */
    div[data-testid="stSelectbox"] > div > div {
        white-space: normal !important;
        height: auto !important;
        min-height: 40px !important;
    }
    
    /* 增加侧边栏宽度，防止内容过窄 */
    section[data-testid="stSidebar"] {
        min-width: 350px !important;
        width: 350px !important;
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
        padding-top: 1rem !important;
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
    # 横向标签页布局
    tab_main, tab_config, tab_monitor, tab_tools, tab_help = st.tabs(["🏠 主页", "⚙️ 配置", "📊 监控", "🔧 工具", "❓ 帮助"])
    
    with tab_main:
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
        st.markdown("### 💠 知识库控制台")
        if "model_list" not in st.session_state: st.session_state.model_list = []

        # 使用当前工作目录下的 vector_db_storage
        default_output_path = os.path.join(os.getcwd(), "vector_db_storage")
        output_base = st.text_input("存储根目录", value=default_output_path)
        existing_kbs = (setattr(kb_manager, "base_path", output_base), kb_manager.list_all())[1]

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
            # 头部控制区 - 单行布局
            if "path_val" not in st.session_state: 
                st.session_state.path_val = os.path.abspath(defaults.get("target_path", ""))
            if 'path_input' not in st.session_state:
                st.session_state.path_input = ""
            if st.session_state.get('uploaded_path') and not st.session_state.path_input:
                st.session_state.path_input = st.session_state.uploaded_path

            # 创建布局列
            if is_create_mode:
                action_mode = "NEW"
                path_col1, path_col2 = st.columns([5, 1])
                
                with path_col1:
                    target_path = st.text_input(
                        "文件/文件夹路径", 
                        value=st.session_state.path_input,
                        placeholder="📁 /Users/username/docs 或上传后自动生成",
                        key="path_input_display",
                        label_visibility="collapsed"
                    )
                with path_col2:
                    if st.button("📂", help="在Finder中打开", use_container_width=True):
                        # ... Finder 打开逻辑 ...
                        if target_path and os.path.exists(target_path):
                            import webbrowser
                            import urllib.parse
                            try:
                                file_url = 'file://' + urllib.parse.quote(os.path.abspath(target_path))
                                webbrowser.open(file_url)
                                st.toast("✅ 已打开")
                            except: pass
                        else:
                            st.warning("请先输入路径")
            else:
                # 管理模式：左侧操作模式，右侧路径
                mode_col, path_col1, path_col2 = st.columns([2, 4, 1])
                
                with mode_col:
                    action_mode_sel = st.radio("模式", ["➕ 追加", "🔄 覆盖"], horizontal=True, label_visibility="collapsed")
                    action_mode = "APPEND" if "追加" in action_mode_sel else "NEW"
                
                with path_col1:
                    target_path = st.text_input(
                        "路径",
                        value=st.session_state.path_input,
                        placeholder="📁 路径",
                        key="path_input_display",
                        label_visibility="collapsed"
                    )
                with path_col2:
                    if st.button("📂", help="打开", use_container_width=True):
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


            # 数据源输入选项卡
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
            
            with src_tab_web:
                # 输入方式选择 - 使用更紧凑的布局
                col1, col2 = st.columns(2)
                with col1:
                    url_mode = st.button("🔗 网址抓取", use_container_width=True, key="url_mode_btn")
                with col2:
                    search_mode = st.button("🔍 关键词搜索", use_container_width=True, key="search_mode_btn")
                
                # 根据按钮点击确定模式
                if url_mode:
                    st.session_state.crawl_input_mode = "url"
                elif search_mode:
                    st.session_state.crawl_input_mode = "search"
                
                # 获取当前模式
                current_mode = st.session_state.get('crawl_input_mode', 'url')
                
                if current_mode == "url":
                    # 网址抓取模式
                    crawl_url = st.text_input("🔗 网址", placeholder="python.org", help="支持自动添加https://")
                    search_keyword = None
                    
                    # 抓取参数
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        crawl_depth = st.number_input("递归深度", 1, 10, 2, help="抓取多少层链接")
                    with col2:
                        max_pages = st.number_input("每层页数", 1, 1000, 20, help="每层最多抓取页数")
                    with col3:
                        parser_type = st.selectbox("解析器", ["default", "article", "documentation"])
                    
                else:  # current_mode == "search"
                    # 关键词搜索模式
                    crawl_url = None
                    search_keyword = st.text_input("🔍 搜索关键词", placeholder="Python编程、机器学习、人工智能", help="全网搜索相关内容")
                    
                    # 搜索参数
                    col1, col2 = st.columns(2)
                    with col1:
                        max_pages = st.number_input("每引擎页数", 10, 500, 50, help="每个搜索引擎抓取的页数（共5个引擎：Google、Bing、维基百科、知乎、百度百科）")
                    with col2:
                        parser_type = st.selectbox("解析器", ["default", "article", "documentation"])
                    
                    crawl_depth = 1  # 搜索模式固定深度1
                
                # 排除配置 - 可选
                with st.expander("🚫 排除链接 (可选)", expanded=False):
                    exclude_text = st.text_area("每行一个，支持 * 通配符", 
                                               placeholder="*/admin/*\n*.pdf", 
                                               height=68)
                    exclude_patterns = [line.strip() for line in exclude_text.split('\n') if line.strip()] if exclude_text else []
                
                # 知识库设置
                st.write("### 📚 知识库设置")
                
                web_kb_name = st.text_input(
                    "知识库名称", 
                    placeholder="留空自动生成（推荐）", 
                    help="每次抓取创建独立的知识库，便于管理不同时间的内容"
                )
                
                st.caption("💡 每次抓取都会创建一个独立的知识库，包含本次抓取的所有网页")
                
                # 抓取按钮
                btn_disabled = not crawl_url and not search_keyword
                if st.button("🚀 抓取并创建知识库", use_container_width=True, type="primary", disabled=btn_disabled):
                    if crawl_url:
                        # 网址抓取模式
                        try:
                            from src.processors.web_crawler import WebCrawler
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
                                    exclude_patterns=exclude_patterns,
                                    parser_type=parser_type,
                                    status_callback=update_status
                                )
                            
                            progress_bar.progress(1.0)
                            
                            # 记录爬取结果
                            logger.success(f"🌐 网页爬取完成: 获取 {len(saved_files)} 个页面")
                            
                            if saved_files:
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
                                
                                st.success(f"✅ 抓取完成！获取 {len(saved_files)} 页，正在创建知识库: {kb_name}")
                                
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
                                    st.write(f"**抓取页面**: {len(saved_files)} 页")
                                    st.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                    for i, file_path in enumerate(saved_files[:3], 1):
                                        file_name = os.path.basename(file_path)
                                        st.text(f"{i}. {file_name}")
                                    if len(saved_files) > 3:
                                        st.text(f"... 还有 {len(saved_files) - 3} 个文件")
                                
                                # 推荐问题
                                try:
                                    from src.chat.web_suggestion_engine import WebSuggestionEngine
                                    web_engine = WebSuggestionEngine()
                                    web_suggestions = web_engine.generate_suggestions_from_crawl(crawl_url, saved_files)
                                    
                                    if web_suggestions:
                                        st.markdown("**💡 推荐问题:**")
                                        for i, suggestion in enumerate(web_suggestions[:3], 1):
                                            if st.button(suggestion, key=f"web_q_{i}", use_container_width=True):
                                                st.session_state.suggested_question = suggestion
                                                st.rerun()
                                except:
                                    pass
                                
                                st.rerun()
                            
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
                            
                            # 全网搜索网站列表
                            search_engines = [
                                f"https://www.google.com/search?q={search_keyword}",
                                f"https://www.bing.com/search?q={search_keyword}",
                                f"https://zh.wikipedia.org/wiki/Special:Search?search={search_keyword}",
                                f"https://www.zhihu.com/search?type=content&q={search_keyword}",
                                f"https://baike.baidu.com/search?word={search_keyword}"
                            ]
                            
                            # 记录搜索开始
                            logger.info(f"🔍 开始关键词搜索: '{search_keyword}' (每个引擎:{max_pages}页, 共{len(search_engines)}个引擎)")
                            
                            # 在多个搜索引擎中搜索
                            for i, search_url in enumerate(search_engines):
                                engine_name = ["Google", "Bing", "维基百科", "知乎", "百度百科"][i]
                                update_status(f"正在搜索 {engine_name}: {search_keyword}")
                                logger.info(f"🔍 搜索引擎: {engine_name} - {search_url}")
                                
                                try:
                                    with st.spinner(f"搜索 {engine_name}..."):
                                        saved_files = crawler.crawl_advanced(
                                            start_url=search_url,
                                            max_depth=2,  # 深度2才能抓取搜索结果链接指向的页面
                                            max_pages=max_pages,  # 每个搜索引擎使用完整的页数
                                            exclude_patterns=exclude_patterns,
                                            parser_type=parser_type,
                                            status_callback=update_status
                                        )
                                        all_saved_files.extend(saved_files)
                                        
                                    progress_bar.progress((i + 1) / len(search_engines))
                                    
                                except Exception as e:
                                    update_status(f"❌ {engine_name} 搜索失败: {e}")
                                    continue
                            
                            progress_bar.progress(1.0)
                            
                            if all_saved_files:
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
                                
                                st.success(f"✅ 全网搜索完成！获取 {len(all_saved_files)} 页，正在创建知识库: {kb_name}")
                                
                                # 记录搜索完成
                                logger.success(f"🔍 关键词搜索完成: '{search_keyword}' - 获取 {len(all_saved_files)} 个页面")
                                
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
                                    st.write(f"**抓取页面**: {len(all_saved_files)} 页")
                                    st.write(f"**创建时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                
                                st.rerun()
                            
                            else:
                                st.warning("未搜索到相关内容")
                                
                        except Exception as e:
                            st.error(f"搜索失败: {str(e)}")
                
                # 简洁的使用提示
                st.caption("💡 支持 python.org 等简化输入，自动添加 https:// 前缀")

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
                        with st.expander("查看跳过详情", expanded=True):
                            for reason in result.skip_reasons:
                                st.text(f"• {reason}")

                    # 为文件上传场景生成智能名称
                    if result.success_count > 0:
                        try:
                            # 计算文件类型分布
                            file_types = {}
                            for filename in current_names:
                                ext = os.path.splitext(filename)[1].lower()
                                file_types[ext] = file_types.get(ext, 0) + 1

                            # 使用上传的文件名生成智能名称
                            folder_name = os.path.basename(result.batch_dir)  # batch_xxx
                            auto_name = generate_smart_kb_name(result.batch_dir, result.success_count, file_types, folder_name)

                            # 存储智能生成的名称
                            st.session_state.upload_auto_name = auto_name
                        except Exception as e:
                            st.session_state.upload_auto_name = None

                    time.sleep(1)
                    if result.success_count > 0:
                        st.rerun()


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

                    # 仅在没有预设名称时使用文件夹名
                    if not (hasattr(st.session_state, 'upload_auto_name') and st.session_state.upload_auto_name):
                        auto_name = folder_name

                    # 智能生成知识库名称
                    if cnt > 0:
                        # 如果已有来自爬虫的特定名称，不要覆盖
                        if not (hasattr(st.session_state, 'upload_auto_name') and st.session_state.upload_auto_name):
                            auto_name = generate_smart_kb_name(target_path, cnt, file_types, folder_name)
                else:
                    st.error("❌ 路径不存在，请检查路径是否正确")

            # final_kb_name 必须在 if/else 中被定义，以确保其在模块作用域内
            st.write("")
            if is_create_mode:
                st.markdown("**知识库名称**")

                # 显示智能建议
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
                # 第一行：索引和元数据选项
                adv_col1, adv_col2 = st.columns(2)
                with adv_col1:
                    force_reindex = st.checkbox("🔄 强制重建索引", False, help="删除现有索引，重新构建")
                    use_ocr = st.checkbox("🔍 启用OCR识别", value=False, help="识别PDF中的图片文字（耗时较长）", key="kb_use_ocr")
                with adv_col2:
                    extract_metadata = st.checkbox("📊 提取元数据", value=False, help="提取文件分类、关键词等信息")
                    generate_summary = st.checkbox("📝 生成文档摘要", value=False, help="为每个文档生成AI摘要", key="kb_generate_summary")
                
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
            
            # 检查是否需要自动构建知识库（网页抓取触发）
            if st.session_state.get('auto_build_kb', False):
                st.session_state.auto_build_kb = False  # 清除标记
                btn_start = True  # 自动触发构建

        # --- 现有库的管理 ---
        if not is_create_mode:
            st.write("")
            
            # 💬 聊天控制 - 2×2布局
            st.write("**💬 聊天控制**")
            row1_col1, row1_col2 = st.columns(2)
            row2_col1, row2_col2 = st.columns(2)
            
            with row1_col1:
                if st.button("🔄 撤销", use_container_width=True, disabled=len(state.get_messages()) < 2):
                    if len(state.get_messages()) >= 2:
                        st.session_state.messages.pop()
                        st.session_state.messages.pop()
                        if current_kb_name:
                            HistoryManager.save(current_kb_name, state.get_messages())
                        st.toast("✅ 已撤销")
                        time.sleep(0.5)
                        st.rerun()
            
            with row1_col2:
                if st.button("🧹 清空", use_container_width=True, disabled=len(state.get_messages()) == 0):
                    st.session_state.messages = []
                    st.session_state.suggestions_history = []
                    if current_kb_name:
                        HistoryManager.save(current_kb_name, [])
                    st.toast("✅ 已清空")
                    time.sleep(0.5)
                    st.rerun()
            
            with row2_col1:
                export_content = ""
                if len(state.get_messages()) > 0:
                    export_content = f"# 对话记录 - {current_kb_name}\n\n**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
                    for i, msg in enumerate(st.session_state.messages, 1):
                        role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
                        export_content += f"## {role} ({i})\n\n{msg['content']}\n\n"
                
                st.download_button("📥 导出", export_content, file_name=f"chat_{current_kb_name}_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown", use_container_width=True, disabled=len(state.get_messages()) == 0)
            
            with row2_col2:
                if st.button("📊 统计", use_container_width=True, disabled=len(state.get_messages()) == 0):
                    qa_count = len(state.get_messages()) // 2
                    total_chars = sum(len(msg["content"]) for msg in st.session_state.messages)
                    st.toast(f"💬 {qa_count} 轮对话 | 📝 {total_chars} 字符")
            
            st.write("")
            
            # 🛠️ 系统操作 - 1×2布局
            st.write("**🛠️ 系统操作**")
            sys_col1, sys_col2 = st.columns(2)
            
            with sys_col1:
                st.link_button("🔀 新窗口", "http://localhost:8501", use_container_width=True)
            
            with sys_col2:
                if st.button("🗑️ 删除知识库", use_container_width=True, disabled=not current_kb_name):
                    st.session_state.confirm_delete = True
                    st.rerun()
            
            # 删除确认对话框
            if st.session_state.get('confirm_delete', False):
                st.warning(f"⚠️ 确认删除知识库 '{current_kb_name}' 吗？")
                confirm_col1, confirm_col2 = st.columns(2)
                
                with confirm_col1:
                    if st.button("✅ 确认删除", type="primary", use_container_width=True):
                        st.toast(f"🗑️ 已删除知识库: {current_kb_name}")
                        st.session_state.current_nav = "➕ 新建知识库..."
                        st.session_state.confirm_delete = False
                        st.rerun()
                
                with confirm_col2:
                    if st.button("❌ 取消", use_container_width=True):
                        st.session_state.confirm_delete = False
                        st.rerun()

            # 底部工具栏 - 单行布局
            st.write("")
            tool_cols = st.columns(3)
            
    
    with tab_config:
        st.session_state.current_tab = "config"
        st.markdown("### ⚙️ 模型配置")
        
        # P0改进3: 侧边栏分组 - 基础配置（默认展开）- 使用新组件 (Stage 3.2.2)
        config_values = render_basic_config(defaults)

        # 提取配置值
        llm_provider = config_values.get('llm_provider', 'Ollama')
        llm_url = config_values.get('llm_url', 'http://localhost:11434')
        llm_model = config_values.get('llm_model', 'qwen2.5:7b')
        llm_key = config_values.get('llm_key', '')
        embed_provider = config_values.get('embed_provider', 'HuggingFace (本地/极速)')
        embed_model = config_values.get('embed_model', 'BAAI/bge-small-zh-v1.5')
        embed_url = config_values.get('embed_url', '')
        embed_key = config_values.get('embed_key', '')

        # 设置全局LLM（确保查询改写等功能可以使用）
        if not hasattr(Settings, 'llm') or Settings.llm is None:
            set_global_llm_model(llm_provider, llm_model, llm_key, llm_url)

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
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.metric("CPU 使用率", f"{cpu_percent:.1f}%")
                with col2:
                    st.caption(f"{psutil.cpu_count()} 核")
                st.progress(cpu_percent / 100)

                col1, col2 = st.columns([4, 1])
                with col1:
                    st.metric("GPU 状态", "活跃" if gpu_active else "空闲")
                with col2:
                    st.caption("32 核")
                if gpu_active:
                    st.progress(0.5)
                else:
                    st.progress(0.0)

                col1, col2 = st.columns([4, 1])
                with col1:
                    st.metric("内存使用", f"{mem.percent:.1f}%")
                with col2:
                    st.caption(f"{mem.used/1024**3:.1f}GB")
                st.progress(mem.percent / 100)

                col1, col2 = st.columns([4, 1])
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
        st.markdown("#### ⬆️ 快速上传")
        uploaded_file = st.file_uploader("选择文件", type=['pdf', 'txt', 'docx', 'md'], key="tools_uploader")
        if uploaded_file:
            st.success(f"✅ 已选择: {uploaded_file.name}")
            st.info("💡 请到主页完成处理")
    
    with tab_help:
        st.markdown("### 📖 帮助")
        st.info("RAG Pro Max v2.2.1 - 横向标签页版本")

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

def process_knowledge_base_logic():
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
        logger.error(f"❌ 嵌入模型加载失败: {embed_model}")
        raise ValueError(f"无法加载嵌入模型: {embed_model}")
    
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
        extract_metadata=extract_metadata,  # 传递性能选项
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
st.title("🛡️ RAG Pro Max")

# 引入新的优化组件
from src.utils.enhanced_ocr_optimizer import enhanced_ocr_optimizer
from src.ui.progress_monitor import progress_monitor

# 显示实时进度监控
progress_monitor.render_all_tasks()

# 在侧边栏添加性能统计
with st.sidebar:
    # v2.3.0: 智能监控状态
    try:
        from src.core.v23_integration import get_v23_integration
        v23 = get_v23_integration()
        v23.render_v23_sidebar()
    except ImportError:
        pass
    
    with st.expander("📊 性能统计", expanded=True):
        stats = enhanced_ocr_optimizer.get_performance_stats()
        for key, value in stats.items():
            st.write(f"**{key}**: {value}")
        
        if st.button("🧪 运行性能测试"):
            with st.spinner("正在运行性能基准测试..."):
                benchmark_results = enhanced_ocr_optimizer.benchmark_performance()
                st.json(benchmark_results)

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
    """点击追问按钮，将问题加入队列（去重）"""
    from src.queue.queue_manager import QueueManager
    queue_manager = QueueManager()
    queue_manager.add_question(q)
    st.rerun()

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
    chat_engine, error_msg = kb_loader.load_knowledge_base(
        active_kb_name, embed_provider, embed_model, embed_key, embed_url
    )
    
    if chat_engine:
        st.session_state.chat_engine = chat_engine
        logger.success("问答引擎已启用GPU加速")
        logger.log("SUCCESS", f"知识库加载成功: {active_kb_name}", stage="知识库加载")
        st.toast(f"✅ 知识库 '{active_kb_name}' 挂载成功！")
        cleanup_memory()
    else:
        logger.log("ERROR", f"知识库加载失败: {active_kb_name} - {error_msg}", stage="知识库加载")
        if "维度不匹配" in error_msg:
            # 处理维度不匹配的特殊情况
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 重建索引", type="primary", use_container_width=True):
                    with st.spinner("正在清理旧索引..."):
                        import shutil
                        db_path = os.path.join(output_base, active_kb_name)
                        shutil.rmtree(db_path, ignore_errors=True)
                        st.success("✅ 索引已清理，请重新上传文档")
                        time.sleep(2)
                        st.rerun()
            with col2:
                if st.button("↩️ 切换模型", use_container_width=True):
                    st.info("请在侧边栏选择原模型（通常是 bge-small-zh-v1.5）")
            st.stop()
        else:
            st.error(f"知识库挂载失败：{error_msg}")
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
            
            process_knowledge_base_logic()
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
            # 文档列表查看
            tab1, tab2 = st.tabs(["📊 统计信息", "📄 文档列表"])
            
            with tab1:
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
            run_summary = False
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
                                file_info['summary'] = summary
                                success_count += 1
                    except Exception as e:
                        st.warning(f"⚠️ {fname}: {str(e)}")
                        
                        progress_bar.progress((i + 1) / selected_count)
                    
                    # 保存 manifest
                    with open(ManifestManager.get_path(db_path), 'w', encoding='utf-8') as f:
                        json.dump(doc_manager.manifest, f, indent=4, ensure_ascii=False)
                    
                    status_text.empty()
                    progress_bar.empty()
                    st.success(f"✅ 已生成 {success_count}/{selected_count} 个摘要")
                    st.session_state.selected_for_summary = set()
                    time.sleep(1)
                    st.rerun()  # 立即刷新页面显示摘要
            
            # 文档列表标签页 (v1.6)
            with tab2:
                show_kb_documents(active_kb_name)
            
            st.divider()
            
            # 搜索筛选排序（单行超紧凑布局）
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2.5, 1.2, 1.2, 1.2, 1.2, 1.5, 1])
            search_term = col1.text_input("🔍", "", key="file_search", placeholder="搜索文件名...", label_visibility="collapsed")
            filter_type = col2.selectbox("📂", ["全部"] + sorted(set(f.get('type', 'Unknown') for f in doc_manager.manifest['files'])), label_visibility="collapsed")
            
            # 分类筛选
            all_categories = set(f.get('category', '其他') for f in doc_manager.manifest['files'] if f.get('category'))
            filter_category = col3.selectbox("📋", ["全部"] + sorted(all_categories), label_visibility="collapsed") if all_categories else "全部"
            
            # 热度筛选
            filter_heat = col4.selectbox("🔥", ["全部", "高频", "中频", "低频", "未用"], label_visibility="collapsed")
            
            # 质量筛选
            filter_quality = col5.selectbox("✅", ["全部", "优秀", "正常", "低质", "空"], label_visibility="collapsed")
            
            sort_by = col6.selectbox("排序", ["时间↓", "时间↑", "大小↓", "大小↑", "名称", "热度↓", "片段↓"], label_visibility="collapsed")
            page_size = col7.selectbox("页", [10, 20, 50, 100], index=0, label_visibility="collapsed")
            
            # 筛选文件
            filtered_files = doc_manager.manifest['files']
            
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
                            # 格式：📄 文件名.pdf  [灰色小字: 2.5MB · 2023-12-12 · 质量 · 命中3次]
                            file_icon = f.get('icon', '📄')
                            
                            # 截断超长文件名
                            fname = f['name']
                            if len(fname) > 25: fname = fname[:23] + "..."
                            
                            # 添加更多关键信息到一行中
                            hit_count = f.get('hit_count', 0)
                            category = f.get('category', '')
                            hit_info = f"命中{hit_count}次" if hit_count > 0 else ""
                            category_info = f"{category}" if category and category != '未分类' else ""
                            
                            # 组合额外信息
                            extra_info = " · ".join(filter(None, [hit_info, category_info]))
                            if extra_info:
                                extra_info = " · " + extra_info
                            
                            line_html = f"""
                            <div style='display: flex; align-items: baseline; white-space: nowrap; overflow: hidden;'>
                                <span style='font-weight: 600; font-size: 1rem; margin-right: 0.5rem;'>{file_icon} {fname}</span>
                                <span style='color: gray; font-size: 0.75rem;'>
                                    {f['size']} · {chunk_count}片段 · {display_date} · {q_icon}{extra_info}
                                </span>
                            </div>
                            """
                            st.markdown(line_html, unsafe_allow_html=True)
                            
                            # 显示摘要（如果有的话）
                            if f.get('summary'):
                                summary_text = f['summary']
                                if len(summary_text) > 100:
                                    summary_text = summary_text[:97] + "..."
                                st.caption(f"📝 {summary_text}")
                        
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
                                                    
                                                    # 保存manifest
                                                    from src.config.manifest_manager import ManifestManager
                                                    ManifestManager.save(db_path, doc_manager.manifest['files'], doc_manager.manifest.get('embed_model', 'Unknown'))
                                                    
                                                    st.success("✅ 摘要生成成功！")
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
                            # 操作区：仅保留删除按钮，节省空间
                            # 这里的 key 必须唯一
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

# 模型与任务设置
with st.expander("🤖 模型与任务设置", expanded=False):
    # 获取可用模型列表
    try:
        ollama_url = st.session_state.get('llm_url', "http://localhost:11434")
        models, error = fetch_remote_models(ollama_url, "")
        
        if models:
            available_models = models
        else:
            # logger.warning(f"无法获取模型列表: {error}")
            available_models = ["llama3", "mistral", "gemma", "deepseek-coder", "qwen2.5:7b"] # Fallback list
    except Exception as e:
        # logger.error(f"获取模型列表异常: {e}")
        available_models = ["llama3", "mistral", "qwen2.5:7b"]
        
    # 获取当前模型
    current_model = st.session_state.get('selected_model', 'qwen2.5:7b')
    if current_model not in available_models:
        # 如果当前模型不在列表中（可能是初次加载），尝试匹配
        if available_models:
            # 优先保持当前设置（如果只是列表获取失败），否则选第一个
            if current_model not in ["llama3", "mistral", "qwen2.5:7b"]:
                 current_model = available_models[0]
            
    # 模型选择下拉框
    selected_model_new = st.selectbox(
        "选择 AI 模型 (根据任务需求切换)",
        options=available_models,
        index=available_models.index(current_model) if current_model in available_models else 0,
        key="model_selector_dropdown",
        help="Code: 写代码 | Vision: 看图 | Chat: 闲聊"
    )
    
    # 检测模型变更
    if selected_model_new != st.session_state.get('selected_model'):
        st.session_state.selected_model = selected_model_new
        # 切换全局 LLM
        # 假设都是 Ollama 模型，如果有其他 provider 需要更复杂的逻辑
        if set_global_llm_model("Ollama", selected_model_new, api_url=ollama_url):
            st.toast(f"✅ 已切换到模型: {selected_model_new}", icon="🤖")
        else:
            st.toast(f"❌ 切换模型失败: {selected_model_new}", icon="⚠️")

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

# 查询优化设置
with st.expander("🔧 查询设置", expanded=False):
    enable_query_optimization = st.checkbox(
        "💡 启用查询优化", 
        value=st.session_state.get('enable_query_optimization', False),
        help="AI会分析并优化你的问题，提升检索准确性"
    )
    st.session_state.enable_query_optimization = enable_query_optimization
    
    if enable_query_optimization:
        st.caption("✅ 系统会建议优化查询，由你选择是否使用")
    else:
        st.caption("📝 直接使用原问题进行检索")

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
                512: "BAAI/bge-small-zh-v1.5",
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
                    if st.button(f"👉 {q}", key=f"sug_btn_{int(time.time())}_{idx}", use_container_width=True):
                        click_btn(q)
                
                if st.button("✨ 继续推荐 3 个追问", key=f"gen_more_{int(time.time())}", type="secondary", use_container_width=True):
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
