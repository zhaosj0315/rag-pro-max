# 初始化环境配置
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.environment import initialize_environment
initialize_environment()

import os
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

# 文档预览 (v1.6)
from src.kb.document_viewer import DocumentViewer
from src.ui.document_preview import show_upload_preview, show_kb_documents

def generate_smart_kb_name(target_path, cnt, file_types, folder_name):
    """智能生成知识库名称 - 重点优化多文件和文件夹场景"""
    import re
    from datetime import datetime
    
    # 分析文件类型
    main_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
    if not main_types:
        return f"{folder_name}_{datetime.now().strftime('%m%d')}"
    
    main_ext = main_types[0][0].replace('.', '').upper()
    
    # 获取所有文件名（不含扩展名）
    all_files = []
    try:
        for f in os.listdir(target_path):
            if not f.startswith('.'):
                all_files.append(os.path.splitext(f)[0])
    except:
        pass
    
    # 策略1: 单文件 - 清理文件名
    if cnt == 1 and all_files:
        filename = all_files[0]
        clean_name = re.sub(r'[_\-\s]*(?:v?\d+[\.\d]*|20\d{2}[\-\d]*|final|draft|copy|backup|new|old|temp).*$', '', filename, flags=re.IGNORECASE)
        clean_name = re.sub(r'^[_\-\s]+|[_\-\s]+$', '', clean_name)
        if clean_name and len(clean_name) > 2:
            return clean_name[:20]
    
    # 策略2: 多文件 - 寻找共同前缀（优先级最高）
    if len(all_files) > 1:
        common_prefix = os.path.commonprefix(all_files)
        clean_prefix = re.sub(r'[_\-\s\d]*$', '', common_prefix)
        if len(clean_prefix) >= 3:
            return clean_prefix[:15]
    
    # 策略3: 分析高频有意义词汇（文件上传场景重点优化）
    if all_files:
        words = []
        for filename in all_files:
            parts = re.split(r'[_\-\s\.\d]+', filename.lower())
            words.extend([w for w in parts if len(w) >= 3])
        
        if words:
            from collections import Counter
            word_freq = Counter(words)
            stop_words = {
                'the', 'and', 'for', 'with', 'doc', 'file', 'new', 'old', 'temp', 'test', 'demo',
                'pdf', 'docx', 'txt', 'xlsx', 'ppt', 'html', 'json', 'csv', 'info', 'case'
            }
            # 降低阈值：只需出现1次，但优先选择出现多次的
            meaningful_words = [
                (w, c) for w, c in word_freq.most_common(5) 
                if w not in stop_words and len(w) >= 3
            ]
            if meaningful_words:
                # 优先选择出现次数多的，其次选择长度长的
                best_word = max(meaningful_words, key=lambda x: (x[1], len(x[0])))
                return best_word[0].capitalize()[:12]
    
    # 策略4: 基于文件夹名（如果有意义且不是batch_xxx）
    if folder_name and not folder_name.startswith('batch_') and folder_name not in ['temp_uploads', 'uploads', 'documents', 'files', 'temp']:
        clean_folder = re.sub(r'[_\-\s]*(?:20\d{2}[\-\d]*|backup|copy|new|old|temp|v\d+).*$', '', folder_name, flags=re.IGNORECASE)
        clean_folder = re.sub(r'^[_\-\s]+|[_\-\s]+$', '', clean_folder)
        
        # 文件夹名智能处理
        if clean_folder and len(clean_folder) >= 2:
            # 处理下划线分隔的复合词
            if '_' in clean_folder:
                parts = clean_folder.split('_')
                meaningful_parts = [p for p in parts[:3] if len(p) >= 2]
                if meaningful_parts:
                    if len(meaningful_parts) == 1:
                        return meaningful_parts[0][:15]
                    else:
                        combined = '_'.join(meaningful_parts[:2])
                        return combined[:15]
            else:
                return clean_folder[:15]
    
    # 策略5: 基于文件类型的智能命名（最后选择）
    type_names = {
        'PDF': '文档库', 'DOCX': '文档库', 'DOC': '文档库',
        'MD': '笔记本', 'TXT': '文本集',
        'PY': 'Python项目', 'JS': 'JS项目', 'JAVA': 'Java项目',
        'XLSX': '数据表', 'CSV': '数据集',
        'PPT': '演示文稿', 'PPTX': '演示文稿',
        'HTML': '网页集', 'JSON': '配置集'
    }
    
    base_name = type_names.get(main_ext, f"{main_ext}文件")
    date_suffix = datetime.now().strftime("%m%d")
    return f"{base_name}_{date_suffix}"

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
    logger.separator("RAG Pro Max 启动")
    logger.info("应用初始化中...")
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
    
    # v1.5.1: 性能监控面板
    perf_monitor.render_panel()
    
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
        
        # 文档预览 (v1.6) - 带翻页
        if uploaded_files:
            with st.expander(f"📄 已选择 {len(uploaded_files)} 个文件 - 点击预览", expanded=False):
                # 翻页设置
                page_size = 10
                total_pages = (len(uploaded_files) - 1) // page_size + 1
                
                if 'preview_page' not in st.session_state:
                    st.session_state.preview_page = 0
                
                # 翻页控制
                col1, col2, col3 = st.columns([1, 2, 1])
                if col1.button("⬅️ 上一页", disabled=st.session_state.preview_page == 0):
                    st.session_state.preview_page -= 1
                    st.rerun()
                col2.write(f"第 {st.session_state.preview_page + 1}/{total_pages} 页")
                if col3.button("下一页 ➡️", disabled=st.session_state.preview_page >= total_pages - 1):
                    st.session_state.preview_page += 1
                    st.rerun()
                
                st.divider()
                
                # 显示当前页的文件
                start_idx = st.session_state.preview_page * page_size
                end_idx = min(start_idx + page_size, len(uploaded_files))
                
                for idx, uploaded_file in enumerate(uploaded_files[start_idx:end_idx]):
                    col1, col2, col3 = st.columns([4, 1, 1])
                    col1.write(f"📎 {uploaded_file.name}")
                    col2.write(f"{uploaded_file.size / 1024:.1f} KB")
                    if col3.button("👁️", key=f"preview_{start_idx + idx}_{uploaded_file.name}_{uploaded_file.size}", help="预览"):
                        st.session_state['preview_file'] = uploaded_file
                
                # 显示预览对话框
                if 'preview_file' in st.session_state and st.session_state.preview_file:
                    show_upload_preview(st.session_state.preview_file)
                    st.session_state.preview_file = None
        
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
                
                auto_name = folder_name
                
                # 智能生成知识库名称
                if cnt > 0:
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
                    HistoryManager.save(current_kb_name, state.get_messages())
                st.toast("✅ 已撤销上一条消息")
                time.sleep(0.5)
                st.rerun()
        
        # 清空按钮
        if col2.button("🧹 清空对话", use_container_width=True, disabled=len(state.get_messages()) == 0):
            st.session_state.messages = []
            st.session_state.suggestions_history = []
            if current_kb_name:
                HistoryManager.save(current_kb_name, [])
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
        logger.success("快速开始模式：已配置默认值")
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
    
    status_container.update(label=f"✅ 知识库 '{final_kb_name}' 处理完成", state="complete", expanded=False)
    
    # 资源清理
    resource_guard.throttler.cleanup_memory()
    logger.info("🧹 资源已清理")
    
    time.sleep(0.5)
    return result.doc_count

# ==========================================
# 6. 聊天界面 & 无限追问功能
# ==========================================
st.title("🛡️ RAG Pro Max")

# 紧凑侧边栏CSS样式
st.markdown("""
<style>
/* 侧边栏紧凑化 */
.css-1d391kg {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
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
            files_without_summary = [f for f in doc_manager.manifest['files'] if not f.get('summary') and f.get('doc_ids')]
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
                
                if st.button("📥 导出清单", use_container_width=True):
                    export_data = f"知识库: {active_kb_name}\n文件数: {stats['file_cnt']}\n片段数: {stats['total_chunks']}\n\n文件列表:\n"
                    for f in doc_manager.manifest['files']:
                        export_data += f"- {f['name']} ({f['type']}, {len(f.get('doc_ids', []))} 片段)\n"
                    st.download_button("下载", export_data, f"{active_kb_name}_清单.txt", use_container_width=True)
            
            # 文档列表标签页 (v1.6)
            with tab2:
                show_kb_documents(active_kb_name)
            
            st.divider()
            
            # 搜索筛选排序（单行超紧凑布局）
            col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 1, 1, 1, 1, 1.2, 0.8])
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
                    orig_idx = doc_manager.manifest['files'].index(f)
                    
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
                                other for other in doc_manager.manifest['files']
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
                                            manifest = ManifestManager.load(db_path)
                                            for file in manifest['files']:
                                                if file['name'] == f['name']:
                                                    file['summary'] = summary
                                                    break
                                            
                                            # 保存 manifest
                                            with open(ManifestManager.get_path(db_path), 'w', encoding='utf-8') as mf:
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
                logger.info(f"💬 摘要生成使用模型: {current_model}")
                
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
                HistoryManager.save(active_kb_name, state.get_messages())
                st.rerun()
            except Exception as e:
                error_msg = str(e)
                if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                    summary_placeholder.info("⏱️ LLM 响应超时，已跳过自动摘要。您可以直接开始提问。")
                    logger.warning(f"⏱️ 摘要生成超时: {e}")
                else:
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
            kb_name = os.path.basename(db_path)
            kb_manager.save_info(kb_name, embed_model, 0)
            
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
        
        logger.separator("知识库查询")
        logger.start_operation("查询", f"知识库: {active_kb_name}")
        
        # 查询改写 (v1.6) - 在处理引用内容之前
        query_rewriter = QueryRewriter(Settings.llm)
        should_rewrite, reason = query_rewriter.should_rewrite(final_prompt)
        
        if should_rewrite:
            logger.info(f"💡 检测到需要改写查询: {reason}")
            rewritten_query = query_rewriter.suggest_rewrite(final_prompt)
            
            if rewritten_query and rewritten_query != final_prompt:
                # 保存原问题用于显示
                original_prompt = final_prompt
                # 自动使用优化后的查询，不等待用户选择
                logger.info(f"✅ 自动使用优化后的查询: {final_prompt} → {rewritten_query}")
                final_prompt = rewritten_query
                
                # 显示改写信息（不阻塞）
                with st.chat_message("assistant", avatar="🤖"):
                    st.info(f"💡 **查询已自动优化**\n\n原问题：{original_prompt}\n\n优化后：{rewritten_query}")
        
        
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
                    
                    # status 块结束，确保回答仍然显示
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
                        
                        # 使用并行执行器处理节点（自动判断串行/并行）
                        executor = ParallelExecutor()
                        tasks = [(d, active_kb_name) for d in node_data]
                        # 使用串行处理避免多进程问题
                        srcs = [process_node_worker(task) for task in tasks]
                        
                        if len(node_data) >= 10:
                            logger.info(f"⚡ 并行处理: {len(srcs)} 个节点")
                        else:
                            logger.info(f"⚡ 串行处理: {len(srcs)} 个节点")
                    
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
                    
                    # 获取LLM模型
                    llm_model = None
                    if st.session_state.get('chat_engine'):
                        chat_engine = st.session_state.chat_engine
                        if hasattr(chat_engine, '_llm'):
                            llm_model = chat_engine._llm
                            logger.info(f"🔍 从chat_engine._llm获取LLM: {type(llm_model)}")
                        elif hasattr(chat_engine, 'llm'):
                            llm_model = chat_engine.llm
                            logger.info(f"🔍 从chat_engine.llm获取LLM: {type(llm_model)}")
                        else:
                            logger.info("⚠️ chat_engine中未找到LLM")
                    else:
                        logger.info("⚠️ chat_engine未设置")
                    
                    logger.info(f"🔍 推荐问题生成 - LLM可用: {llm_model is not None}")
                    
                    initial_sugs = generate_follow_up_questions(
                        full_text, 
                        num_questions=3,
                        existing_questions=existing_questions,
                        query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None,
                        llm_model=llm_model
                    )
                    sug_container.empty()
                    
                    if initial_sugs:
                        # 设置推荐问题
                        st.session_state.suggestions_history = initial_sugs[:3]
                        
                        # 详细日志记录
                        logger.info(f"✨ 生成 {len(initial_sugs)} 个新推荐问题")
                        for i, q in enumerate(initial_sugs[:3], 1):
                            logger.info(f"   {i}. {q}")
                    else:
                        logger.info("⚠️ 推荐问题生成失败")
                    
                    # 延迟保存：确认所有步骤（包括推荐问题）都成功后再保存
                    if active_kb_name: HistoryManager.save(active_kb_name, state.get_messages())
                    
                    # 释放内存
                    cleanup_memory()
                    logger.info("🧹 对话完成，内存已清理")
                    
                    st.session_state.is_processing = False  # 处理完成
                    
                    # 自动处理队列中的下一个问题
                    if st.session_state.question_queue:
                        logger.info(f"📝 队列中还有 {len(st.session_state.question_queue)} 个问题，自动处理下一个")
                        st.rerun()  # 触发重新运行，处理下一个问题
                except Exception as e: 
                    print(f"❌ 查询出错: {e}\n")
                    st.error(f"出错: {e}")
                    
                    # 发生错误，回滚最后一条消息（如果是 assistant 生成的）
                    # 避免保存不完整的回答
                    if st.session_state.messages and st.session_state.messages[-1]['role'] == 'assistant':
                        st.session_state.messages.pop()
                    
                    # 释放内存
                    cleanup_memory()
                    logger.info("🧹 错误处理完成，内存已清理")
                    st.session_state.is_processing = False
            
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
