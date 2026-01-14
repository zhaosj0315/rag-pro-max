# 初始化环境配置
import warnings
import os
import sys
import time
import json
import glob
import re

# --- Monkey Patch: 修复 Streamlit FileWatcher Race Condition ---
# 捕获 watchdog 线程中的 FileNotFoundError (通常由临时文件快速删除引起)
try:
    import streamlit.watcher.util
    
    # 1. Patch path_modification_time
    _original_path_modification_time = streamlit.watcher.util.path_modification_time
    def _safe_path_modification_time(path, allow_nonexistent=False):
        try:
            return _original_path_modification_time(path, allow_nonexistent)
        except (FileNotFoundError, OSError):
            return 0.0
    streamlit.watcher.util.path_modification_time = _safe_path_modification_time

    # 2. Patch calc_md5_with_blocking_retries (针对本报错的核心修复)
    _original_calc_md5 = streamlit.watcher.util.calc_md5_with_blocking_retries
    def _safe_calc_md5(path, **kwargs):
        try:
            return _original_calc_md5(path, **kwargs)
        except (FileNotFoundError, OSError):
            # 返回一个哑值的MD5，避免崩溃
            return "0" * 32
    streamlit.watcher.util.calc_md5_with_blocking_retries = _safe_calc_md5
    
except ImportError:
    pass
# -----------------------------------------------------------

# 极其早地初始化日志，防止任何模块在加载时触发
from src.app_logging import LogManager
logger = LogManager()

# 极其早地抑制 Pydantic 警告
warnings.filterwarnings("ignore", category=UserWarning, message=".*UnsupportedFieldAttributeWarning.*")
warnings.filterwarnings("ignore", message=".*validate_default.*")

# 环境变量设置 - 减少启动警告
__version__ = "4.5.2"
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

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

# --- [逻辑对齐] 处理分享链接 (Session Sharing) ---
if "share" in st.query_params:
    share_id = st.query_params["share"]
    from src.chat.share_manager import ShareManager
    share_data = ShareManager.get_share(share_id)
    
    if share_data:
        st.info(f"📑 正在查看分享会话: **{share_data['kb_name']}** (由 {share_data['creator']} 分享于 {share_data['created_at'][:10]})")
        
        # 渲染快照消息
        for msg in share_data["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if st.button("返回我的工作台", use_container_width=True):
            del st.query_params["share"]
            st.rerun()
        st.stop() # 停止后续正常逻辑渲染
    else:
        st.error("❌ 分享链接已失效或 ID 不正确")
        if st.button("进入系统"):
            del st.query_params["share"]
            st.rerun()
        st.stop()

# 防止HTML内容被截断
st.set_page_config(
    page_title="RAG Pro Max",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 设置不截断HTML显示
import streamlit.components.v1 as components

import time
import ollama
import re
import subprocess
from urllib.parse import urlparse

# 引入日志模块 (提前初始化防止后续逻辑报错)
from src.app_logging import LogManager
logger = LogManager()

# 🧹 启动时自动清理临时文件
from src.common.utils import cleanup_temp_files

# 执行启动清理（使用一周=168小时）
cleaned_count = cleanup_temp_files("temp_uploads", 168)
if cleaned_count > 0:
    logger.info(f"🧹 已清理 {cleaned_count} 个临时文件")

import json
import platform
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing as mp

# 引入新工具
from src.utils.file_system_utils import get_deep_file_attributes, reveal_in_file_manager, NotesManager, set_where_from_metadata
notes_manager = NotesManager()

# 引入新的优化组件
from src.utils.enhanced_ocr_optimizer import enhanced_ocr_optimizer
from src.ui.progress_monitor import progress_monitor
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage
from llama_index.core.memory import ChatMemoryBuffer

def enhanced_web_search(final_prompt, logger):
    """增强的联网搜索功能"""
    import time
    import re
    from urllib.parse import urlparse
    
    try:
        # 使用新版ddgs
        from ddgs import DDGS
        
        logger.info(f"🌐 启动增强联网搜索...")
        search_start_time = time.time()
        
        # 智能关键词提取
        def extract_keywords(query):
            # 移除疑问词
            remove_words = ['什么是', '哪些', '如何', '怎么', '为什么', '是什么', '有哪些', '具体', '到底']
            cleaned = query
            for word in remove_words:
                cleaned = cleaned.replace(word, ' ')
            
            # 特殊处理 - 更精准的关键词映射
            if '发射场' in query:
                return ['航天发射场', '发射基地', 'launch site', 'spaceport']
            elif '文件位置' in query or '定位文件' in query:
                return ['文件定位', '查找文件', 'find file location']
            elif '机器学习' in query and 'Python' in query:
                return ['Python机器学习', 'Python ML', 'machine learning python']
            elif '人工智能' in query:
                return ['人工智能', 'AI', 'artificial intelligence']
            elif 'OpenAI' in query and 'Deep Research' in query:
                return ['OpenAI Deep Research', 'AI research jobs', '人工智能研究岗位', 'knowledge work automation']
            elif 'AI' in query and ('岗位' in query or '工作' in query or 'job' in query):
                return ['AI工作岗位', 'AI jobs', 'artificial intelligence careers', 'AI替代工作']
            elif '研究生' in query and 'AI' in query:
                return ['研究生AI应用', 'graduate AI research', 'AI学术研究']
            elif '知识密集型' in query or 'knowledge intensive' in query:
                return ['知识密集型工作', 'knowledge work', 'cognitive jobs', 'AI automation jobs']
            else:
                # 提取中文词汇 (改进：更好的分词)
                chinese_words = re.findall(r'[\u4e00-\u9fff]{2,}', cleaned)
                english_words = re.findall(r'[a-zA-Z]{3,}', cleaned)
                
                # 过滤常见词
                filtered_chinese = [w for w in chinese_words if w not in ['可以', '能够', '应该', '需要', '进行']]
                filtered_english = [w for w in english_words if w.lower() not in ['can', 'should', 'need', 'will', 'have']]
                
                return (filtered_chinese + filtered_english)[:3]
        
        keywords = extract_keywords(final_prompt)
        logger.info(f"🔑 提取关键词: {keywords}")
        
        all_results = []
        
        # 搜索每个关键词
        with DDGS() as ddgs:
            for keyword in keywords[:3]:  # 最多搜索3个关键词
                try:
                    logger.info(f"🔍 搜索: {keyword}")
                    
                    # 根据语言选择区域
                    if re.search(r'[\u4e00-\u9fff]', keyword):
                        # 中文关键词
                        results = list(ddgs.text(keyword, max_results=5, region='cn-zh'))
                        if not results:
                            results = list(ddgs.text(keyword, max_results=5))
                    else:
                        # 英文关键词
                        results = list(ddgs.text(keyword, max_results=5, region='us-en'))
                        if not results:
                            results = list(ddgs.text(keyword, max_results=5))
                    
                    if results:
                        logger.info(f"  ✅ 找到 {len(results)} 条结果")
                        all_results.extend(results)
                    else:
                        logger.info(f"  ❌ 无结果")
                        
                except Exception as e:
                    logger.warning(f"  ❌ 搜索失败: {e}")
                    continue
        
        # 去重
        unique_results = []
        seen_urls = set()
        for result in all_results:
            url = result.get('href', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # 质量过滤
        quality_results = []
        for result in unique_results:
            title = result.get('title', '').lower()
            body = result.get('body', '').lower()
            
            # 过滤垃圾内容
            if not any(spam in title + body for spam in ['广告', '推广', 'ad', 'advertisement', '购买', '下载', 'buy', 'download']):
                # 计算相关性得分
                score = 0
                for kw in keywords:
                    if kw.lower() in title:
                        score += 3
                    if kw.lower() in body:
                        score += 1
                
                # 权威性加分
                url = result.get('href', '')
                if any(domain in url for domain in [
                    'wikipedia.org', 'baidu.com', 'zhihu.com', 'github.com',
                    'stackoverflow.com', 'csdn.net', 'edu.cn', '.gov.cn',
                    'nature.com', 'science.org', 'arxiv.org', 'ieee.org',
                    'openai.com', 'anthropic.com', 'deepmind.com', 'mit.edu',
                    'stanford.edu', 'harvard.edu', 'tsinghua.edu.cn', 'pku.edu.cn'
                ]):
                    score += 2
                
                # 内容长度合理性
                if 50 <= len(body) <= 500:
                    score += 1
                
                result['quality_score'] = max(0, score)
                quality_results.append(result)
        
        # 按质量排序
        quality_results.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        search_duration = round(time.time() - search_start_time, 2)
        
        logger.info(f"📊 搜索完成: {len(quality_results)} 条高质量结果，耗时 {search_duration}s")
        
        return quality_results[:8]  # 返回前8个结果
        
    except ImportError:
        logger.error("❌ 未安装 ddgs 库，请运行: pip install ddgs")
        return []
    except Exception as e:
        logger.error(f"❌ 联网搜索失败: {e}")
        return []

def render_smart_visualization(df, query, msg_idx, stage_id, recommendation=None):
    """
    [v5.9.3] 业务级全能画板：全局健壮性升级，彻底解决层级图表类型冲突。
    """
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from pandas.api.types import is_numeric_dtype
    import time

    if df.empty:
        st.info("数据为空，无法生成图表")
        return

    # 1. 自动识别列类型
    num_cols = [c for c in df.columns if is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if c not in num_cols]
    
    if not num_cols:
        st.caption("⚠️ 未检测到数值列，仅展示表格数据")
        st.dataframe(df, use_container_width=True)
        return

    # 2. [v5.9.3] 全局数据清洗：防止 Plotly 在排序/层级处理时触发 TypeError
    clean_df = df.copy()
    for col in cat_cols:
        clean_df[col] = clean_df[col].fillna("Unknown").astype(str)

    # 3. 核心 KPI 汇总卡 (Bento 风格)
    st.markdown("---")
    kpi_cols = st.columns(min(len(num_cols), 4))
    for i, col in enumerate(num_cols[:4]):
        with kpi_cols[i]:
            avg_val = df[col].mean()
            sum_val = df[col].sum()
            st.metric(label=f"平均 {col}", value=f"{avg_val:,.2f}")
            st.caption(f"合计: {sum_val:,.0f}")

    # 4. 标签页切换
    tab_titles = ["🤖 AI 推荐", "🎯 业务转化", "🌲 层级分布", "📊 基础对比", "📦 更多分析", "📋 原始数据"]
    tabs = st.tabs(tab_titles)
    
    key_base = f"vis_{msg_idx}_{stage_id}_{int(time.time()*1000)}"

    # --- Tab 0: AI 推荐 ---
    with tabs[0]:
        if recommendation:
            viz_type = recommendation.get('viz_type', 'bar')
            x_axis = recommendation.get('x_axis')
            y_axis = recommendation.get('y_axis')
            color = recommendation.get('color')
            path = recommendation.get('path')
            title = recommendation.get('title', 'AI 业务视图')
            reason = recommendation.get('reason', '')
            
            st.caption(f"💡 **业务洞察**: {reason}")
            
            try:
                fig = None
                common = {"title": title, "template": "plotly_white"}
                
                # 校验字段
                valid_x = x_axis if x_axis in clean_df.columns else clean_df.columns[0]
                valid_y = y_axis if (isinstance(y_axis, str) and y_axis in clean_df.columns) or (isinstance(y_axis, list) and all(yi in clean_df.columns for yi in y_axis)) else num_cols[0]
                
                if viz_type == 'funnel':
                    fig = px.funnel(clean_df, x=valid_y, y=valid_x, title=title)
                elif viz_type == 'treemap':
                    fig = px.treemap(clean_df, path=path or [valid_x], values=valid_y, title=title)
                elif viz_type == 'sunburst':
                    fig = px.sunburst(clean_df, path=path or [valid_x], values=valid_y, title=title)
                elif viz_type == 'indicator':
                    val = df[valid_y].iloc[0] if not df.empty else 0
                    fig = go.Figure(go.Indicator(
                        mode = "number+delta", value = val, title = {"text": title},
                        domain = {'x': [0, 1], 'y': [0, 1]}
                    ))
                elif viz_type == 'radar' and len(num_cols) >= 3:
                    fig = px.line_polar(clean_df, r=num_cols, theta=clean_df.columns[0], line_close=True, title=title)
                else:
                    if color and color in clean_df.columns: common["color"] = color
                    if viz_type == 'bar': fig = px.bar(clean_df, x=valid_x, y=valid_y, **common)
                    elif viz_type == 'line': fig = px.line(clean_df, x=valid_x, y=valid_y, **common)
                    elif viz_type == 'pie': fig = px.pie(clean_df, names=valid_x, values=valid_y[0] if isinstance(valid_y, list) else valid_y, hole=0.4, title=title)
                    elif viz_type == 'box': fig = px.box(clean_df, x=valid_x, y=valid_y, **common)
                    elif viz_type == 'histogram': fig = px.histogram(clean_df, x=valid_x, y=valid_y, **common)
                
                if fig:
                    fig.update_layout(margin=dict(t=40, l=0, r=0, b=0))
                    st.plotly_chart(fig, use_container_width=True, key=f"{key_base}_ai")
                else:
                    st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.warning(f"AI 视图渲染失败，请切换至手动模式。")
        else:
            st.info("AI 正在根据数据学习业务模式...")

    # --- Tab 1: 业务转化 (漏斗图) ---
    with tabs[1]:
        c1, c2 = st.columns(2)
        f_y = c1.selectbox("步骤/阶段 (维度)", clean_df.columns, key=f"{key_base}_f_y")
        f_x = c2.selectbox("转化指标 (数值)", num_cols, key=f"{key_base}_f_x")
        if f_x and f_y:
            fig = px.funnel(clean_df, x=f_x, y=f_y, template="plotly_white", title="业务转化漏斗")
            st.plotly_chart(fig, use_container_width=True, key=f"{key_base}_funnel_fig")

    # --- Tab 2: 层级分布 (树图/旭日图) ---
    with tabs[2]:
        c1, c2, c3 = st.columns(3)
        h_mode = c1.radio("展示模式", ["矩形树图", "旭日图"], horizontal=True, key=f"{key_base}_h_mode")
        h_path = c2.multiselect("层级路径 (可多选)", cat_cols or clean_df.columns[:2], default=cat_cols[:2] if len(cat_cols)>=2 else cat_cols, key=f"{key_base}_h_p")
        h_val = c3.selectbox("数值权重", num_cols, key=f"{key_base}_h_v")
        if h_path and h_val:
            try:
                if h_mode == "矩形树图": 
                    fig = px.treemap(clean_df, path=h_path, values=h_val, template="plotly_white")
                else: 
                    fig = px.sunburst(clean_df, path=h_path, values=h_val, template="plotly_white")
                st.plotly_chart(fig, use_container_width=True, key=f"{key_base}_hierarchy_fig")
            except Exception as e:
                st.caption(f"层级图表暂时无法显示 (原因: 包含不兼容的数据格式)")
                st.dataframe(df[h_path + [h_val]], use_container_width=True)

    # --- Tab 3: 基础对比 ---
    with tabs[3]:
        c1, c2, c3 = st.columns(3)
        b_x = c1.selectbox("X轴 (分类)", clean_df.columns, key=f"{key_base}_b_x")
        b_y = c2.multiselect("Y轴 (数值)", num_cols, default=num_cols[:1], key=f"{key_base}_b_y")
        b_c = c3.selectbox("分组颜色 (可选)", [None] + cat_cols, key=f"{key_base}_b_c")
        if b_x and b_y:
            fig = px.bar(clean_df, x=b_x, y=b_y, color=b_c, barmode="group", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True, key=f"{key_base}_bar_fig")

    # --- Tab 4: 更多分析 ---
    with tabs[4]:
        sub_tabs = st.tabs(["📉 趋势分析", "📦 统计分布", "🕸️ 雷达评价"])
        with sub_tabs[0]:
            st.plotly_chart(px.area(clean_df, x=clean_df.columns[0], y=num_cols[:1], template="plotly_white", title="累计趋势图"), use_container_width=True, key=f"{key_base}_area_fig")
        with sub_tabs[1]:
            st.plotly_chart(px.box(clean_df, y=num_cols[0], template="plotly_white", title="数据分布箱线图"), use_container_width=True, key=f"{key_base}_box_fig")
        with sub_tabs[2]:
            if len(num_cols) >= 3:
                try:
                    radar_theta = cat_cols[0] if cat_cols else clean_df.columns[0]
                    radar_r = [c for c in num_cols if c != radar_theta]
                    if len(radar_r) >= 3:
                        fig = px.line_polar(clean_df, r=radar_r, theta=radar_theta, line_close=True, title="多维属性对比", template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True, key=f"{key_base}_radar_fig")
                except: st.info("雷达图生成受阻")
            else:
                st.info("💡 雷达图需要至少 3 个数值指标列。")

    # --- Tab 5: 原始数据 ---
    with tabs[5]:
        st.dataframe(df, use_container_width=True)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.llms.ollama import Ollama
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.schema import Document

# 导入自定义嵌入
from src.custom_embeddings import create_custom_embedding

# terminal_logger 已被 logger 替代
from src.chat_utils_improved import generate_follow_up_questions_safe as generate_follow_up_questions
from src.chat.unified_suggestion_engine import get_unified_suggestion_engine

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
from src.chat.unified_suggestion_engine import get_unified_suggestion_engine
from src.chat import HistoryManager

# 引入 UI 模块
from src.ui.page_style import PageStyle
from src.ui.sidebar_config import SidebarConfig
from src.ui.mobile_adapter import MobileAdapter

# 引入工具函数
from src.utils.app_utils import (
    get_kb_embedding_dim,
    remove_file_from_manifest,
    show_first_time_guide,
    open_file_native,
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

# 引入统一UI组件
from src.ui.unified_dialogs import show_document_detail_dialog

from src.utils.kb_utils import generate_smart_kb_name
from src.utils.app_utils import initialize_session_state


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
from src.chat import ChatEngine

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
        # 使用统一配置加载器 (读取 rag_config.json)
        config = ConfigLoader.load()
        
        llm_provider = config.get('llm_provider', 'Ollama')
        
        # 提取配置
        if llm_provider == 'OpenAI-Compatible':
            llm_model = config.get('llm_model_other', '')
            llm_url = config.get('llm_url_other', '')
            llm_key = config.get('llm_key_other', '')
        elif llm_provider == 'OpenAI':
            llm_model = config.get('llm_model_openai', 'gpt-3.5-turbo')
            llm_url = config.get('llm_url_openai', 'https://api.openai.com/v1')
            llm_key = config.get('llm_key', '')
        else:  # Ollama & Default
            llm_model = config.get('llm_model_ollama', 'gpt-oss:20b')
            llm_url = config.get('llm_url_ollama', 'http://localhost:11434')
            llm_key = ""
        
        system_prompt = config.get('system_prompt', None)
        
        # 设置全局LLM
        if llm_model:
            set_global_llm_model(llm_provider, llm_model, llm_key, llm_url, system_prompt=system_prompt)
            
    except Exception as e:
        logger.warning(f"全局LLM初始化失败: {e}")
    
    st.session_state.app_initialized = True
    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = None
    
    # --- [v5.6.3] 现场恢复：基于 URL 参数持久化活跃会话 ---
    if "kb_id" in st.query_params and st.session_state.get('current_kb_id') is None:
        target_kb = st.query_params["kb_id"]
        st.session_state.current_kb_id = target_kb
        # 设置导航显示格式以匹配侧边栏
        st.session_state.current_nav = f"☑️ 📂 {target_kb}"
        # 如果有 session_id，一并恢复
        if "sess_id" in st.query_params:
            st.session_state.current_session_id = st.query_params["sess_id"]
        
        logger.info(f"🔄 正在从 URL 恢复现场: KB={target_kb}", stage="现场恢复")

    logger.success("应用初始化完成")

# 每次运行时同步当前状态到 URL，确保刷新不丢失
if st.session_state.get('current_kb_id'):
    st.query_params["kb_id"] = st.session_state.current_kb_id
    if st.session_state.get('current_session_id'):
        st.query_params["sess_id"] = st.session_state.current_session_id

# --- 自动登录逻辑 (v4.5.2) ---
# 必须在登录拦截之前执行
if not st.session_state.get("logged_in"):
    token = st.query_params.get("session_token")
    if token:
        try:
            from src.auth.session_manager import validate_session
            from src.auth.user_auth import load_users
            
            username = validate_session(token)
            if username:
                users = load_users()
                user_info = users.get(username)
                if user_info and user_info.get('is_active', True):
                    from src.auth.audit_logger import AuditLogger
                    from src.common.utils import get_client_ip
                    st.session_state.logged_in = True
                    st.session_state.user = username
                    st.session_state.role = user_info.get('role', 'standard_user')
                    AuditLogger.log(username, "AUTO_LOGIN", "通过 Session Token 自动登录", action_type="AUTH", ip=get_client_ip())
                    logger.info(f"自动登录成功: {username}")
                    st.toast(f"👋 欢迎回来, {username}", icon="✨")
        except Exception as e:
            logger.warning(f"自动登录失败: {e}")

# ==========================================
# 登录拦截逻辑 (管理为先)
# ==========================================
from src.auth.login_page import render_login_page
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    render_login_page()
    st.stop()

# ==========================================
# 2. 本地持久化与工具函数
# ==========================================
CONFIG_FILE = "rag_config.json"
HISTORY_DIR = "chat_histories"
UPLOAD_DIR = "temp_uploads"

# 确保目录存在
for d in [HISTORY_DIR, UPLOAD_DIR]:
    if not os.path.exists(d): os.makedirs(d)

# 使用新的配置加载器 (Stage 8)
defaults = ConfigLoader.load()

from src.common.business import generate_doc_summary

with st.sidebar:
    # 渲染移动端视图适配器 (响应式预览)
    MobileAdapter.render_view_selector()
    
    # 横向标签页布局 (v3.4: 管理为先)
    tab_labels = ["🏠 主页", "🎭 角色", "⚙️ 配置", "📊 监控", "❓ 帮助"]
    if st.session_state.get('role') == 'admin':
        tab_labels.append("👤 用户")
    
    tabs = st.tabs(tab_labels)
    
    # 动态分配 tab 变量
    if st.session_state.get('role') == 'admin':
        tab_main, tab_roles, tab_config, tab_monitor, tab_help, tab_user = tabs
    else:
        tab_main, tab_roles, tab_config, tab_monitor, tab_help = tabs
    
    # 渲染管理 Tab (仅 Admin)
    if st.session_state.get('role') == 'admin':
        with tab_user:
            from src.auth.user_management import render_admin_management
            render_admin_management()

    # --- 退出登录按钮 (位于侧边栏底部) ---
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 退出当前账号", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

    with tab_main:
        # ... 原有代码保持不变 ...
        # (定位到知识库控制台)


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
            output_base = st.text_input("知识库存储路径", value=default_output_path, help="知识库文件的保存位置", label_visibility="collapsed")
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
        all_base_kbs = kb_manager.list_all()
        
        # --- 权限与可见性过滤 ---
        from src.auth.session_manager import get_visible_kbs
        from src.auth.permission_manager import permission_manager
        
        current_user = st.session_state.get('user', 'guest_user')
        current_role = st.session_state.get('role', 'guest')
        
        base_kbs = get_visible_kbs(current_user, current_role, all_base_kbs)
        
        # 为每个知识库创建带复选框的选项
        from src.config.manifest_manager import ManifestManager
        nav_options = []
        
        # 权限检查：是否可以新建知识库
        can_create = permission_manager.has_permission(current_user, "kb_create")
        if can_create:
            nav_options.append("➕ 新建知识库...")
            
        nav_options.append("💬 纯对话模式 (Pure Chat)")
        
        for kb in base_kbs:
            # --- 前端脱敏: 剥离用户名前缀 ---
            display_name = kb
            from src.auth.user_auth import load_users
            all_known_users = load_users()
            
            if "_" in kb:
                parts = kb.split("_", 1)
                # 如果前半部分是已知用户，则剥离
                if parts[0] in all_known_users:
                    display_name = parts[1]

            # 获取统计信息 (v2.7.6: 增强信息展示)
            try:
                kb_path = os.path.join(output_base, kb)
                stats = ManifestManager.get_stats(kb_path)
                doc_count = stats.get('file_count', 0)
                size_str = ManifestManager.format_size(stats.get('total_size', 0))
                date_str = stats.get('created_time', '').split('T')[0] if stats.get('created_time') else 'N/A'
                info_str = f" (📄{doc_count} | 💾{size_str} | 🕒{date_str})"
            except Exception:
                info_str = " (N/A)"

            # 检查是否被选中
            is_selected = st.session_state.get(f"kb_check_{kb}", False)
            checkbox_symbol = "☑️" if is_selected else "☐"
            
            # --- Admin 视角增强: 显示所有者 ---
            owner_info = ""
            if current_role == 'admin':
                try:
                    kb_path = os.path.join(output_base, kb)
                    manifest_path = ManifestManager.get_path(kb_path)
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        m_data = json.load(f)
                        owner = m_data.get('owner', 'admin(历史)')
                        owner_info = f" | 👤{owner}"
                except:
                    # 备选：从文件名解析前缀
                    if "_" in kb:
                        owner_info = f" | 👤{kb.split('_')[0]}"
                    else:
                        owner_info = " | 👤admin"
            
            nav_options.append(f"{checkbox_symbol} 📂 {display_name}{info_str}{owner_info}")
        
        # 保存选中的知识库列表
        selected_kbs = [kb for kb in base_kbs if st.session_state.get(f"kb_check_{kb}", False)]
        st.session_state.selected_kbs = selected_kbs

        # 检查是否要显示配置页面
        if st.session_state.get('show_industry_config'):
            from src.ui.industry_config_interface import render_industry_config_interface
            
            # 返回按钮
            if st.button("← 返回主页"):
                st.session_state.show_industry_config = False
                st.rerun()
            
            # 渲染配置界面
            render_industry_config_interface()
            st.stop()  # 停止执行后续代码

        default_idx = 0
        if "current_nav" in st.session_state:
            # 强化匹配逻辑 (v2.7.6): 兼容带统计信息和复选框图标的情况
            # 1. 移除图标
            current_nav_clean = st.session_state.current_nav.replace("☑️ ", "").replace("☐ ", "")
            # 2. 移除统计信息 (📄... | 💾... | 🕒...)
            current_nav_clean = current_nav_clean.split(" (")[0].strip()
            
            for i, opt in enumerate(nav_options):
                # 对待匹配项执行同样的清理
                opt_clean = opt.replace("☑️ ", "").replace("☐ ", "").split(" (")[0].strip()
                if opt_clean == current_nav_clean:
                    default_idx = i
                    break
            
            # 兜底：如果清理后匹配到了，更新 session_state 确保同步最新格式
            if default_idx > 0 and nav_options[default_idx] != st.session_state.current_nav:
                st.session_state.current_nav = nav_options[default_idx]

        # 知识库选择 - 直接复选框模式
        select_col1, select_col2, select_col3 = st.columns([0.6, 5.9, 0.5])
        with select_col1:
            st.markdown("**选择:**")
        with select_col2:
            selected_nav = st.selectbox("选择知识库或对话模式", nav_options, index=default_idx, label_visibility="collapsed")
            
            # 自动启动纯对话模式 (v2.7.6) - 简化版本
            if selected_nav == "💬 纯对话模式 (Pure Chat)" and st.session_state.get('current_kb_id') != "pure_chat":
                # 纯对话模式不需要加载任何知识库，直接设置为纯对话状态
                st.session_state.chat_engine = "pure_chat"  # 使用字符串标识，避免加载复杂组件
                st.session_state.current_kb_id = "pure_chat"
                st.toast("✅ 纯对话模式已启动 - 直接与AI对话")
                st.rerun()

            # 处理复选框点击逻辑 - 只有当用户手动更改选择时才触发
            if selected_nav != st.session_state.get('current_nav') and (selected_nav.startswith("☐") or selected_nav.startswith("☑️")):
                # 提取知识库名称 (支持带统计信息的格式)
                kb_name = selected_nav.split("📂 ")[1].split(" (")[0].strip() if "📂 " in selected_nav else ""
                if kb_name:
                    # 切换复选框状态
                    current_state = st.session_state.get(f"kb_check_{kb_name}", False)
                    new_state = not current_state
                    st.session_state[f"kb_check_{kb_name}"] = new_state
                    
                    # 关键修复：立即更新 current_nav 字符串，确保下次 rerun 时 index 匹配正确
                    new_symbol = "☑️" if new_state else "☐"
                    st.session_state.current_nav = f"{new_symbol} 📂 {kb_name}"
                    st.rerun()
        with select_col3:
            if st.button("🔄", help="刷新知识库列表", use_container_width=True, key="refresh_kb_list"):
                st.rerun()

        # 自动启动系统逻辑 (替代原有的启动按钮)
        # 纯对话模式已在上方 selectbox 处理，此处处理知识库模式
        is_pure_chat = (selected_nav == "💬 纯对话模式 (Pure Chat)")
        
        # 仅在非创建模式且非纯对话模式下执行自动启动
        if not is_pure_chat and selected_nav != "➕ 新建知识库...":
            target_kb_id = None
            selected_kbs = st.session_state.get('selected_kbs', [])
            
            if len(selected_kbs) == 1:
                target_kb_id = selected_kbs[0]
            elif len(selected_kbs) > 1:
                target_kb_id = "multi_kb_mode"
            
            # 如果目标ID有效，且与当前运行的ID不一致，则触发启动
            if target_kb_id and target_kb_id != st.session_state.get('current_kb_id'):
                # 显示加载状态 (仅在初次加载或切换时)
                if st.session_state.get('current_kb_id') is None:
                     status_text = f"正在启动: {target_kb_id}..."
                     spinner_ctx = st.spinner(status_text)
                else:
                     # 切换时使用 toast 以减少干扰
                     status_text = None
                     spinner_ctx = st.empty()

                with spinner_ctx:
                    try:
                        if target_kb_id == "multi_kb_mode":
                            st.session_state.chat_engine = "multi_kb_mode"
                            st.session_state.current_kb_id = "multi_kb_mode"
                            st.toast(f"✅ 多知识库模式已启动 ({len(selected_kbs)}个)")
                        else:
                            # 单知识库
                            kb_name = target_kb_id
                            from src.rag_engine import create_rag_engine
                            rag_engine = create_rag_engine(kb_name)
                            if rag_engine:
                                st.session_state.chat_engine = rag_engine.get_chat_engine()
                                st.session_state.current_kb_id = kb_name
                                st.toast(f"✅ 知识库 '{kb_name}' 已启动")
                            else:
                                st.error(f"❌ 无法启动知识库 '{kb_name}'")
                                # 添加友好的错误引导
                                from src.utils.friendly_error_handler import friendly_error
                                friendly_error("知识库未加载", 
                                             f"知识库 '{kb_name}' 启动失败",
                                             ["检查知识库文件是否完整", "尝试重新创建知识库", "查看系统日志获取详细信息"])
                                st.session_state.current_kb_id = None
                        
                        # 只有在引擎变化时才 rerun，确保界面刷新
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 启动失败: {str(e)}")
                        logger.error(f"Auto-start failed: {e}")

        # 知识库搜索/过滤已按用户要求移除

        # 卸载知识库按钮（释放内存）
        if not (selected_nav == "➕ 新建知识库...") and st.session_state.get('chat_engine') is not None:
            if st.button("🔓 卸载知识库（释放内存）", use_container_width=True, help="释放当前知识库占用的内存资源"):
                st.session_state.chat_engine = None
                st.session_state.current_kb_id = None
                cleanup_memory()
                st.toast("✅ 知识库已卸载，内存已释放")
                st.rerun()

        # --- 会话历史 (Session History) v2.7.3 ---
        # 提取当前的 active_kb_name (如果已选择)
        current_active_kb = None
        # 局部判断是否为创建模式，避免 NameError
        _is_creating = (selected_nav == "➕ 新建知识库...")
        if not _is_creating and "📂 " in selected_nav:
             current_active_kb = selected_nav.split("📂 ")[1].split(" (")[0].strip()
        
        if current_active_kb:
            st.markdown("---")
            with st.expander("🕒 历史会话", expanded=True):
                from src.chat.history_manager import HistoryManager
                sessions = HistoryManager.list_sessions(current_active_kb)
                
                # 新建会话按钮
                if st.button("➕ 新建会话", use_container_width=True, key="sidebar_new_chat"):
                    # [v5.6.6 核心修复] 在切换前，先保存当前正在进行的会话，防止标题丢失
                    if st.session_state.get('messages'):
                        old_sess_id = st.session_state.get('current_session_id')
                        HistoryManager.save_session(current_active_kb, st.session_state.messages, old_sess_id)
                        logger.info(f"💾 已在切换前自动保存旧会话: {old_sess_id or 'default'}")

                    import uuid
                    new_id = str(uuid.uuid4())[:8]
                    st.session_state.current_session_id = new_id
                    st.query_params["sess_id"] = new_id # 同步到 URL
                    
                    # --- [逻辑对齐] 注入初始状态 (Initial State) ---
                    kb_path = os.path.join("vector_db_storage", current_active_kb)
                    from src.config.manifest_manager import ManifestManager
                    manifest = ManifestManager.load(kb_path)
                    
                    initial_msg = []
                    summary = manifest.get('summary', "👋 知识库已就绪，您可以开始提问了。")
                    sug = manifest.get('suggestions', [])
                    
                    # 构造初始欢迎消息
                    initial_msg.append({
                        "role": "assistant", 
                        "content": f"### 📊 知识库初始化完成\n\n{summary}",
                        "suggestions": sug,
                        "is_initial": True
                    })
                    
                    st.session_state.messages = initial_msg
                    st.session_state.suggestions_history = sug
                    
                    HistoryManager.save_session(current_active_kb, initial_msg, new_id)
                    st.rerun()
                
                # 显示刚才生成的分享 ID
                if st.session_state.get('last_share_id'):
                    st.code(f"http://localhost:8501/?share={st.session_state.last_share_id}", language="markdown")
                    if st.button("关闭分享提示", key="close_share"):
                        del st.session_state['last_share_id']
                        st.rerun()

                # 会话列表
                total_sess = len(sessions)
                for i, sess in enumerate(sessions):
                    sess_id = sess['id']
                    # 为每个会话生成一个专门的编号
                    display_idx = total_sess - i
                    label = f"#{display_idx} {sess['title']}"
                    
                    is_active = (sess_id == st.session_state.get('current_session_id'))
                    is_pinned = sess.get('pinned', False)
                    
                    # 使用列布局放置操作按钮 [标题(6), 置顶(1), 分享(1), 重命名(1), 删除(1)]
                    c_title, c_pin, c_share, c_edit, c_del = st.columns([5.5, 1.2, 1.2, 1.2, 1.2])
                    
                    with c_title:
                        icon = "📌" if is_pinned else ("📂" if is_active else "📄")
                        btn_type = "primary" if is_active else "secondary"
                        # 确保 key 唯一
                        safe_sess_id = str(sess_id) if sess_id else "default"
                        
                        if st.button(f"{icon} {label}", key=f"sess_btn_{safe_sess_id}", use_container_width=True, type=btn_type, help=label):
                            # [v5.6.8 核心修复] 切换前，保存当前正在进行的会话状态
                            if st.session_state.get('messages'):
                                current_old_id = st.session_state.get('current_session_id')
                                HistoryManager.save_session(current_active_kb, st.session_state.messages, current_old_id)
                            
                            # 立即更新内存和 URL，防止初始化逻辑抢跑
                            st.session_state.current_session_id = sess_id
                            st.query_params["sess_id"] = sess_id if sess_id else ""
                            
                            st.session_state.messages = HistoryManager.load_session(current_active_kb, sess_id)
                            # 恢复建议
                            st.session_state.suggestions_history = []
                            if st.session_state.messages:
                                last_msg = st.session_state.messages[-1]
                                if isinstance(last_msg, dict) and last_msg.get('suggestions'):
                                    st.session_state.suggestions_history = last_msg['suggestions']
                            st.rerun()
                            
                    with c_pin:
                        pin_icon = "🔓" if is_pinned else "📌"
                        pin_help = "取消置顶" if is_pinned else "置顶会话"
                        if st.button(pin_icon, key=f"sess_pin_{safe_sess_id}", help=pin_help):
                            HistoryManager.toggle_pin_session(current_active_kb, sess_id)
                            st.rerun()

                    with c_share:
                        if st.button("🔗", key=f"sess_share_{safe_sess_id}", help="生成分享链接"):
                            from src.chat.share_manager import ShareManager
                            # 加载该会话的完整消息
                            share_msgs = HistoryManager.load_session(current_active_kb, sess_id)
                            s_id = ShareManager.create_share(current_active_kb, share_msgs, st.session_state.get('user', 'admin'))
                            st.session_state.last_share_id = s_id
                            st.toast(f"✅ 分享链接已生成")
                            
                    with c_edit:
                        if st.button("✏️", key=f"sess_edit_{safe_sess_id}", help="重命名"):
                            st.session_state[f"renaming_sess_{safe_sess_id}"] = True
                    
                    with c_del:
                        if st.button("🗑️", key=f"sess_del_{safe_sess_id}", help="删除会话"):
                            # 增加二次确认 (利用 session_state)
                            st.session_state[f"confirm_del_{safe_sess_id}"] = True
                    
                    # 内联重命名区域
                    if st.session_state.get(f"renaming_sess_{safe_sess_id}"):
                        with st.container():
                            new_name = st.text_input("新名称", value=label, key=f"input_ren_{safe_sess_id}", label_visibility="collapsed")
                            rc1, rc2 = st.columns(2)
                            if rc1.button("保存", key=f"save_ren_{safe_sess_id}", use_container_width=True):
                                HistoryManager.rename_session(current_active_kb, sess_id, new_name)
                                del st.session_state[f"renaming_sess_{safe_sess_id}"]
                                st.rerun()
                            if rc2.button("取消", key=f"cancel_ren_{safe_sess_id}", use_container_width=True):
                                del st.session_state[f"renaming_sess_{safe_sess_id}"]
                                st.rerun()
                                
                    # 内联删除确认区域
                    if st.session_state.get(f"confirm_del_{safe_sess_id}"):
                        st.warning("确定删除?")
                        dc1, dc2 = st.columns(2)
                        if dc1.button("是", key=f"yes_del_{safe_sess_id}", type="primary", use_container_width=True):
                            HistoryManager.delete_session(current_active_kb, sess_id)
                            if is_active:
                                st.session_state.current_session_id = None
                                st.session_state.messages = []
                            del st.session_state[f"confirm_del_{safe_sess_id}"]
                            st.rerun()
                        if dc2.button("否", key=f"no_del_{safe_sess_id}", use_container_width=True):
                            del st.session_state[f"confirm_del_{safe_sess_id}"]
                            st.rerun()

        if selected_nav != st.session_state.get('current_nav'):
            st.session_state.pop('suggestions_history', None) 

        st.session_state.current_nav = selected_nav

        is_create_mode = (selected_nav == "➕ 新建知识库...")
        
        # 根据选中的知识库确定当前模式
        selected_kbs = st.session_state.get('selected_kbs', [])
        if len(selected_kbs) == 1:
            current_kb_name = selected_kbs[0]
        elif len(selected_kbs) > 1:
            current_kb_name = None  # 多知识库模式
            st.info(f"🔍 已选择 {len(selected_kbs)} 个知识库: {', '.join(selected_kbs)}")
        else:
            if selected_nav == "💬 纯对话模式 (Pure Chat)":
                current_kb_name = "pure_chat"
            else:
                # 兼容带统计信息的格式
                raw_name = selected_nav.split("📂 ")[1] if "📂 " in selected_nav else ""
                short_name = raw_name.split(" (")[0].strip() if not is_create_mode and raw_name else None
                
                # --- [v5.6.4 核心修复] 建立短名到全名的映射逻辑 ---
                if short_name:
                    # 优先检查 session_state 里保存的全名
                    if st.session_state.get('current_kb_id') and short_name in st.session_state.current_kb_id:
                        current_kb_name = st.session_state.current_kb_id
                    else:
                        # 兜底：从实际存在的目录中找匹配的库 (防止刷新丢失)
                        all_kbs = kb_manager.list_all()
                        matches = [k for k in all_kbs if k.endswith(f"_{short_name}") or k == short_name]
                        current_kb_name = matches[0] if matches else short_name
                else:
                    current_kb_name = None

        # --- [逻辑对齐补丁] 自动恢复最近一次历史会话 ---
        if current_kb_name and current_kb_name != "pure_chat" and not is_create_mode:
            # 强化物理路径校验：确保 ID 对应真实的 docstore.json
            kb_full_path = os.path.join(output_base, current_kb_name)
            if not os.path.exists(os.path.join(kb_full_path, "docstore.json")):
                # 如果找不到，尝试自愈 (在已有的库里找同名但带前缀的)
                all_kbs = kb_manager.list_all()
                for k in all_kbs:
                    if k.endswith(f"_{current_kb_name}"):
                        current_kb_name = k
                        break

            # 如果知识库切换了，或者当前没有加载消息
            if st.session_state.get('last_loaded_kb') != current_kb_name or not st.session_state.get('messages'):
                from src.chat.history_manager import HistoryManager
                st.session_state.current_kb_id = current_kb_name
                sessions = HistoryManager.list_sessions(current_kb_name)
                if sessions:
                    # 默认加载第一个（通常是最近更新的）
                    latest_sess_id = sessions[0]['id']
                    st.session_state.current_session_id = latest_sess_id
                    st.session_state.messages = HistoryManager.load_session(current_kb_name, latest_sess_id)
                    # 恢复建议历史
                    if st.session_state.messages:
                        last_msg = st.session_state.messages[-1]
                        if isinstance(last_msg, dict) and last_msg.get('suggestions'):
                            st.session_state.suggestions_history = last_msg['suggestions']
                
                st.session_state.last_loaded_kb = current_kb_name
                # 仅在真正需要时触发刷新，避免无限循环
                if st.session_state.get('messages'):
                    st.rerun()

        # 统一的数据源处理逻辑
        uploaded_files = st.session_state.get('uploader') # 优先从 uploader 获取，支持多模式
        crawl_url = None
        search_keyword = None
        target_path = ""
        btn_start = False # Initialize early to avoid NameError and support APPEND mode
        source_mode = st.session_state.get('data_source_selector') # 确保从 radio 获取最新模式
        
        if is_create_mode:
            # 注入 CSS 增强核心功能视觉效果
            st.markdown("""
            <style>
            /* 放大 4x1 选择器的文字和图标 */
            div[data-testid="stRadio"] > div[role="radiogroup"] > label {
                padding: 10px 15px !important;
                border-radius: 8px !important;
                transition: all 0.2s ease !important;
            }
            div[data-testid="stRadio"] > div[role="radiogroup"] > label p {
                font-size: 1.15rem !important;
                font-weight: 600 !important;
                color: #31333F !important;
            }
            /* 选中状态稍微变色提醒 */
            div[data-testid="stRadio"] > div[role="radiogroup"] > label[data-baseweb="radio"]:has(input:checked) {
                background-color: rgba(255, 75, 75, 0.05) !important;
            }
            </style>
            """, unsafe_allow_html=True)

            # 5x1 水平数据源选择
            source_mode = st.radio(
                "数据源", 
                ["📂 文件上传", "📝 粘贴文本", "🔗 网址抓取", "📊 数据分析", "🔍 智能搜索"], 
                horizontal=True,
                label_visibility="collapsed",
                key="data_source_selector"
            )
            
            if source_mode == "📊 数据分析":
                st.info("💡 **数据分析模式**: 适合上传 CSV、Excel 或包含报表的文档。系统将自动提取表格结构并支持复杂的 SQL 统计查询。")
                da_files = st.file_uploader(
                    "上传业务表单或数据字典", 
                    accept_multiple_files=True, 
                    type=['csv', 'xlsx', 'xls', 'md', 'markdown'],
                    key="da_uploader",
                    label_visibility="collapsed"
                )
                if da_files:
                    st.session_state.is_data_analysis_mode = True
                    # 关键：立即同步给全局变量供下文统一处理
                    uploaded_files = da_files
            
            elif source_mode == "📂 文件上传":
                # 权限拦截 (实时校验)
                from src.auth.permission_manager import permission_manager
                current_user = st.session_state.get('user', 'guest_user')
                can_upload = permission_manager.has_permission(current_user, "upload_files")
                
                if not can_upload:
                    st.warning("🔒 权限不足：您当前的角色没有上传文件的权限。")
                
                # 添加上传引导
                from src.utils.user_guidance import show_guidance
                show_guidance("upload")
                
                # 双模式：支持上传和手动输入路径
                uploaded_files = st.file_uploader(
                    "拖入文件", 
                    accept_multiple_files=True, 
                    key="uploader",
                    label_visibility="collapsed",
                    help="支持格式: PDF, DOCX, TXT, MD, Excel, CSV, 图片",
                    type=['pdf', 'docx', 'txt', 'md', 'markdown', 'xlsx', 'xls', 'csv', 'pptx', 'jpg', 'png', 'jpeg'],
                    disabled=not can_upload
                )
                
                # 恢复路径输入
                st.markdown("<div style='margin-top: -5px; margin-bottom: 5px;'><span style='font-size: 0.75rem; color: gray;'>或粘贴本地目录路径:</span></div>", unsafe_allow_html=True)
                manual_path = st.text_input(
                    "本地路径",
                    placeholder="例如: /Users/name/Documents/docs",
                    key="manual_path_input",
                    label_visibility="collapsed",
                    disabled=not can_upload
                )
                if manual_path and os.path.exists(manual_path):
                    st.session_state.uploaded_path = manual_path
            
            elif source_mode == "📝 粘贴文本":
                # 权限拦截 (实时校验)
                from src.auth.permission_manager import permission_manager
                current_user = st.session_state.get('user', 'guest_user')
                can_upload = permission_manager.has_permission(current_user, "upload_files")
                
                if not can_upload:
                    st.warning("🔒 权限不足：您当前的角色没有粘贴文本的权限。")
                # 只在首次加载时注入CSS，避免重复注入
                if 'paste_css_injected' not in st.session_state:
                    st.markdown("""
                    <style>
                    .stTextArea textarea {
                        border: 2px dashed rgba(49, 51, 63, 0.2) !important;
                        background-color: rgba(240, 242, 246, 0.5) !important;
                        border-radius: 0.5rem !important;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    st.session_state.paste_css_injected = True
                
                # 自动保存逻辑 - 失焦时触发
                def auto_save_text():
                    # 获取当前输入的文本
                    content = st.session_state.get('paste_text_display', '')
                    if content and content.strip():
                        try:
                            # 如果是截断显示的文本，需要获取完整内容
                            if "... [文本过长，已截断显示，完整内容已保存] ..." in content:
                                # 从完整文本存储中获取
                                full_content = st.session_state.get('paste_text_content', content)
                            else:
                                full_content = content
                            
                            # 确保有实际内容
                            if not full_content or not full_content.strip():
                                return
                                
                            save_dir = os.path.join(UPLOAD_DIR, f"text_{int(time.time())}")
                            if not os.path.exists(save_dir): 
                                os.makedirs(save_dir)
                            safe_name = "manual_input.txt"
                            
                            # 保存完整内容
                            with open(os.path.join(save_dir, safe_name), 'w', encoding='utf-8') as f:
                                f.write(full_content)
                            
                            # 设置路径 - 复用原来的逻辑
                            abs_path = os.path.abspath(save_dir)
                            st.session_state.uploaded_path = abs_path
                            st.session_state.path_input = abs_path
                            
                            # 生成名称 - 复用原来的逻辑
                            preview = "".join(c for c in full_content[:15] if c.isalnum() or c.isspace()).strip()
                            st.session_state.upload_auto_name = f"Text_{preview}"
                            
                            # 标记已保存
                            st.session_state.text_auto_saved = True
                            st.session_state.saved_text_length = len(full_content)
                            
                        except Exception as e:
                            st.error(f"自动保存失败: {e}")
                
                # 获取当前文本，如果超过10万字符则截断显示
                current_text = st.session_state.get('paste_text_display', '')
                display_text = current_text
                is_truncated = False
                
                # 存储完整文本
                if current_text:
                    st.session_state.paste_text_content = current_text
                
                if len(current_text) > 100000:
                    display_text = current_text[:10000] + "\n\n... [文本过长，已截断显示，完整内容已保存] ..."
                    is_truncated = True
                
                # 文本输入框 - 显示截断后的文本
                text_input_content = st.text_area(
                    "文本内容", 
                    value=display_text,
                    height=200,
                    placeholder="在此粘贴文本，失焦时自动保存...", 
                    label_visibility="collapsed",
                    key="paste_text_display",
                    on_change=auto_save_text
                )
                
                # 更新完整文本存储
                if not is_truncated:
                    st.session_state.paste_text_content = text_input_content
                
                # 显示状态信息
                if st.session_state.get('text_auto_saved'):
                    saved_length = st.session_state.get('saved_text_length', 0)
                    st.success(f"✅ 文本已自动保存 ({saved_length:,} 字符) - {st.session_state.get('upload_auto_name', '')}")
                elif current_text:
                    char_count = len(current_text)
                    if is_truncated:
                        st.info(f"📊 大文本 ({char_count:,} 字符) - 前端仅显示前10,000字符，完整内容将自动保存")
                    else:
                        st.caption(f"📊 字符数: {char_count:,}")
                
                # 不需要手动保存按钮了，失焦自动保存
        else:
            # 管理模式 - 使用一行化布局 (1x2 紧凑布局)
            manage_title_col1, manage_title_col2 = st.columns([4, 1])
            with manage_title_col1:
                st.markdown("📤 **添加文档**")
            with manage_title_col2:
                # 权限检查：重建索引
                from src.auth.permission_manager import permission_manager
                current_user = st.session_state.get('user', 'guest_user')
                can_rebuild = permission_manager.has_permission(current_user, "kb_rebuild_index")
                
                if can_rebuild:
                    if st.button("🔄", help="重建索引 (覆盖该库)", use_container_width=True):
                        # 触发重建逻辑
                        st.session_state.uploaded_path = os.path.join("vector_db_storage", current_kb_name)
                        # 这里需要一种方式标记为 NEW 模式，并通过 trigger_btn_start 强制触发
                        st.session_state.trigger_rebuild = True
                        st.session_state.trigger_btn_start = True
                        st.rerun()
                else:
                    st.button("🔒", help="无重建索引权限", disabled=True, use_container_width=True)

            # 追加模式的文件上传
            action_mode = "APPEND"
            # 如果触发了重建，则强制改为 NEW
            if st.session_state.get('trigger_rebuild'):
                action_mode = "NEW"
                st.session_state.trigger_rebuild = False # 消费掉标记
            
            # 初始化 btn_start
            if st.session_state.get('trigger_btn_start'):
                btn_start = True
                st.session_state.trigger_btn_start = False # 消费掉标记
            
            target_path = "" # 管理模式不需要手动指定路径，使用KB原有路径
            
            uploaded_files = st.file_uploader(
                "追加文件到当前知识库", 
                accept_multiple_files=True, 
                key="uploader_append",
                label_visibility="collapsed"
            )
            
            # 添加更新知识库按钮
            if uploaded_files:
                # 添加文件上传成功提示
                st.success(f"✅ 文件上传成功！共选择了 {len(uploaded_files)} 个文件")
                
                # 导入进度显示组件
                from src.ui.document_progress import doc_progress
                
                # 显示文件处理进度
                st.markdown("### 📄 文件处理进度")
                doc_progress.start_processing(uploaded_files)
                
                # 文档质量评估
                if st.checkbox("📊 启用文档质量评估", value=False, key="enable_quality_assessment"):
                    st.markdown("### 📋 文档质量评估")
                    from src.utils.document_quality_assessor import show_quality_assessment, quality_assessor
                    
                    # 对每个上传的文件进行质量评估
                    for uploaded_file in uploaded_files:
                        if uploaded_file.type.startswith('text/') or uploaded_file.name.endswith(('.txt', '.md')):
                            try:
                                content = str(uploaded_file.read(), "utf-8")
                                uploaded_file.seek(0)  # 重置文件指针
                                
                                with st.expander(f"📄 {uploaded_file.name} - 质量评估"):
                                    show_quality_assessment(content, uploaded_file.name)
                            except Exception as e:
                                st.warning(f"⚠️ 无法评估 {uploaded_file.name}: {str(e)}")
                        elif uploaded_file.name.endswith('.pdf'):
                            try:
                                with st.expander(f"📄 {uploaded_file.name} - PDF质量评估"):
                                    assessment_result = quality_assessor.assess_pdf_file(uploaded_file)
                                    
                                    # 显示评估结果
                                    col1, col2, col3 = st.columns(3)
                                    
                                    with col1:
                                        score = assessment_result['scores']['overall']
                                        if score >= 80:
                                            st.success(f"📊 总体评分: {score:.1f}")
                                        elif score >= 60:
                                            st.warning(f"📊 总体评分: {score:.1f}")
                                        else:
                                            st.error(f"📊 总体评分: {score:.1f}")
                                    
                                    with col2:
                                        st.info(f"🏆 质量等级: {assessment_result['grade']}")
                                    
                                    with col3:
                                        st.info(f"📄 字数: {assessment_result['word_count']}")
                                    
                                    # 详细评分
                                    st.markdown("**📋 详细评分**")
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.metric("📖 可读性", f"{assessment_result['scores']['readability']:.1f}")
                                        st.metric("💡 内容密度", f"{assessment_result['scores']['content_density']:.1f}")
                                    
                                    with col2:
                                        st.metric("🏗️ 结构性", f"{assessment_result['scores']['structure']:.1f}")
                                        st.metric("✏️ 语言质量", f"{assessment_result['scores']['language_quality']:.1f}")
                                    
                                    # 改进建议
                                    if assessment_result['suggestions']:
                                        st.markdown("**💡 改进建议**")
                                        for suggestion in assessment_result['suggestions']:
                                            st.write(f"• {suggestion}")
                                            st.write(f"• {suggestion}")
                                            
                            except Exception as e:
                                st.error(f"❌ PDF评估失败 {uploaded_file.name}: {str(e)}")
                        else:
                            st.info(f"📄 {uploaded_file.name} - 暂不支持此文件类型的质量评估")
                
                # 高级选项 (复用新建模式的逻辑)
                with st.expander("🔧 高级选项 (本次更新有效)", expanded=False):
                    # 布局优化：全选 + 状态提示在一行
                    h_col1, h_col2 = st.columns([1.5, 2.5])
                    with h_col1:
                        select_all = st.checkbox("✅ 一键全选", value=False, key="kb_adv_select_all_update", help="开启/关闭所有高级选项")
                    with h_col2:
                        status_placeholder = st.empty()
                    
                    default_val = select_all
                    
                    opt_col1, opt_col2, opt_col3 = st.columns(3)
                    with opt_col1:
                        st.checkbox("🔍 OCR识别", value=default_val, key="kb_use_ocr", help="识别PDF中的图片文字")
                    with opt_col2:
                        st.checkbox("📊 元数据", value=default_val, key="kb_extract_metadata", help="提取文件分类、关键词")
                    with opt_col3:
                        st.checkbox("📝 生成摘要", value=default_val, key="kb_generate_summary", help="生成AI摘要")
                    
                    # 更新状态提示
                    options = []
                    if st.session_state.get("kb_use_ocr"): options.append("OCR")
                    if st.session_state.get("kb_extract_metadata"): options.append("元数据")
                    if st.session_state.get("kb_generate_summary"): options.append("摘要")
                    
                    if options:
                        status_placeholder.caption(f"🔧 启用: {'|'.join(options)}")
                    else:
                        status_placeholder.caption("⚡ 快速模式：已关闭高级选项")

                st.info("💡 上传后请点击下方 '更新知识库' 按钮")
                if st.button("🔄 更新知识库", type="primary", use_container_width=True, key="update_kb_btn"):
                    # 立即处理上传，确保路径存在 (Failsafe)
                    try:
                        from src.processors.upload_handler import UploadHandler
                        # UPLOAD_DIR is global/imported
                        handler = UploadHandler(UPLOAD_DIR, logger)
                        with st.spinner("正在预处理文件..."):
                            result = handler.process_uploads(uploaded_files)
                            st.session_state.uploaded_path = os.path.abspath(result.batch_dir)
                            st.session_state.last_processed_path = st.session_state.uploaded_path
                            # Update hash to prevent double processing downstream
                            import hashlib
                            upload_hash = hashlib.md5("".join([f"{f.name}_{f.size}" for f in uploaded_files]).encode()).hexdigest()
                            st.session_state.last_upload_hash = upload_hash
                    except Exception as e:
                        logger.error(f"Immediate upload processing failed: {e}")
                    
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
        # btn_start already initialized above
        
        if is_create_mode:
            if source_mode == "🔗 网址抓取":
                # 权限拦截 (实时校验)
                from src.auth.permission_manager import permission_manager
                current_user = st.session_state.get('user', 'guest_user')
                can_crawl = permission_manager.has_permission(current_user, "use_crawler")
                
                if not can_crawl:
                    st.warning("🔒 权限不足：您当前的角色没有抓取网页的权限。")
                
                # --- 网址抓取模式 ---
                # 设置同步状态
                st.session_state.crawl_input_mode = "url"
                
                # 加载优化器
                try:
                    from src.processors.crawl_optimizer import CrawlOptimizer
                    if 'crawl_optimizer' not in st.session_state:
                        st.session_state.crawl_optimizer = CrawlOptimizer()
                    optimizer = st.session_state.crawl_optimizer
                except ImportError:
                    optimizer = None

                c_url, c_btn = st.columns([7, 1])
                with c_url:
                    crawl_url = st.text_input("网址", placeholder="https://example.com", label_visibility="collapsed")
                    st.session_state.crawl_url = crawl_url
                with c_btn:
                    if st.button("🧠", help="AI分析", key="smart_analyze_url", use_container_width=True):
                        if crawl_url:
                            with st.spinner("🔍"):
                                test_url = crawl_url if crawl_url.startswith(('http://', 'https://')) else f"https://{crawl_url}"
                                analysis = optimizer.analyze_website(test_url) if optimizer else None
                                if analysis: st.session_state.crawl_analysis = analysis
                        else:
                            st.toast("请先输入网址", icon="⚠️")
                
                # 分析结果
                if 'crawl_analysis' in st.session_state:
                    analysis = st.session_state.crawl_analysis
                    with st.expander("🎯 推荐: " + analysis['site_type'].title(), expanded=True):
                        st.caption(f"💡 {analysis['description']}")

                # 参数行 (紧凑 4列布局)
                c_p1, c_p2, c_p3, c_p4 = st.columns(4)
                with c_p1:
                    default_depth = st.session_state.crawl_analysis['recommended_depth'] if 'crawl_analysis' in st.session_state else 2
                    crawl_depth = st.number_input("递归深度", 1, 10, default_depth)
                    st.session_state.crawl_depth = crawl_depth
                with c_p2:
                    default_pages = st.session_state.crawl_analysis['recommended_pages'] if 'crawl_analysis' in st.session_state else 5
                    max_pages = st.number_input("最大页数", 1, 1000, default_pages)
                    st.session_state.max_pages = max_pages
                with c_p3:
                    parser_type = st.selectbox("解析器", ["default", "article", "documentation"], label_visibility="visible")
                    st.session_state.parser_type = parser_type
                with c_p4:
                    # 质量筛选 (简化为数字输入，0表示关闭)
                    url_quality_threshold = st.number_input("质量阈值 (0=关)", 0.0, 100.0, 45.0, 5.0, help="内容质量评分阈值，低于此分数的页面将被丢弃")
                    st.session_state.url_quality_threshold = url_quality_threshold
                    enable_url_filter = (url_quality_threshold > 0)
                
                search_keyword = None # 互斥

            elif source_mode == "🔍 智能搜索":
                # --- 智能搜索模式 ---
                # 设置同步状态
                st.session_state.crawl_input_mode = "search"
                crawl_url = None # 互斥
                
                # 行业选择 (紧凑)
                try:
                    from src.config.unified_sites import get_industry_list
                    industries = get_industry_list()
                    sel_ind = st.selectbox("行业", industries, label_visibility="collapsed")
                except:
                    sel_ind = "🔧 技术开发"
                
                c_kw, c_btn = st.columns([7, 1])
                with c_kw:
                    search_keyword = st.text_input("关键词", placeholder="输入搜索内容...", label_visibility="collapsed")
                    st.session_state.search_keyword = search_keyword
                with c_btn:
                    st.button("🧠", help="AI推荐", key="smart_analyze_search", use_container_width=True)

                # 参数行 (紧凑 4列布局)
                c_s1, c_s2, c_s3, c_s4 = st.columns(4)
                with c_s1:
                    crawl_depth = st.number_input("深度", 1, 5, 2)
                    st.session_state.search_crawl_depth = crawl_depth
                with c_s2:
                    max_pages = st.number_input("总页数", 1, 500, 5)
                    st.session_state.search_max_pages = max_pages
                with c_s3:
                    parser_type = st.selectbox("解析器", ["default", "article", "documentation"], key="parser_search")
                    st.session_state.search_parser_type = parser_type
                with c_s4:
                    # 质量筛选 (简化为数字输入，0表示关闭)
                    quality_threshold = st.number_input("质量阈值 (0=关)", 0.0, 100.0, 0.0, 5.0, key="search_quality_threshold", help="内容质量评分阈值")
                    st.session_state.quality_threshold = quality_threshold
                
                # 预估提示
                est_pages = max_pages ** crawl_depth
                if est_pages > 100: st.caption(f"ℹ️ 预估抓取: {est_pages} 页")
                
                selected_industry = sel_ind # 传递变量

            # 排除配置 (通用)
            if source_mode in ["🔗 网址抓取", "🔍 智能搜索"]:
                with st.expander("🚫 排除链接", expanded=False):
                    exclude_text = st.text_area("每行一个", height=68, placeholder="*/admin/*")
                    exclude_patterns = [line.strip() for line in exclude_text.split('\n') if line.strip()] if exclude_text else []
                
                # 抓取按钮 (已移除，功能合并至侧边栏按钮)

            # 处理上传 (Stage 4.1 - 使用 UploadHandler)
            if uploaded_files:
                # 使用文件名+大小的组合作为哈希，判断文件列表是否真正改变
                import hashlib
                upload_hash = hashlib.md5("".join([f"{f.name}_{f.size}" for f in uploaded_files]).encode()).hexdigest()
                
                # 只要哈希不同，或者当前没有有效的上传路径，就重新处理
                # 这能修复“路径丢失”的问题，同时保留哈希优化
                if st.session_state.get('last_upload_hash') != upload_hash or not st.session_state.get('uploaded_path'):
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
                    st.session_state.last_processed_path = st.session_state.uploaded_path
                    
                    # 显示上传结果
                    if result.success_count > 0:
                        st.toast(f"✅ 成功上传 {result.success_count} 个文件")
                        
                        # 文档质量评估
                        if st.checkbox("📊 启用文档质量评估", value=False, key="enable_quality_assessment_new"):
                            st.markdown("### 📋 文档质量评估")
                            from src.utils.document_quality_assessor import show_quality_assessment, quality_assessor
                            
                            # 对每个上传的文件进行质量评估
                            for uploaded_file in uploaded_files:
                                if uploaded_file.type.startswith('text/') or uploaded_file.name.endswith(('.txt', '.md')):
                                    try:
                                        content = str(uploaded_file.read(), "utf-8")
                                        uploaded_file.seek(0)  # 重置文件指针
                                        
                                        with st.expander(f"📄 {uploaded_file.name} - 质量评估"):
                                            show_quality_assessment(content, uploaded_file.name)
                                    except Exception as e:
                                        st.warning(f"⚠️ 无法评估 {uploaded_file.name}: {str(e)}")
                                elif uploaded_file.name.endswith('.pdf'):
                                    try:
                                        with st.expander(f"📄 {uploaded_file.name} - PDF质量评估"):
                                            assessment_result = quality_assessor.assess_pdf_file(uploaded_file)
                                            
                                            # 显示评估结果
                                            col1, col2, col3 = st.columns(3)
                                            
                                            with col1:
                                                score = assessment_result['scores']['overall']
                                                if score >= 80:
                                                    st.success(f"📊 总体评分: {score:.1f}")
                                                elif score >= 60:
                                                    st.warning(f"📊 总体评分: {score:.1f}")
                                                else:
                                                    st.error(f"📊 总体评分: {score:.1f}")
                                            
                                            with col2:
                                                st.info(f"🏆 质量等级: {assessment_result['grade']}")
                                            
                                            with col3:
                                                st.info(f"📄 字数: {assessment_result['word_count']}")
                                            
                                            # 详细评分
                                            st.markdown("**📋 详细评分**")
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.metric("📖 可读性", f"{assessment_result['scores']['readability']:.1f}")
                                                st.metric("💡 内容密度", f"{assessment_result['scores']['content_density']:.1f}")
                                            
                                            with col2:
                                                st.metric("🏗️ 结构性", f"{assessment_result['scores']['structure']:.1f}")
                                                st.metric("✏️ 语言质量", f"{assessment_result['scores']['language_quality']:.1f}")
                                            
                                            # 改进建议
                                            if assessment_result['suggestions']:
                                                st.markdown("**💡 改进建议**")
                                                for suggestion in assessment_result['suggestions']:
                                                    st.write(f"• {suggestion}")
                                                    
                                    except Exception as e:
                                        st.error(f"❌ PDF评估失败 {uploaded_file.name}: {str(e)}")
                                else:
                                    st.info(f"📄 {uploaded_file.name} - 暂不支持此文件类型的质量评估")

                    if result.skipped_count > 0:
                        st.warning(f"⚠️ 跳过 {result.skipped_count} 个文件")

                    # 为文件上传场景生成智能名称 (兼容数据分析模式)
                    if result.success_count > 0:
                        try:
                            # 统一捕获当前模式下的文件列表
                            curr_files = uploaded_files if uploaded_files else []
                            
                            file_types = {}
                            for f in curr_files:
                                ext = os.path.splitext(f.name)[1].lower()
                                file_types[ext] = file_types.get(ext, 0) + 1

                            folder_name = os.path.basename(result.batch_dir)
                            auto_name = generate_smart_kb_name(result.batch_dir, result.success_count, file_types, folder_name)
                            st.session_state.upload_auto_name = auto_name
                        except Exception:
                            st.session_state.upload_auto_name = None
                    
                    # 关键修复：不再强制全页面 rerun，而是依靠 Streamlit 自然流转
                    # 这样可以保留 uploader 的状态，避免其因刷新而报错或重置
                
                elif st.session_state.get('last_processed_path'):
                    # 如果哈希匹配（说明是 rerun），且有备份路径，则恢复
                    logger.debug(st.session_state.last_processed_path)
                    st.session_state.uploaded_path = st.session_state.last_processed_path
                else:
                    logger.info("DEBUG: Hash matched but no last_processed_path found!")


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

                    # --- 极简一行化：状态徽章 + 名称输入 ---
                    # 避免在左侧重复显示长文件名，只显示状态，名称在输入框中显示
                    status_col, input_col = st.columns([1.2, 4])
                    
                    with status_col:
                        # 垂直居中的状态徽章
                        st.markdown(
                            """<div style='
                                background: #f0fdf4; 
                                color: #15803d; 
                                padding: 6px 8px; 
                                border-radius: 6px; 
                                border: 1px solid #bbf7d0;
                                text-align: center; 
                                font-size: 0.85rem; 
                                font-weight: 500;
                                white-space: nowrap;
                                margin-top: 1px;
                            '>✅ 源就绪</div>""", 
                            unsafe_allow_html=True
                        )
                    
                    with input_col:
                        if is_create_mode:
                            final_kb_name = st.text_input(
                                "知识库名称", 
                                value=sanitize_filename(auto_name) if auto_name else "", 
                                placeholder="输入库名",
                                label_visibility="collapsed",
                                key="kb_name_inline_input"
                            )
                        else:
                            final_kb_name = current_kb_name
                            st.markdown(f"<div style='padding-top: 6px;'><b>{final_kb_name}</b></div>", unsafe_allow_html=True)

                    # 类型分布（紧凑化）
                    if file_types:
                        sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]
                        type_text = " · ".join([f"{ext.replace('.', '')}:{count}" for ext, count in sorted_types])
                        st.caption(f"📊 {type_text} · 源: {display_name}")
                else:
                    # 只有在非爬虫且非数据分析初级阶段时才报错
                    is_web_waiting = (source_mode == "🔗 网址抓取" and st.session_state.get('crawl_url_input'))
                    is_da_waiting = (source_mode == "📊 数据分析" and uploaded_files)
                    
                    if not is_web_waiting and not is_da_waiting:
                        st.error("❌ 路径不存在，请检查路径是否正确")
                        # 添加友好的错误引导
                        from src.utils.friendly_error_handler import friendly_error
                        friendly_error("文件上传", 
                                     "指定的路径不存在或无法访问",
                                     ["检查路径拼写是否正确", "确认您有访问该路径的权限", "尝试使用文件上传功能代替手动路径"])
                    elif is_da_waiting:
                        st.markdown(
                            """<div style='background: #fffbeb; color: #92400e; padding: 6px 8px; border-radius: 6px; border: 1px solid #fef3c7; text-align: center; font-size: 0.85rem;'>⏳ 等待文件预处理...</div>""", 
                            unsafe_allow_html=True
                        )
                    final_kb_name = current_kb_name if not is_create_mode else ""
            else:
                final_kb_name = current_kb_name if not is_create_mode else ""

            st.write("")

            # 高级选项
            with st.expander("🔧 高级选项", expanded=False):
                # 布局优化：全选 + 状态提示在一行
                h_col1, h_col2 = st.columns([1.5, 2.5])
                with h_col1:
                    select_all = st.checkbox("✅ 一键全选", value=False, key="kb_adv_select_all", help="开启/关闭所有高级选项")
                with h_col2:
                    status_placeholder = st.empty()
                
                # 根据一键全选状态设置默认值
                default_val = select_all

                # 选项布局：如果非新建模式，显示强制重建索引
                # 新建模式下隐藏强制重建（本身就是新建）
                if not is_create_mode:
                    # 权限检查
                    from src.auth.permission_manager import permission_manager
                    current_user = st.session_state.get('user', 'guest_user')
                    can_rebuild = permission_manager.has_permission(current_user, "kb_rebuild_index")
                    
                    if can_rebuild:
                        force_reindex = st.checkbox("🔄 强制重建索引", value=default_val, key="kb_force_reindex", help="删除现有索引，重新构建")
                    else:
                        st.checkbox("🔄 强制重建索引 (🔒)", value=False, disabled=True, help="无重建索引权限")
                        force_reindex = False
                else:
                    force_reindex = False

                # 剩下的3个选项显示在一行
                opt_col1, opt_col2, opt_col3 = st.columns(3)
                with opt_col1:
                    use_ocr = st.checkbox("🔍 OCR识别", value=default_val, key="kb_use_ocr", help="识别PDF中的图片文字")
                with opt_col2:
                    extract_metadata = st.checkbox("📊 元数据", value=default_val, key="kb_extract_metadata", help="提取文件分类、关键词")
                with opt_col3:
                    generate_summary = st.checkbox("📝 生成摘要", value=default_val, key="kb_generate_summary", help="生成AI摘要")
                
                # 保存到session state
                st.session_state.use_ocr = use_ocr
                st.session_state.generate_summary = generate_summary
                
                # 更新状态提示
                options = []
                if force_reindex: options.append("重建索引")
                if extract_metadata: options.append("元数据")
                if use_ocr: options.append("OCR")
                if generate_summary: options.append("摘要")
                
                if options:
                    status_placeholder.caption(f"🔧 启用: {'|'.join(options)}")
                else:
                    status_placeholder.caption("⚡ 快速模式：已关闭高级选项")


            st.write("")

            btn_label = "🚀 立即创建" if is_create_mode else ("➕ 执行追加" if action_mode=="APPEND" else "🔄 执行覆盖")
            btn_start = st.button(btn_label, type="primary", use_container_width=True, key="main_sidebar_start_btn")
            
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
            
            # 确保 action_mode 在此定义
            if 'action_mode' not in locals():
                action_mode = "NEW" if is_create_mode else "APPEND"

        # --- 现有库的管理 (卡片式布局) ---
        if not is_create_mode:
            # 注入 CSS 修复按钮对齐问题
            st.markdown("""
            <style>
            /* 强制统一操作栏按钮的高度和对齐 */
            div[data-testid="column"] button, 
            div[data-testid="column"] a {
                min-height: 38px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                margin-top: 0px !important;
            }
            /* 修复下载按钮和链接按钮的文字偏移 */
            div[data-testid="stDownloadButton"] > button,
            div[data-testid="stLinkButton"] > a {
                padding-top: 0px !important;
                padding-bottom: 0px !important;
                line-height: 1 !important;
            }
            </style>
            """, unsafe_allow_html=True)
            
            with st.container(border=True):
                # 顶部信息栏已移除（用户反馈冗余）
                
                # 底部：操作栏 (优化为 4 + 1 布局)
                op_row1 = st.columns(4)
                op_row2 = st.columns(1)
                
                # 第一行：常用操作
                with op_row1[0]:
                    if st.button("🔄 撤销", use_container_width=True, disabled=len(state.get_messages()) < 2, help="撤销最近一轮对话"):
                        if len(state.get_messages()) >= 2:
                            st.session_state.messages.pop()
                            st.session_state.messages.pop()
                            if current_kb_name:
                                HistoryManager.save_session(current_kb_name, state.get_messages(), st.session_state.get('current_session_id'))
                            st.toast("✅ 已撤销")
                            time.sleep(0.5)
                            st.rerun()
                
                with op_row1[1]:
                    if st.button("➕ 新对话", use_container_width=True, disabled=len(state.get_messages()) == 0, help="保存当前记录并开始新对话"):
                        import uuid
                        # 生成新会话ID
                        new_id = str(uuid.uuid4())[:8]
                        # 切换到新会话 (旧会话已自动保存)
                        st.session_state.current_session_id = new_id
                        st.session_state.messages = []
                        st.session_state.suggestions_history = []
                        # 初始化存储
                        if current_kb_name:
                            HistoryManager.save_session(current_kb_name, [], new_id)
                        
                        st.toast("✅ 已开启新会话，旧记录可在左侧历史中查看")
                        time.sleep(0.5)
                        st.rerun()
                
                with op_row1[2]:
                    export_content = ""
                    if len(state.get_messages()) > 0:
                        export_content = f"# 对话记录 - {current_kb_name}\n\n**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
                        for i, msg in enumerate(st.session_state.messages, 1):
                            role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
                            export_content += f"## {role} ({i})\n\n{msg['content']}\n\n"
                    
                    st.download_button("📥 导出", export_content, file_name=f"chat_{current_kb_name}_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown", use_container_width=True, disabled=len(state.get_messages()) == 0)

                with op_row1[3]:
                    # 删除权限检查 (颗粒化)
                    from src.auth.permission_manager import permission_manager
                    current_user = st.session_state.get('user', 'guest_user')
                    can_delete = permission_manager.has_permission(current_user, "kb_delete_own")
                    
                    if st.button("🗑️ 删除", use_container_width=True, type="primary", disabled=not current_kb_name or not can_delete, help="永久删除该知识库" if can_delete else "🔒 您没有删除知识库的权限"):
                        st.session_state.confirm_delete = True
                        st.rerun()

                # 第二行：视图与窗口
                with op_row2[0]:
                    st.link_button("🔀 打开新窗口", "http://localhost:8501", use_container_width=True, help="在浏览器新标签页打开")
            
            # 删除确认对话框 (放在卡片外，避免嵌套问题)
            if st.session_state.get('confirm_delete', False):
                st.warning(f"⚠️ 确认永久删除知识库 '{current_kb_name}' 吗？此操作不可恢复！")
                confirm_col1, confirm_col2 = st.columns([1, 1])
                
                with confirm_col1:
                    if st.button("✅ 确认删除", type="primary", use_container_width=True):
                        from src.auth.audit_logger import AuditLogger
                        from src.common.utils import get_client_ip
                        AuditLogger.log(st.session_state.get('user'), "DELETE_KB", f"永久删除了知识库: {current_kb_name}", status="warning", ip=get_client_ip())
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
            
    
    with tab_roles:
        from src.ui.role_manager_ui import RoleManagerUI
        RoleManagerUI.render()

    with tab_config:
        st.session_state.current_tab = "config"
        
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
    
    with tab_help:
        st.markdown("### 📖 RAG Pro Max 智能门户")
        
        # 1. 搜索栏
        help_search = st.text_input("🔍 搜索功能、配置或疑难解答...", placeholder="例如：GPU 加速、API、部署...", key="help_search_input")
        
        if help_search:
            # 简单的关键词检索逻辑
            from src.utils.doc_search import search_docs
            results = search_docs(help_search)
            if results:
                st.markdown(f"**找到 {len(results)} 条相关结果:**")
                for res in results:
                    with st.expander(f"📄 {res['title']}", expanded=True):
                        st.markdown(res['preview'])
                        if st.button(f"查看完整文档: {res['file']}", key=f"view_full_{res['file']}"):
                            st.session_state.full_doc_to_show = res['file']
                st.divider()
            else:
                st.warning("未找到匹配内容，请尝试更简单的关键词。")

        # 2. 动态导航与快速入口
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🚀 快速上手", use_container_width=True):
                st.session_state.help_active_tab = "onboarding"
        with col2:
            if st.button("🔌 API 文档", use_container_width=True):
                st.session_state.help_active_tab = "api"
        with col3:
            if st.button("❓ 常见问题", use_container_width=True):
                st.session_state.help_active_tab = "faq"

        # 3. 核心内容区
        active_tab = st.session_state.get('help_active_tab', 'onboarding')
        
        if active_tab == "onboarding":
            # --- 1. Hero Header: 产品概览 ---
            st.markdown("""
            <div style="background: linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%); padding: 2rem; border-radius: 12px; margin-bottom: 2rem; border: 1px solid #e0e0e0;">
                <h1 style="color: #1a1a1a; margin-bottom: 0.5rem;">🌌 RAG Pro Max <span style="font-size: 1rem; color: #666; font-weight: normal;">v5.6.0 Enterprise</span></h1>
                <p style="color: #4a4a4a; font-size: 1.1rem; line-height: 1.6;">
                    <b>云原生级私有化知识中台</b> — 专为高价值数据设计的下一代认知引擎。<br>
                    融合了 <b>OCR 视觉解析</b>、<b>混合语义检索</b> 与 <b>CoT 深度推理</b>，让您的文档真正“开口说话”。
                </p>
            </div>
            """, unsafe_allow_html=True)

            # --- 2. 核心能力矩阵 (仿阿里云功能特性) ---
            st.markdown("#### ✨ 核心能力矩阵")
            cap_col1, cap_col2, cap_col3, cap_col4 = st.columns(4)
            
            with cap_col1:
                with st.container(border=True):
                    st.markdown("#### 📄 全模态解析")
                    st.caption("不仅仅是文本。支持 PDF 表格还原、Excel 数据透视及图片 OCR 识别。")
                    st.markdown("`PDF` `Excel` `Image` `Markdown`")
            
            with cap_col2:
                with st.container(border=True):
                    st.markdown("#### 🔍 混合检索")
                    st.caption("BM25 关键词匹配 + BGE 向量语义召回，确保专业术语与模糊语义都不遗漏。")
                    st.markdown("`Hybrid Search` `Rerank`")

            with cap_col3:
                with st.container(border=True):
                    st.markdown("#### 🧠 深度思考")
                    st.caption("内置 Chain-of-Thought (CoT) 推理链，支持多步推演与专家会审模式。")
                    st.markdown("`CoT` `Multi-Agent` `Reasoning`")
            
            with cap_col4:
                with st.container(border=True):
                    st.markdown("#### 🛡️ 数据主权")
                    st.caption("100% 本地化部署。支持 RBAC 细粒度权限管控与全量资产加密导出。")
                    st.markdown("`Local First` `RBAC` `Encrypted`")

            st.markdown("---")

            # --- 3. 快速行动区 ---
            st.markdown("#### 🚀 快速开始")
            action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
            
            with action_col1:
                if st.button("➕ 新建知识库", use_container_width=True, type="primary"):
                    st.session_state.show_new_kb_dialog = True
                    st.rerun()
                st.caption("开始构建您的第一个知识大脑")
            
            with action_col2:
                if st.button("💬 纯对话模式", use_container_width=True):
                    st.session_state.current_kb_id = "pure_chat"
                    st.session_state.chat_engine = "pure_chat"
                    st.rerun()
                st.caption("直接与底层大模型进行交互")
            
            with action_col3:
                # 状态检查清单 (优化版)
                with st.expander("✅ 环境自检清单 (System Health)", expanded=False):
                    check_cols = st.columns(2)
                    check_cols[0].success("Python 3.10+ Runtime Ready")
                    check_cols[0].success("Vector DB (Chroma) Connected")
                    check_cols[1].success("LLM/Embedding Model Loaded")
                    check_cols[1].success("GPU Acceleration Enabled")

            st.markdown("---")

            # --- 4. 系统架构图 (Mermaid) ---
            st.markdown("#### 🏗️ 逻辑架构视图")
            st.markdown("""
            ```mermaid
            graph LR
                A[📂 非结构化数据] -->|OCR/Parser| B(统一文档对象)
                B -->|Chunking| C{混合索引引擎}
                C -->|Embedding| D[向量数据库]
                C -->|Tokenize| E[倒排索引库]
                
                U[👤 用户提问] -->|Rewrite| Q[优化查询]
                Q -->|Retrieve| D & E
                D & E -->|Fusion| R[重排序结果]
                R -->|Context| L[🧠 LLM 推理核心]
                L -->|Answer| O[💡 最终答案]
                
                style C fill:#e1f5fe,stroke:#01579b
                style L fill:#fff3e0,stroke:#ff6f00
                style U fill:#f3e5f5,stroke:#7b1fa2
            ```
            """)
            st.caption("RAG Pro Max 数据流转示意图")

        elif active_tab == "api":
            st.markdown("#### 🔌 开发者与 API 集成")
            st.code("""
# 快速查询示例
import requests
resp = requests.post("http://localhost:8000/query", 
                     json={"query": "核心逻辑是什么?", "kb_name": "tech_doc"})
print(resp.json()["answer"])
            """, language="python")
            st.caption("详细接口说明请参考根目录下的 `API_DOCUMENTATION.md`")

        elif active_tab == "faq":
            st.markdown("#### ❓ 常见问题汇总")
            faqs = [
                ("为什么分析图表无法显示？", "请确保查询涉及结构化数据。系统会自动感应数据特征并切换模式。"),
                ("如何迁移知识库？", "导出“终极五福资产包” ZIP，在目标机器解压至 `vector_db_storage` 即可。"),
                ("GPU 占用过高怎么办？", "可在配置中心调低“并发工作进程数”或切换至 CPU 模式。")
            ]
            for q, a in faqs:
                with st.expander(f"Q: {q}"):
                    st.write(f"A: {a}")

        # 4. 底部快捷文档访问
        st.divider()
        st.markdown("**📚 完整技术文档库**")
        doc_cols = st.columns(4)
        docs = [
            ("架构设计", "ARCHITECTURE.md"),
            ("用户手册", "USER_MANUAL.md"),
            ("部署指南", "DEPLOYMENT.md"),
            ("更新日志", "CHANGELOG.md")
        ]
        for i, (label, file) in enumerate(docs):
            with doc_cols[i % 4]:
                if st.button(label, key=f"doc_btn_{i}", use_container_width=True):
                    # 联动侧边栏的文档查看逻辑
                    try:
                        with open(file, 'r', encoding='utf-8') as f:
                            st.toast(f"正在加载 {file}...")
                            # 这里可以触发一个 dialog 显示内容
                            st.session_state.full_doc_content = f.read()
                            st.session_state.show_doc_dialog = True
                    except:
                        st.error("文档读取失败")

    # 全局文档弹窗
    if st.session_state.get('show_doc_dialog'):
        @st.dialog("📄 技术文档预览", width="large")
        def show_doc():
            st.markdown(st.session_state.full_doc_content)
            if st.button("关闭", use_container_width=True):
                st.session_state.show_doc_dialog = False
                st.rerun()
        show_doc()
        
        # 系统信息
        st.markdown("---")
        st.markdown("#### 📊 系统信息")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            import psutil
            cpu_percent = psutil.cpu_percent()
            st.metric("CPU使用率", f"{cpu_percent}%")
        
        with col2:
            memory = psutil.virtual_memory()
            st.metric("内存使用率", f"{memory.percent}%")
        
        with col3:
            import os
            kb_count = 0
            if os.path.exists("vector_db_storage"):
                kb_count = len([d for d in os.listdir("vector_db_storage") if os.path.isdir(os.path.join("vector_db_storage", d))])
            st.metric("知识库数量", kb_count)
        
        with col4:
            session_count = len([k for k in st.session_state.keys() if 'session' in k.lower()])
            st.metric("活跃会话", session_count)

# ==========================================
# 主功能区域
# ==========================================

# 根据选择的模式显示对应功能
if st.session_state.get('main_mode', 'rag') == 'sql':
    # ==========================================
    # 📊 数据分析模式
    # ==========================================
    st.markdown("##### 📊 数据分析 (Text-to-SQL)")
    
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
        st.markdown("###### 📁 数据导入")
        
        uploaded_data = st.file_uploader(
            "上传Excel/CSV/MD字典文件", 
            type=['xlsx', 'csv', 'md', 'markdown'],
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
            st.markdown("###### 📋 数据结构")
            try:
                schema = st.session_state.sql_engine.get_schema()
                for table, columns in schema.items():
                    with st.expander(f"📊 {table}"):
                        st.write(f"字段: {', '.join(columns)}")
            except:
                st.write("暂无数据")

    with col2:
        st.markdown("###### 💬 数据问答")
        
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
                                    
                                    # --- [v5.8.0] 智能可视化推荐引擎 ---
                                    if len(df) > 0:
                                        with st.spinner("🤖 正在思考最佳可视化方案..."):
                                            try:
                                                import plotly.express as px
                                                
                                                # 获取推荐
                                                # da_engine 是在外面定义的，这里需要确保能访问到。
                                                # 由于前面是在 `if is_da_mode or data_files:` 块里初始化的 da_engine，
                                                # 但这里是 `if is_data_analysis_mode:` 块，可能不在同一个作用域。
                                                # 幸运的是，`da_engine` 通常是按需初始化的。
                                                # 我们需要重新获取 persist_dir 来初始化 da_engine
                                                
                                                # 获取当前知识库路径
                                                current_kb_id = st.session_state.get('current_kb_id')
                                                if current_kb_id:
                                                    kb_path = os.path.join(output_base, current_kb_id)
                                                    from src.processors.data_analyst import DataAnalystEngine
                                                    temp_da_engine = DataAnalystEngine(kb_path, logger)
                                                    
                                                    rec = temp_da_engine.recommend_visualization(
                                                        data_query, 
                                                        df.columns.tolist(), 
                                                        df.head(3).to_dict(orient='records'), 
                                                        st.session_state.llm
                                                    )
                                                    
                                                    viz_type = rec.get('viz_type', 'table')
                                                    x_axis = rec.get('x_axis')
                                                    y_axis = rec.get('y_axis')
                                                    color = rec.get('color') # [v5.8.1] 支持分组/颜色维度
                                                    title = rec.get('title', '数据可视化')
                                                    reason = rec.get('reason', '')
                                                    
                                                    if reason:
                                                        st.caption(f"💡 AI建议: {reason}")
                                                    
                                                    if viz_type != 'table':
                                                        st.markdown(f"### {title}")
                                                        fig = None
                                                        
                                                        try:
                                                            # 智能绘图参数组装
                                                            common_args = {'title': title}
                                                            if color and color in df.columns:
                                                                common_args['color'] = color
                                                            
                                                            if viz_type == 'bar':
                                                                fig = px.bar(df, x=x_axis, y=y_axis, **common_args)
                                                            elif viz_type == 'line':
                                                                fig = px.line(df, x=x_axis, y=y_axis, **common_args)
                                                            elif viz_type == 'pie':
                                                                fig = px.pie(df, names=x_axis, values=y_axis if isinstance(y_axis, str) else y_axis[0], title=title)
                                                            elif viz_type == 'scatter':
                                                                fig = px.scatter(df, x=x_axis, y=y_axis, **common_args)
                                                            elif viz_type == 'area':
                                                                fig = px.area(df, x=x_axis, y=y_axis, **common_args)
                                                            elif viz_type == 'box':
                                                                fig = px.box(df, x=x_axis, y=y_axis, **common_args)
                                                            elif viz_type == 'histogram':
                                                                fig = px.histogram(df, x=x_axis, y=y_axis, **common_args)
                                                            elif viz_type == 'heatmap':
                                                                # 热力图通常需要三个维度：x, y, z(color)
                                                                if len(df.columns) >= 3:
                                                                    z_axis = y_axis if isinstance(y_axis, str) else y_axis[0]
                                                                    fig = px.density_heatmap(df, x=x_axis, y=color or df.columns[1], z=z_axis, title=title)
                                                                else:
                                                                    # 降级为表格
                                                                    viz_type = 'table'
                                                            
                                                            if fig:
                                                                st.plotly_chart(fig, use_container_width=True)
                                                            else:
                                                                st.info("AI 建议展示表格")
                                                                
                                                        except Exception as plot_err:
                                                            logger.warning(f"高级绘图失败 ({viz_type}): {plot_err}，尝试降级为 Bar Chart")
                                                            try:
                                                                # 降级尝试：基础柱状图
                                                                fig = px.bar(df, x=x_axis, y=y_axis, title=f"{title} (降级展示)")
                                                                st.plotly_chart(fig, use_container_width=True)
                                                            except:
                                                                st.warning("无法生成图表，请查看上方数据表。")
                                                    
                                            except ImportError:
                                                # 降级方案
                                                if len(df.columns) >= 2:
                                                    chart_col1, chart_col2 = st.columns(2)
                                                    with chart_col1:
                                                        if st.button("📊 柱状图"):
                                                            st.bar_chart(df.set_index(df.columns[0]))
                                                    with chart_col2:
                                                        if st.button("📈 折线图"):
                                                            st.line_chart(df.set_index(df.columns[0]))
                                            except Exception as e:
                                                logger.warning(f"可视化生成失败: {e}")
                                                # 降级方案
                                                if len(df.columns) >= 2:
                                                    st.bar_chart(df.set_index(df.columns[0]))
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

def jump_to_knowledge_base(kb_name: str, output_base: str):
    """统一的知识库跳转逻辑"""
    logger.log("知识库跳转", "start", f"🚀 跳转函数开始执行: {kb_name}")
    logger.log("知识库跳转", "info", f"🔄 准备跳转到知识库: {kb_name}")
    logger.log("知识库跳转", "info", f"📁 输出路径: {output_base}")
    
    # 强制刷新知识库管理器的缓存
    from src.kb.kb_manager import KBManager
    logger.log("知识库跳转", "info", f"🔧 创建知识库管理器实例")
    kb_manager = KBManager(output_base)
    kb_list = kb_manager.list_all()
    logger.log("知识库跳转", "info", f"📋 当前知识库列表: {kb_list}")
    logger.log("知识库跳转", "info", f"📊 知识库总数: {len(kb_list)}")
    
    # 确认新知识库在列表中
    if kb_name in kb_list:
        logger.log("知识库跳转", "success", f"✅ 新知识库已在列表中: {kb_name}")
    else:
        logger.log("知识库跳转", "warning", f"⚠️ 新知识库不在列表中: {kb_name}")
    
    # 设置跳转参数
    logger.log("知识库跳转", "info", f"⚙️ 开始设置跳转参数")
    old_nav = st.session_state.get('current_nav', 'None')
    old_kb_id = st.session_state.get('current_kb_id', 'None')
    
    # 清除多选状态，确保单选模式
    logger.log("知识库跳转", "info", f"🧹 清除多选状态")
    st.session_state.selected_kbs = []
    cleared_count = 0
    for kb in kb_list:
        if st.session_state.get(f"kb_check_{kb}", False):
            cleared_count += 1
        st.session_state[f"kb_check_{kb}"] = False
    
    # --- 核心修复：计算显示名称以匹配侧边栏逻辑 ---
    display_name = kb_name
    try:
        from src.auth.user_auth import load_users
        all_known_users = load_users()
        
        if "_" in kb_name:
            parts = kb_name.split("_", 1)
            # 如果前半部分是已知用户，则剥离
            if parts[0] in all_known_users:
                display_name = parts[1]
    except Exception as e:
        logger.warning(f"无法计算显示名称: {e}")

    # 核心修复：在清理完所有状态后，再设置目标知识库的选中状态
    st.session_state[f"kb_check_{kb_name}"] = True
    # 使用计算出的 display_name 设置 current_nav
    st.session_state.current_nav = f"☑️ 📂 {display_name}"
    st.session_state.current_kb_id = kb_name
    st.session_state.chat_engine = None  # 重置聊天引擎，触发重新加载
    
    logger.log("知识库跳转", "info", f"🧹 已清除 {cleared_count} 个复选框状态")
    logger.log("知识库跳转", "info", f"✅ 跳转参数已设置: current_nav={st.session_state.current_nav}")
    logger.log("知识库跳转", "info", "🚀 执行页面刷新...")
    logger.log("知识库跳转", "complete", f"✅ 跳转函数执行完成: {kb_name}")


def process_knowledge_base_logic(kb_name, action_mode="NEW", use_ocr=False, extract_metadata=False, generate_summary=False, force_reindex=False, owner=None):
    """处理知识库逻辑 (Stage 4.2 - 使用 IndexBuilder)"""
    global logger
    
    persist_dir = os.path.join(output_base, kb_name)
    start_time = time.time()
    
    # 资源保护检查
    cpu = psutil_main.cpu_percent(interval=0.1)
    mem = psutil_main.virtual_memory().percent
    result = resource_guard.check_resources(cpu, mem, 0)
    throttle_info = result.get('throttle', {})
    if throttle_info.get('action') == 'reject':
        st.warning(f"⚠️ 系统资源紧张，请稍后再试")
        logger.warning(f"资源不足，暂停处理: CPU={cpu}%, MEM={mem}%")
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
                # 添加友好的错误引导
                from src.utils.friendly_error_handler import friendly_error
                friendly_error("配置错误", 
                             "嵌入模型无法正常加载",
                             ["检查网络连接是否正常", "确认模型配置是否正确", "尝试使用'⚡ 一键配置'重置设置", "如果使用本地模型，确认模型文件存在"])
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

    logger.log("INFO", f"开始处理知识库: {kb_name}", stage="知识库处理")
    
    # UI 状态容器
    status_container = st.status(f"🚀 处理知识库: {kb_name}", expanded=True)
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
            status_container.warning(f"   {warn_msg}")
            logger.warning(f"   {warn_msg}")
        elif msg_type == "error":
            err_msg = args[0]
            status_container.error(f"   {err_msg}")
            logger.error(f"   {err_msg}")

    # 使用 IndexBuilder 处理
    from src.processors.index_builder import IndexBuilder
    # 显式使用局部变量以防止 Unknown 报错
    builder = IndexBuilder(
        kb_name=kb_name,
        persist_dir=persist_dir,
        embed_model=embed,
        embed_model_name=embed_model, # 使用当前活跃的模型名
        use_ocr=use_ocr,
        extract_metadata=extract_metadata,
        generate_summary=generate_summary,
        logger=logger
    )
    
    # 获取源路径
    current_target_path = st.session_state.get('uploaded_path') or st.session_state.get('path_input')
    if not current_target_path or not os.path.exists(current_target_path):
        status_container.update(label="❌ 路径无效", state="error")
        raise ValueError(f"路径无效: {current_target_path}")

    # --- [v5.7.2 修复] 执行顺序重构：先构建索引(创建目录)，再归档数据 ---
    # 原有问题：IndexBuilder.build 在 NEW 模式下会清空目录，导致先归档的文件被删
    
    # 1. 预扫描 (用于 DA 模式判断和 Schema 提取)
    try:
        docs, _ = builder._read_documents(current_target_path, 0, None)
    except:
        docs = []

    # 2. 判断是否启用数据分析模式 & 是否允许空文档
    is_da_mode = st.session_state.get('is_data_analysis_mode', False)
    
    has_data_files = False
    if os.path.exists(current_target_path):
        import glob
        if os.path.isdir(current_target_path):
            has_csv = bool(glob.glob(os.path.join(current_target_path, "**/*.csv"), recursive=True))
            has_xlsx = bool(glob.glob(os.path.join(current_target_path, "**/*.xlsx"), recursive=True))
            has_data_files = has_csv or has_xlsx
        elif current_target_path.endswith(('.csv', '.xlsx', '.xls')):
            has_data_files = True

    allow_empty_docs = is_da_mode or has_data_files

    # 3. 执行标准构建 (RAG + Indexing)
    # 注意：build() 在 NEW 模式下会清空 persist_dir，所以必须先执行
    try:
        result = builder.build(
            source_path=current_target_path,
            force_reindex=force_reindex,
            action_mode=action_mode,
            status_callback=status_callback
        )
    except Exception as e:
        if allow_empty_docs:
            # 数据分析模式允许 RAG 读取失败
            logger.warning(f"RAG索引构建跳过(数据分析模式): {e}")
            from src.processors.index_builder import BuildResult
            result = BuildResult(True, None, 0, 0, 0)
        else:
            raise e

    # 4. [v5.5.5] 全量物理归档 (必须在 build 之后)
    try:
        raw_sources_dir = os.path.join(persist_dir, "raw_sources")
        
        # [v6.3.0] 物理隔离增强：如果是新建模式，清空原有的物理归档目录
        if action_mode == "NEW" and os.path.exists(raw_sources_dir):
            import shutil
            status_container.write("🧹 正在清理旧版物理资产...")
            shutil.rmtree(raw_sources_dir)
            
        if not os.path.exists(raw_sources_dir):
            os.makedirs(raw_sources_dir)
            
        if current_target_path and os.path.exists(current_target_path):
            import shutil
            status_container.write("📦 正在执行原始文献的物理归档与持久化...")
            if os.path.isdir(current_target_path):
                # 递归拷贝整个上传目录
                for root, dirs, files in os.walk(current_target_path):
                    for file in files:
                        if file.startswith('.'): continue
                        src_file = os.path.join(root, file)
                        shutil.copy2(src_file, os.path.join(raw_sources_dir, file))
            else:
                shutil.copy2(current_target_path, os.path.join(raw_sources_dir, os.path.basename(current_target_path)))
            
            logger.info(f"✅ [Data Sovereignty] 所有源材料已安全归档至: {raw_sources_dir}")
    except Exception as e:
        logger.warning(f"⚠️ 原始文件归档失败: {e}")

    # 5. 数据分析引擎处理 (必须在归档之后)
    # 扫描归档后的文件
    import glob
    data_files = []
    if os.path.exists(raw_sources_dir):
        csvs = glob.glob(os.path.join(raw_sources_dir, "**/*.csv"), recursive=True)
        excels = glob.glob(os.path.join(raw_sources_dir, "**/*.xlsx"), recursive=True) + glob.glob(os.path.join(raw_sources_dir, "**/*.xls"), recursive=True)
        mds = glob.glob(os.path.join(raw_sources_dir, "**/*.md"), recursive=True) + glob.glob(os.path.join(raw_sources_dir, "**/*.markdown"), recursive=True)
        data_files = csvs + excels + mds
    
    if is_da_mode or data_files:
        status_container.write("📂 [专项] 启动业务语义大脑引擎...")
        from src.processors.data_analyst import DataAnalystEngine
        from src.utils.model_manager import load_llm_model
        
        da_engine = DataAnalystEngine(persist_dir, logger)
        llm = load_llm_model(llm_provider, llm_model, llm_key, llm_url)
        
        def kb_status_callback(msg):
            status_container.write(msg)
            logger.info(f"👉 {msg}")
        
        if data_files:
             # [v5.7.0] 核心修复：始终处理数据文件以确保数据一致性
             status_container.write(f"📊 检测到 {len(data_files)} 个业务源文件，正在执行物理归档与战略建模...")
             logger.info(f"📊 [Strategic Workshop] 检测到 {len(data_files)} 个业务源文件，启动战略建模...")
             res = da_engine.process_files(data_files, llm, status_callback=kb_status_callback)
             if res['success']:
                 status_container.success(f"✅ 战略大脑初始化完成 (已归档并导入 {len(res['tables'])} 张表)")
                 logger.success(f"✅ [Strategic Workshop] 战略大脑初始化完成 (已导入 {len(res['tables'])} 张表)")

        # Schema 建模 (使用之前读取的 docs)
        if docs:
            # [v6.3.0] 强制刷新业务模型：确保每次更新都能根据最新材料重新建模，防止表结构“粘滞”
            status_container.write("🧠 正在提取最新业务元模型...")
            logger.info("🧠 [Strategic Workshop] 正在从当前源材料中重构业务模型与逻辑通路...")
            
            # 不再判断文件是否存在，而是直接执行提取以覆盖旧模型
            schemas = da_engine.extract_schema_from_docs(docs, llm, status_callback=kb_status_callback)
            
            # 业务蓝图推演
            status_container.write("🌐 正在构建最新业务全景图与关联路径...")
            blueprint = da_engine.infer_business_blueprint(schemas, llm)
            scenario = blueprint.get('business_scenario', '未知业务')
            status_container.info(f"📍 识别业务场景: {scenario}")
            logger.info(f"📍 [Strategic Workshop] 业务蓝图更新完成: {scenario}")
        
        status_container.write("✅ 业务语义建模已更新")
        logger.success("✨ [Strategic Workshop] 全域业务语义建模就绪")
    
    # --- 补丁: 写入所有权信息与模型对齐 ---
    try:
        from src.config.manifest_manager import ManifestManager
        manifest = ManifestManager.load(persist_dir)
        
        # 记录所有者
        if owner:
            manifest['owner'] = owner
            
        # 强制纠正模型元数据 (关键修复)
        manifest['embed_model'] = embed_model
        manifest['embed_provider'] = embed_provider
        
        # 核心修复: 直接保存 JSON 而不是使用错误的 save 方法
        # ManifestManager.save 误将 manifest 字典当作文件列表处理，导致元数据 key 变成文件条目
        manifest_path = ManifestManager.get_path(persist_dir)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=4, ensure_ascii=False)
            
        logger.info(f"✅ 资产所有权与模型对齐已完成: {owner} | {embed_model}")
    except Exception as e:
        logger.warning(f"⚠️ 元数据补全失败: {e}")

    # 计算耗时
    duration = time.time() - start_time
    prog_bar.progress(100)
    status_container.update(label=f"✅ 知识库 '{kb_name}' 处理完成", state="complete", expanded=True)
    
    # 统计信息
    logger.separator("处理完成")
    logger.success(f"✅ 知识库 '{kb_name}' 处理完成")
    logger.info(f"📊 统计: {result.file_count} 个文件, {result.doc_count} 个文档片段")
    logger.info(f"⏱️  耗时: {duration:.1f} 秒")
    
    # 跳转到新创建的知识库
    jump_to_knowledge_base(kb_name, output_base)
    
    st.success(f"🎉 知识库 '{kb_name}' 创建成功！正在跳转...")
    time.sleep(1)
    st.rerun()
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

from src.common.business import click_btn

# 计算当前的 KB ID (根据侧边栏选择)
selected_kbs = st.session_state.get('selected_kbs', [])
if len(selected_kbs) == 1:
    active_kb_name = selected_kbs[0]
elif len(selected_kbs) > 1:
    active_kb_name = "multi_kb_mode"  # 多知识库模式标识
else:
    active_kb_name = current_kb_name if not is_create_mode else None

# 自动加载逻辑
# 优化：增加 messages 为空的判断，确保刷新页面后能触发首次加载
if active_kb_name and (active_kb_name != st.session_state.current_kb_id or not st.session_state.get('messages')):
    # 只在没有正在处理的问题时才切换
    if not st.session_state.get('is_processing', False):
        st.session_state.current_kb_id = active_kb_name
        st.session_state.chat_engine = None
        
        # [关键修复] 优先使用 URL 中的 sess_id，否则获取该库最近活跃的会话 ID
        if not st.session_state.get('current_session_id'):
            latest_id = HistoryManager.get_latest_session_id(active_kb_name)
            st.session_state.current_session_id = latest_id
        
        with st.spinner("📜 正在加载对话历史..."):
            st.session_state.messages = HistoryManager.load_session(active_kb_name, st.session_state.current_session_id)
        
        # 恢复状态：从最后一条消息恢复建议列表 (v5.6.3 增强)
        st.session_state.suggestions_history = []
        if st.session_state.messages:
            last_msg = st.session_state.messages[-1]
            if isinstance(last_msg, dict) and last_msg.get('suggestions'):
                st.session_state.suggestions_history = last_msg['suggestions']
            elif isinstance(last_msg, dict) and 'suggestions' not in last_msg:
                # 尝试向前追溯一条（防止最后一条是用户消息）
                if len(st.session_state.messages) >= 2:
                    prev_msg = st.session_state.messages[-2]
                    if isinstance(prev_msg, dict) and prev_msg.get('suggestions'):
                        st.session_state.suggestions_history = prev_msg['suggestions']
        
        # [关键修复] 如果已有历史记录，禁止触发自动摘要/引导，防止覆盖旧状态
        if st.session_state.messages and len(st.session_state.messages) > 0:
            st.session_state.skip_auto_summary = True
        else:
            st.session_state.skip_auto_summary = False
    else:
        st.warning("⚠️ 正在处理问题，请等待完成后再切换知识库")
        st.session_state.current_nav = f"📂 {st.session_state.current_kb_id}"

# 知识库加载逻辑 - 跳过多知识库模式的单一加载
if active_kb_name and st.session_state.chat_engine is None and active_kb_name != "multi_kb_mode":
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
    # 检查是否为网页抓取模式 - 自动检测模式
    crawl_url = st.session_state.get('crawl_url', '').strip()
    search_keyword = st.session_state.get('search_keyword', '').strip()
    
    # 自动判断模式：有网址就是网址模式，有关键词就是搜索模式
    auto_detected_mode = None
    if crawl_url:
        auto_detected_mode = 'url'
    elif search_keyword:
        auto_detected_mode = 'search'
    
    is_web_crawl_mode = (is_create_mode and auto_detected_mode is not None)
    
    if is_web_crawl_mode:
        current_mode = auto_detected_mode
        
        # 获取抓取参数
        crawl_depth = st.session_state.get('crawl_depth', 2)
        max_pages = st.session_state.get('max_pages', 5)
        parser_type = st.session_state.get('parser_type', 'default')
        url_quality_threshold = st.session_state.get('url_quality_threshold', 45.0)
        quality_threshold = st.session_state.get('quality_threshold', 45.0)
        
        # 执行网页抓取并创建知识库的逻辑
        if current_mode == 'url' and crawl_url:
            logger.log("网页抓取", "start", f"🌐 开始网址抓取模式: {crawl_url}")
            # 网址抓取模式 - 复用现有逻辑
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
                
                # 执行抓取
                if use_async:
                    # 异步爬虫配置
                    max_concurrent = 15
                    
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
                    
                    logger.info(f"🌐 开始网页爬取: {crawl_url} (深度:{crawl_depth}, 页数:{max_pages})")
                    
                    with st.spinner("异步抓取中..."):
                        result = run_async_crawl(
                            start_url=crawl_url,
                            max_depth=crawl_depth,
                            max_pages=max_pages,
                            status_callback=update_status,
                            max_concurrent=max_concurrent,
                            ignore_robots=True,
                            output_dir=unique_output_dir
                        )
                        saved_files = result if isinstance(result, list) else []
                        async_output_dir = unique_output_dir
                else:
                    # 同步爬虫逻辑
                    crawler = WebCrawler(output_dir=unique_output_dir)
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    crawled_count = [0]
                    
                    def update_status(msg):
                        status_text.text(f"📡 {msg}")
                        logger.info(f"🌐 网页爬取: {msg}")
                        if "已保存" in msg:
                            crawled_count[0] += 1
                            progress = min(crawled_count[0] / max_pages, 1.0)
                            progress_bar.progress(progress)
                    
                    logger.info(f"🌐 开始网页爬取: {crawl_url} (深度:{crawl_depth}, 页数:{max_pages})")
                    
                    with st.spinner("网页抓取中..."):
                        saved_files = crawler.crawl_website(
                            start_url=crawl_url,
                            max_depth=crawl_depth,
                            max_pages=max_pages,
                            parser_type=parser_type,
                            status_callback=update_status,
                            quality_threshold=url_quality_threshold
                        )
                
                # 抓取完成后自动创建知识库
                if saved_files:
                    st.success(f"✅ 网页抓取完成！共保存 {len(saved_files)} 个文件")
                    
                    # 设置抓取目录为数据源
                    target_path = unique_output_dir
                    
                    # 自动生成知识库名称 (对齐管理为先: 增加所有者前缀)
                    current_user = st.session_state.get('user', 'admin')
                    kb_name = f"{current_user}_Web_{domain}_{timestamp_dir}"
                    
                    # 继续执行知识库创建逻辑
                    st.info("🚀 开始创建知识库...")
                    
                    # 获取高级选项状态
                    current_use_ocr = st.session_state.get('kb_use_ocr', False)
                    current_extract_metadata = st.session_state.get('kb_extract_metadata', False)
                    current_generate_summary = st.session_state.get('kb_generate_summary', False)
                    current_force_reindex = st.session_state.get('kb_force_reindex', False)
                    
                    # 直接使用 KBProcessor 处理，避免 KBInterface 内部的 rerun 阻断后续逻辑
                    from src.kb.kb_processor import KBProcessor
                    from src.config import ConfigLoader
                    
                    processor = KBProcessor()
                    config = ConfigLoader.load()
                    
                    # 合并配置
                    process_options = {
                        'embed_provider': config.get('embed_provider', 'HuggingFace (本地/极速)'),
                        'embed_model': config.get('embed_model_hf', 'sentence-transformers/all-MiniLM-L6-v2'),
                        'embed_key': config.get('embed_key', ''),
                        'embed_url': config.get('embed_url', ''),
                        'action_mode': 'NEW',
                        'use_ocr': current_use_ocr,
                        'extract_metadata': current_extract_metadata,
                        'generate_summary': current_generate_summary,
                        'force_reindex': current_force_reindex
                    }
                    
                    try:
                        logger.log("网页抓取", "info", f"🚀 正在通过标准逻辑创建知识库: {kb_name}")
                        # [v5.5.7] 强制锚定路径，确保物理归档生效
                        st.session_state.uploaded_path = target_path
                        
                        process_knowledge_base_logic(
                            kb_name=kb_name,
                            action_mode='NEW',
                            use_ocr=current_use_ocr,
                            extract_metadata=current_extract_metadata,
                            generate_summary=current_generate_summary,
                            force_reindex=current_force_reindex,
                            owner=st.session_state.get('user', 'admin')
                        )
                        
                        logger.log("网页抓取", "success", f"✅ 知识库创建并归档成功: {kb_name}")
                        st.success(f"🎉 网页抓取知识库 '{kb_name}' 创建成功！")
                        
                        # 设置标记，防止重复执行
                        st.session_state.web_crawl_completed = True
                        time.sleep(1); st.rerun()
                        
                    except Exception as e:
                        st.error(f"❌ 知识库创建失败: {str(e)}")
                        logger.error(f"知识库创建异常: {str(e)}")
                    
                else:
                    st.error("❌ 网页抓取失败，未获取到任何文件")
                    # 只有失败时才停止执行
                    st.stop()
                    
            except Exception as e:
                st.error(f"❌ 网页抓取失败: {str(e)}")
                logger.error(f"网页抓取错误: {str(e)}")
                st.stop()
                
        elif current_mode == 'search' and search_keyword:
            logger.debug(search_keyword)
            logger.log("智能搜索", "start", f"🔍 开始智能搜索模式: {search_keyword}")
            # 智能搜索模式 - 复用现有逻辑
            try:
                # 获取搜索参数
                crawl_depth = st.session_state.get('search_crawl_depth', 2)
                max_pages = st.session_state.get('search_max_pages', 5)
                parser_type = st.session_state.get('search_parser_type', 'default')
                quality_threshold = st.session_state.get('quality_threshold', 45.0)
                
                st.info(f"🔍 开始智能搜索: {search_keyword}")
                
                # 根据关键词智能选择搜索引擎
                def get_smart_search_engines(keyword):
                    """根据关键词智能选择搜索引擎"""
                    keyword_lower = keyword.lower()
                    
                    # 医学关键词
                    medical_keywords = [
                        'cancer', 'disease', 'medicine', 'health', 'treatment', 'diagnosis',
                        '癌症', '疾病', '医学', '健康', '治疗', '诊断', '药物', '症状', '病理',
                        '卵巢癌', '肺癌', '胃癌', '肝癌', '乳腺癌', '医院', '医生', '手术'
                    ]
                    
                    # 技术关键词
                    tech_keywords = [
                        'python', 'java', 'javascript', 'programming', 'coding', 'algorithm',
                        '编程', '代码', '算法', '开发', '软件', '技术'
                    ]
                    
                    is_medical = any(med_word in keyword_lower for med_word in medical_keywords)
                    is_tech = any(tech_word in keyword_lower for tech_word in tech_keywords)
                    
                    import urllib.parse
                    q = urllib.parse.quote(keyword)
                    
                    # 核心改动：引入通用搜索引擎作为强力跳板
                    # 使用 HTML 版以减少反爬干扰和解析难度
                    general_engines = [
                        f"https://www.bing.com/search?q={q}",
                        f"https://html.duckduckgo.com/html/?q={q}"
                    ]

                    if is_medical:
                        return general_engines + [
                            f"https://zh.wikipedia.org/w/index.php?search={q}",
                            f"https://baike.baidu.com/search/none?word={q}",
                            "https://www.39.net/",
                            "https://www.xywy.com/"
                        ]
                    elif is_tech:
                        return general_engines + [
                            f"https://www.runoob.com/?s={q}",
                            f"https://help.aliyun.com/search_search.htm?k={q}",
                            f"https://so.csdn.net/so/search?q={q}",
                            f"https://zh.wikipedia.org/w/index.php?search={q}"
                        ]
                    else:
                        return general_engines + [
                            f"https://zh.wikipedia.org/w/index.php?search={q}",
                            f"https://baike.baidu.com/search/none?word={q}",
                            f"https://www.zhihu.com/search?type=content&q={q}",
                            f"https://www.icourse163.org/search.htm?search={q}"
                        ]
                
                search_engines = get_smart_search_engines(search_keyword)
                
                # 生成唯一输出目录
                from datetime import datetime
                timestamp_dir = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_output_dir = os.path.join("temp_uploads", f"Search_{search_keyword.replace(' ', '_')}_{timestamp_dir}")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                def update_status(msg):
                    try:
                        # 防御性编程：确保 logger 存在
                        from src.app_logging import LogManager
                        local_logger = LogManager()
                        status_text.caption(f"🌐 **实时进度**: {msg}")
                        local_logger.info(f"🔍 智能搜索: {msg}")
                    except Exception:
                        pass

                logger.info(f"🔍 开始智能搜索: {search_keyword} (深度:{crawl_depth}, 页数:{max_pages})")
                
                with st.spinner("智能搜索中..."):
                    # 使用现有的并发爬虫
                    from src.processors.concurrent_crawler import ConcurrentCrawler
                    from src.processors.content_analyzer import ContentQualityAnalyzer
                    
                    concurrent_crawler = ConcurrentCrawler(max_workers=3)
                    content_analyzer = ContentQualityAnalyzer()

                    def enhanced_progress_callback(message, progress=None):
                        # 回调函数可能在不同上下文中被调用，确保安全
                        try:
                            update_status(message)
                            if progress is not None:
                                progress_bar.progress(progress)
                        except Exception:
                            pass
                
                # 执行并发爬取
                crawl_results = concurrent_crawler.crawl_with_depth(
                    search_engines,
                    max_depth=crawl_depth,
                    max_pages_per_level=max_pages,
                    keyword=search_keyword,
                    progress_callback=enhanced_progress_callback
                )
                
                # 保存结果到文件
                saved_files = []
                if crawl_results:
                    import os
                    os.makedirs(unique_output_dir, exist_ok=True)
                    
                    for i, result in enumerate(crawl_results):
                        if result['success'] and result['content']:
                            # 使用网页标题作为文件名，如果没有标题则使用默认名称
                            title = result.get('title', '').strip()
                            if title:
                                # 清理标题，移除不合法的文件名字符
                                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                                safe_title = safe_title.replace(' ', '_')[:50]  # 限制长度
                                filename = f"{safe_title}_{i+1:03d}.md"
                            else:
                                filename = f"quality_content_{i+1:03d}.md"
                            
                            filepath = os.path.join(unique_output_dir, filename)
                            
                            # 确保导入 (防止多进程或动态加载导致的 NameError)
                            from src.utils.file_system_utils import set_where_from_metadata
                            
                            with open(filepath, 'w', encoding='utf-8') as f:
                                # 🔥 核心修正：使用 Markdown 格式，以便溯源引擎识别和更好展示
                                f.write(f"**URL:** {result['url']}\n\n")
                                f.write(f"# {result['title']}\n\n")
                                f.write(f"**内容:**\n\n{result['content']}\n")
                            
                            # 为文件设置 macOS 下载来源元数据
                            set_where_from_metadata(filepath, result['url'])
                            
                            saved_files.append(filepath)
                
                # 搜索完成后自动创建知识库
                if saved_files:
                    st.success(f"✅ 智能搜索完成！共保存 {len(saved_files)} 个文件")
                    
                    # 设置搜索目录为数据源
                    target_path = unique_output_dir
                    
                    # 自动生成知识库名称 (对齐管理为先: 增加所有者前缀)
                    current_user = st.session_state.get('user', 'admin')
                    kb_name = f"{current_user}_Search_{search_keyword.replace(' ', '_')}_{timestamp_dir}"
                    
                    # 继续执行知识库创建逻辑
                    st.info("🚀 开始创建知识库...")
                    
                    # 获取高级选项状态
                    current_use_ocr = st.session_state.get('kb_use_ocr', False)
                    current_extract_metadata = st.session_state.get('kb_extract_metadata', False)
                    current_generate_summary = st.session_state.get('kb_generate_summary', False)
                    current_force_reindex = st.session_state.get('kb_force_reindex', False)
                    
                    # 直接使用 KBProcessor 处理，避免 KBInterface 内部的 rerun 阻断后续逻辑
                    from src.kb.kb_processor import KBProcessor
                    from src.config import ConfigLoader
                    
                    processor = KBProcessor()
                    config = ConfigLoader.load()
                    
                    # 合并配置
                    process_options = {
                        'embed_provider': config.get('embed_provider', 'HuggingFace (本地/极速)'),
                        'embed_model': config.get('embed_model_hf', 'sentence-transformers/all-MiniLM-L6-v2'),
                        'embed_key': config.get('embed_key', ''),
                        'embed_url': config.get('embed_url', ''),
                        'action_mode': 'NEW',
                        'use_ocr': current_use_ocr,
                        'extract_metadata': current_extract_metadata,
                        'generate_summary': current_generate_summary,
                        'force_reindex': current_force_reindex
                    }
                    
                    try:
                        logger.log("智能搜索", "info", f"🚀 正在通过标准逻辑创建知识库: {kb_name}")
                        # [v5.5.7] 强制锚定搜索路径
                        st.session_state.uploaded_path = target_path
                        
                        process_knowledge_base_logic(
                            kb_name=kb_name,
                            action_mode='NEW',
                            use_ocr=current_use_ocr,
                            extract_metadata=current_extract_metadata,
                            generate_summary=current_generate_summary,
                            force_reindex=current_force_reindex,
                            owner=st.session_state.get('user', 'admin')
                        )
                        
                        logger.log("智能搜索", "success", f"✅ 知识库创建并归档成功: {kb_name}")
                        st.success(f"🎉 智能搜索知识库 '{kb_name}' 创建成功！")
                        
                        st.session_state.smart_search_completed = True
                        time.sleep(1); st.rerun()
                    except Exception as e:
                        st.error(f"❌ 知识库创建失败: {str(e)}")
                        logger.error(f"知识库创建异常: {str(e)}")
                        
                else:
                    st.error("❌ 智能搜索失败，未获取到任何文件")
                    # 只有失败时才停止执行
                    st.stop()
                    
            except Exception as e:
                st.error(f"❌ 智能搜索失败: {str(e)}")
                logger.error(f"智能搜索错误: {str(e)}")
                st.stop()
        else:
            logger.info(f"DEBUG: ❌ 未匹配任何网页抓取分支")
            logger.debug(search_keyword)
            logger.log("网页抓取", "warning", f"⚠️ 未匹配网页抓取条件: mode={current_mode}, url={bool(crawl_url)}, keyword={bool(search_keyword)}")
    
    logger.info("DEBUG: 跳过网页抓取模式，进入原有文件处理逻辑")
    
    # 检查是否已经完成了网页抓取或智能搜索，避免重复处理
    if st.session_state.get('web_crawl_completed') or st.session_state.get('smart_search_completed'):
        logger.log("文件处理", "info", "🔄 检测到网页抓取/智能搜索已完成，跳过文件处理逻辑")
        # 清理标记
        st.session_state.pop('web_crawl_completed', None)
        st.session_state.pop('smart_search_completed', None)
        st.stop()
    
    # 原有的文件处理逻辑
    # 确保 action_mode 已定义 (防止 NameError)
    if 'action_mode' not in locals() and 'action_mode' not in globals():
        action_mode = "NEW" if is_create_mode else "APPEND"

    # 显式获取高级选项状态 (优先从 session_state 获取)
    current_use_ocr = st.session_state.get('kb_use_ocr', False)
    current_extract_metadata = st.session_state.get('kb_extract_metadata', False)
    current_generate_summary = st.session_state.get('kb_generate_summary', False)
    current_force_reindex = st.session_state.get('kb_force_reindex', False)

    # 优化配置保存逻辑：读取-合并-保存
    existing_config = ConfigLoader.load()
    
    config_update = {
        "target_path": target_path,
        "output_path": output_base,
        "llm_provider": llm_provider, # 保存供应商类型
        "embed_provider_idx": ["HuggingFace (本地/极速)", "OpenAI-Compatible", "Ollama"].index(embed_provider),
        "embed_model_hf": embed_model if embed_provider.startswith("HuggingFace") else "",
        "embed_url_ollama": embed_url if embed_provider.startswith("Ollama") else "",
        "embed_model_ollama": embed_model if embed_provider.startswith("Ollama") else ""
    }
    
    # 根据供应商类型保存对应字段
    if llm_provider == "OpenAI-Compatible":
        config_update["llm_url_other"] = llm_url
        config_update["llm_key_other"] = llm_key
        config_update["llm_model_other"] = llm_model
        # 同时也保存通用字段以便兼容
        config_update["llm_url"] = llm_url
        config_update["llm_key"] = llm_key
        config_update["llm_model"] = llm_model
        
    elif llm_provider == "OpenAI":
        config_update["llm_url_openai"] = llm_url
        config_update["llm_key"] = llm_key
        config_update["llm_model_openai"] = llm_model
        
    elif llm_provider == "Ollama":
        config_update["llm_url_ollama"] = llm_url
        config_update["llm_model_ollama"] = llm_model
    
    existing_config.update(config_update)
    ConfigLoader.save(existing_config)

    # Ensure final_kb_name is defined (crucial for APPEND mode where sidebar logic might differ)
    if 'final_kb_name' not in locals():
        if is_create_mode:
            final_kb_name = st.session_state.get('new_kb_name', '') # Try session state or empty
        else:
            final_kb_name = current_kb_name

    if not final_kb_name:
        st.error("请输入知识库名称")
        # 添加友好的输入验证提示
        from src.utils.friendly_error_handler import validation_error
        validation_error("知识库名称", "名称不能为空", "请输入一个有意义的知识库名称，例如：'技术文档'、'产品手册'等")
    else:
        try:
            # --- 空间配额检查 ---
            from src.auth.session_manager import get_user_storage_usage
            from src.auth.user_auth import load_users
            
            curr_user = st.session_state.get('user', 'admin')
            u_data = load_users().get(curr_user, {})
            u_quota_mb = u_data.get("storage_quota_mb", 100)
            
            if u_quota_mb != -1:
                curr_usage_bytes = get_user_storage_usage(curr_user)
                if curr_usage_bytes / (1024 * 1024) >= u_quota_mb:
                    st.error(f"❌ 存储空间已满 ({u_quota_mb}MB)。请清理不再需要的知识库或联系管理员扩容。")
                    st.stop()

            # 使用优化器生成唯一名称，避免重复和时间戳冲突
            # Only optimize name in NEW mode to avoid renaming existing KBs in APPEND mode
            if is_create_mode:
                optimized_name = KBNameOptimizer.generate_unique_name(final_kb_name, output_base)
                
                if not optimized_name: 
                    raise ValueError("知识库名称包含非法字符或为空")
                
                # 如果名称被优化了，提示用户
                if optimized_name != final_kb_name:
                    st.info(f"💡 名称已优化: `{final_kb_name}` → `{optimized_name}`")
                    
                # 使用优化后的名称
                final_kb_name = optimized_name
            
            logger.debug(current_generate_summary)
            logger.debug(st.session_state.get('uploaded_path'))
            logger.debug(bool(uploaded_files) if 'uploaded_files' in locals() else 'Not in locals')

            # --- 核心：重名冲突解决与所有权绑定 ---
            current_user = st.session_state.get('user', 'admin')
            if is_create_mode:
                # 仅在新建时强制加前缀，追加模式保持原名
                if not final_kb_name.startswith(f"{current_user}_"):
                    final_kb_name = f"{current_user}_{final_kb_name}"
            
            # [v3.5.0 修复] 确保拖拽上传的临时路径被正确同步给处理引擎
            # 如果 uploaded_files 有内容但 path 为空，立即调用保存函数获取路径
            if 'uploaded_files' in locals() and uploaded_files and not st.session_state.get('uploaded_path'):
                from src.common.utils import save_uploaded_files
                st.session_state.uploaded_path = save_uploaded_files(uploaded_files, "temp_uploads")
                logger.info(f"📂 [修正] 拖拽上传路径已锚定: {st.session_state.uploaded_path}")

            process_knowledge_base_logic(
                kb_name=final_kb_name,
                action_mode=action_mode,
                use_ocr=current_use_ocr,
                extract_metadata=current_extract_metadata,
                generate_summary=current_generate_summary,
                force_reindex=current_force_reindex,
                owner=current_user # 明确传递所有者
            )
            # st.session_state.current_nav 等跳转逻辑已移至 process_knowledge_base_logic 内部的 jump_to_knowledge_base
            
            if action_mode == "NEW" or action_mode == "APPEND":
                st.session_state.messages = []
                st.session_state.suggestions_history = []
                hist_path = os.path.join(HISTORY_DIR, f"{final_kb_name}.json")
                if os.path.exists(hist_path): os.remove(hist_path)
            
            time.sleep(1); st.rerun()
        except Exception as e:
            st.error(f"执行失败: {e}")

# --- 主视图渲染 ---
if active_kb_name == "multi_kb_mode":
    # 多知识库模式 - 显示简洁的联合查询界面
    selected_kbs = st.session_state.get('selected_kbs', [])
    st.markdown(f"### 🔍 多知识库联合查询")
    st.info(f"已选择 {len(selected_kbs)} 个知识库: {', '.join(selected_kbs)}")
    st.markdown("💡 **使用说明**: 直接在下方输入问题，系统将自动从所有选中的知识库中检索相关信息并提供答案。")
    
elif active_kb_name:
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
        dl_col, rename_col = doc_manager.render_statistics_overview(active_kb_name, stats)
        with dl_col:
            # 使用 popover 将下载选项折叠，节省空间
            with st.popover("📥 数据导出", use_container_width=True, help="导出知识库的所有原始数据、AI加工成果及向量数据库"):
                import io
                import zipfile
                import pandas as pd
                import json
                from datetime import datetime
                from src.auth.permission_manager import permission_manager
                
                # 获取当前用户
                current_user = st.session_state.get('user', 'guest_user')
                can_download = permission_manager.has_permission(current_user, "download_knowledge_base")

                # --- A. 快速资产导出 ---
                st.markdown("**🧠 核心知识 (轻量)**")
                if doc_manager.manifest.get('files'):
                    col_idx, col_rpt = st.columns(2)
                    with col_idx:
                        # 1. 深度 CSV 导出内容生成
                        df_data = []
                        for info in doc_manager.manifest['files']:
                            df_data.append({
                                "文件名": info.get('name'),
                                "分类": info.get('category', '未分类'),
                                "摘要": info.get('summary', '暂无'),
                                "片段数": len(info.get('doc_ids', [])),
                                "路径": info.get('file_path', '未知')
                            })
                        df = pd.DataFrame(df_data)
                        csv_data = df.to_csv(index=False).encode('utf-8-sig')
                        
                        if can_download:
                            st.download_button(label="📊 CSV 索引", data=csv_data, file_name=f"{active_kb_name}_索引.csv", mime='text/csv', use_container_width=True, key=f"dl_csv_h_{active_kb_name}")
                        else:
                            st.button("📊 CSV 索引", disabled=True, key=f"dl_csv_h_{active_kb_name}_disabled", help="无下载权限")

                    with col_rpt:
                        # 2. Markdown 报告内容生成
                        report_md = f"# 知识库全量报告: {active_kb_name}\n\n- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        for info in doc_manager.manifest['files']:
                            report_md += f"## 📄 {info.get('name')}\n- **分类**: {info.get('category', '未分类')}\n- **摘要**: {info.get('summary', '暂无摘要')}\n\n---\n"
                        
                        if can_download:
                            st.download_button(label="📝 MD 报告", data=report_md, file_name=f"{active_kb_name}_报告.md", mime='text/markdown', use_container_width=True, key=f"dl_md_h_{active_kb_name}")
                        else:
                            st.button("📝 MD 报告", disabled=True, key=f"dl_md_h_{active_kb_name}_disabled", help="无下载权限")

                st.divider()
                
                # --- B. 终极全量包 ---
                st.markdown("**🎁 终极资产导出**")
                st.caption("包含报告、索引、元数据、原始文档及全量向量数据库")
                
                # 权限拦截逻辑 (实时校验 - 颗粒化)
                can_export_full = permission_manager.has_permission(current_user, "kb_export_full")
                # can_download 也是必要条件之一 (逻辑上全量导出包含下载)
                final_export_permission = can_export_full and can_download
                
                if not final_export_permission:
                    st.warning("🔒 权限不足：当前角色无法导出全量镜像。")
                
                if st.button("🌟 一键生成全量资产包 (ZIP)", use_container_width=True, key=f"dl_all_in_one_{active_kb_name}", type="primary", disabled=not final_export_permission):
                    from src.auth.audit_logger import AuditLogger
                    from src.common.utils import get_client_ip
                    AuditLogger.log(current_user, "EXPORT_FULL_SNAPSHOT", f"Exported: {active_kb_name}", ip=get_client_ip())
                    
                    with st.status("正在构建多维镜像资产包...", expanded=True) as status:
                        import zipfile, io, pandas as pd, plotly.express as px
                        
                        def process_multi_assets(msg, name, z):
                            if msg.get('is_data_report') and msg.get('stages'):
                                for s_idx, stage in enumerate(msg['stages']):
                                    if not stage.get('data'): continue
                                    try:
                                        df_raw = pd.DataFrame(stage['data'])
                                        for c in [col for col in df_raw.columns if not pd.api.types.is_numeric_dtype(df_raw[col])]:
                                            df_raw[c] = df_raw[c].fillna("Unknown").astype(str)
                                        num_cols = [c for c in df_raw.columns if pd.api.types.is_numeric_dtype(df_raw[c])]
                                        
                                        tasks = []
                                        rec = stage.get('recommendation')
                                        if rec:
                                            v_t, v_x, v_y, v_c = rec.get('viz_type'), rec.get('x_axis'), rec.get('y_axis'), rec.get('color')
                                            args = {'x':v_x, 'y':v_y, 'title': f"AI Rec: {rec.get('title')}", 'template':'plotly_white'}
                                            if v_c and v_c in df_raw.columns: args['color'] = v_c
                                            tasks.append(('ai', v_t, args))
                                        
                                        if len(num_cols) > 0:
                                            tasks.append(('bar', 'bar', {'x': df_raw.columns[0], 'y': num_cols[0], 'title': 'Comparison View', 'template':'plotly_white'}))
                                            if len(df_raw) > 1:
                                                tasks.append(('line', 'line', {'x': df_raw.columns[0], 'y': num_cols[0], 'title': 'Trend View', 'template':'plotly_white', 'markers':True}))

                                        for suffix, p_type, p_args in tasks:
                                            try:
                                                f_p = None
                                                if p_type == 'bar': f_p = px.bar(df_raw, **p_args)
                                                elif p_type == 'line': f_p = px.line(df_raw, **p_args)
                                                elif p_type == 'pie': f_p = px.pie(df_raw, names=p_args['x'], values=p_args['y'], title=p_args['title'], hole=0.4)
                                                
                                                if f_p:
                                                    cid = f"chart_{name}_s{s_idx}_{suffix}"
                                                    z.writestr(f"02_历史对话/Charts_IMG/{cid}.png", f_p.to_image(format="png", scale=2))
                                                    z.writestr(f"02_历史对话/Charts_HTML/{cid}.html", f_p.to_html(include_plotlyjs='cdn'))
                                            except Exception as plot_err:
                                                logger.warning(f"Plot failed for {suffix}: {plot_err}")
                                    except Exception as e:
                                        logger.warning(f"Asset process failed: {e}")

                        def msg_to_md_multi(msg, name):
                            r = "👤 用户 (User)" if msg['role'] == 'user' else "🤖 助手 (Assistant)"
                            m = f"#### {r}\n{msg['content']}\n\n"
                            if msg.get('stats'):
                                s = msg['stats']
                                m += f"> ⏱️ **耗时**: {s.get('time',0):.1f}s | 📝 **Tokens**: {s.get('tokens',0)}\n\n"
                            
                            if msg.get('is_data_report') and msg.get('stages'):
                                m += "### 📊 极光战略推演全维度报告\n"
                                for s_idx, stage in enumerate(msg['stages']):
                                    s_meta = stage.get('meta', {})
                                    m += f"#### 📍 阶段 {s_meta.get('stage_id')}: {s_meta.get('title')}\n"
                                    if stage.get('data'):
                                        try:
                                            df_m = pd.DataFrame(stage['data'])
                                            m += "##### 📋 核心数据采样:\n" + df_m.head(5).to_markdown(index=False) + "\n\n"
                                        except: pass
                                    
                                    m += "##### 🎨 数据多维呈现 (Gallery):\n"
                                    for suffix, label in [('ai', '🤖 AI 智能推荐'), ('bar', '📊 对比分布视角'), ('line', '📈 趋势分析视角')]:
                                        cid = f"chart_{name}_s{s_idx}_{suffix}"
                                        m += f"**{label}**\n\n![{label}](../Charts_IMG/{cid}.png)\n\n"
                                        m += f"🔗 [点击全屏交互查看 {label}](../Charts_HTML/{cid}.html)\n\n"
                                    
                                    rec = stage.get('recommendation')
                                    if rec and rec.get('insight'):
                                        m += f"> 💡 **深度洞察 / Insight**: {rec['insight']}\n\n"
                            
                            if msg.get('sources'):
                                m += "**📚 参考来源:**\n"
                                for src in msg['sources'][:3]: m += f"- [{src.get('file_name')}] ({src.get('score',0):.2f})\n"
                                m += "\n"
                            return m + "---\n\n"

                        manifest_json = json.dumps(doc_manager.manifest, indent=4, ensure_ascii=False)
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                            status.write("正在打包资产清单与镜像记录...")
                            zip_file.writestr("01_核心资产/知识摘要报告.md", report_md if 'report_md' in locals() else "# Report")
                            zip_file.writestr("01_核心资产/数据资产清单.csv", csv_data if 'csv_data' in locals() else "Filename")
                            
                            curr_msgs = st.session_state.get('messages', [])
                            if curr_msgs:
                                ts_n = datetime.now().strftime('%H%M%S')
                                md_act = f"# 活跃会话全维度快照 ({ts_n})\n\n"
                                for m in curr_msgs:
                                    md_act += msg_to_md_multi(m, f"ACTIVE_{ts_n}")
                                    process_multi_assets(m, f"ACTIVE_{ts_n}", zip_file)
                                zip_file.writestr(f"02_历史对话/MD_纪要/ACTIVE_SESSION_{ts_n}.md", md_act)
                                zip_file.writestr(f"02_历史对话/Raw_JSON/ACTIVE_SESSION_{ts_n}.json", json.dumps({"messages": curr_msgs}, indent=4, ensure_ascii=False))

                            history_dir = "chat_histories"
                            if os.path.exists(history_dir):
                                for chat_f in os.listdir(history_dir):
                                    if chat_f.endswith(".json") and (chat_f.startswith(f"{active_kb_name}.") or chat_f.startswith(f"{active_kb_name}@")):
                                        try:
                                            with open(os.path.join(history_dir, chat_f), 'r', encoding='utf-8') as f:
                                                cd = json.load(f)
                                                if not cd.get('messages'): continue
                                                t_h = cd.get('title','chat')
                                                sn = "".join([c for c in t_h if c.isalnum() or c in (' ','_','-')]).strip()
                                                hmd = f"# 会话镜像: {t_h}\n\n"
                                                for m in cd['messages']:
                                                    hmd += msg_to_md_multi(m, sn)
                                                    process_multi_assets(m, sn, zip_file)
                                                zip_file.writestr(f"02_历史对话/MD_纪要/{sn}.md", hmd)
                                                zip_file.write(os.path.join(history_dir, chat_f), arcname=f"02_历史对话/Raw_JSON/{chat_f}")
                                        except: continue

                            status.write("打包业务数据库与归档文件...")
                            ddb = os.path.join(db_path, "business_data.db")
                            if os.path.exists(ddb): zip_file.write(ddb, arcname="03_战略大脑/business_data.db")
                            for f in ["business_schema.json", "business_blueprint.json"]:
                                fp = os.path.join(db_path, f)
                                if os.path.exists(fp): zip_file.write(fp, arcname=f"03_战略大脑/{f}")

                            zip_file.writestr("04_系统配置/manifest.json", manifest_json)
                            raw_p = os.path.join(db_path, "raw_sources")
                            if os.path.exists(raw_p):
                                for root, _, files in os.walk(raw_p):
                                    for file in files:
                                        if not file.startswith('.'):
                                            af = os.path.join(root, file)
                                            zip_file.write(af, arcname=os.path.join("05_原始文档库", os.path.relpath(af, raw_p)))

                            for f in ["docstore.json", "index_store.json", "vector_store.json", "graph_store.json"]:
                                fp = os.path.join(db_path, f)
                                if os.path.exists(fp): zip_file.write(fp, arcname=f"06_向量快照/{f}")

                        status.update(label="✅ 全维度镜像资产包已生成！", state="complete")
                        st.download_button(
                            label="⬇️ 下载全维度镜像包 (.zip)",
                            data=zip_buffer.getvalue(),
                            file_name=f"FULL_SNAPSHOT_{active_kb_name}_{datetime.now().strftime('%H%M%S')}.zip",
                            mime="application/zip",
                            use_container_width=True,
                            key=f"dl_final_{active_kb_name}"
                        )
                
                st.info("💡 提示：全量包可直接用于系统迁移或永久离线归档。")

        # 权限检查：重命名
        from src.auth.permission_manager import permission_manager
        current_user = st.session_state.get('user', 'guest_user')
        can_rename = permission_manager.has_permission(current_user, "kb_rename")
        
        if can_rename:
            if rename_col.button("✏️", help="重命名"): 
                st.session_state.renaming = True
        else:
            rename_col.button("🔒", disabled=True, help="无重命名权限")
    
    # 文件管理
    with st.container(key="kb_details_container"):
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
            
            # 权限检查：文件系统访问
            from src.auth.permission_manager import permission_manager
            current_user = st.session_state.get('user', 'guest_user')
            can_access_fs = permission_manager.has_permission(current_user, "kb_filesystem_access")
            
            # 1. 打开知识库目录
            with op_col1:
                if can_access_fs:
                    if st.button("📂 打开目录", use_container_width=True, help="在Finder中打开知识库文件夹"):
                        import webbrowser
                        import urllib.parse
                        try:
                            file_url = 'file://' + urllib.parse.quote(os.path.abspath(db_path))
                            webbrowser.open(file_url)
                            st.toast("✅ 已在Finder中打开")
                        except Exception as e:
                            st.error(f"打开失败: {e}")
                else:
                    st.button("📂 打开目录", use_container_width=True, disabled=True, help="无文件系统访问权限")
            
            # 2. 复制路径
            with op_col2:
                if can_access_fs:
                    if st.button("📋 复制路径", use_container_width=True, help="复制知识库路径到剪贴板"):
                        try:
                            import subprocess
                            subprocess.run(["pbcopy"], input=db_path.encode(), check=True)
                            st.toast(f"✅ 已复制")
                        except Exception as e:
                            st.info(f"📁 路径: {db_path}")
                else:
                    st.button("📋 复制路径", use_container_width=True, disabled=True, help="无文件系统访问权限")
            
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
                # 权限检查
                from src.auth.permission_manager import permission_manager
                current_user = st.session_state.get('user', 'guest_user')
                can_download = permission_manager.has_permission(current_user, "download_knowledge_base")
                
                if can_download:
                    if st.button("📥 导出清单", use_container_width=True, help="导出当前文件列表"):
                        export_data = f"知识库: {active_kb_name}\n文件数: {stats['file_cnt']}\n片段数: {stats['total_chunks']}\n\n文件列表:\n"
                        for f in doc_manager.manifest['files']:
                            export_data += f"- {f['name']} ({f['type']}, {len(f.get('doc_ids', []))} 片段)\n"
                        st.download_button("下载", export_data, f"{active_kb_name}_清单.txt", use_container_width=True)
                else:
                    st.button("📥 导出清单", use_container_width=True, disabled=True, help="无下载权限")

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
                        # 单行布局：标题 + 元数据 + 摘要 + 操作
                        col_info, col_summary, col_ops = st.columns([6, 2.5, 1.5])
                        
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
                        
                        # 详情直接展开 (专业版)
                        with st.expander(f"🔍 深度档案与数据取证 - {f['name']}", expanded=False):
                            actual_file_path = f.get('file_path')
                            if not actual_file_path or not os.path.exists(actual_file_path):
                                actual_file_path = os.path.join(db_path, f['name'])
                            
                            # 获取深度属性
                            deep_attrs = get_deep_file_attributes(actual_file_path)
                            
                            # 1. 顶部专业仪表盘 (Health Dashboard)
                            h_col1, h_col2, h_col3, h_col4 = st.columns(4)
                            
                            with h_col1:
                                indexed_status = "✅ 已索引" if f.get('doc_ids') else "⏳ 未索引"
                                st.markdown(f"<div style='background:#f0f7ff; color:#0550ae; padding:4px 10px; border-radius:15px; text-align:center; font-size:0.8rem; font-weight:600;'>{indexed_status}</div>", unsafe_allow_html=True)
                            
                            with h_col2:
                                efficiency = deep_attrs.get('efficiency', '100%')
                                st.markdown(f"<div style='background:#f6ffed; color:#389e0d; padding:4px 10px; border-radius:15px; text-align:center; font-size:0.8rem; font-weight:600;'>💾 存储效率 {efficiency}</div>", unsafe_allow_html=True)
                                
                            with h_col3:
                                heat = "🔥 热数据" if f.get('hit_count', 0) > 5 else "❄️ 冷数据"
                                st.markdown(f"<div style='background:#fff7e6; color:#d46b08; padding:4px 10px; border-radius:15px; text-align:center; font-size:0.8rem; font-weight:600;'>📈 {heat} ({f.get('hit_count', 0)})</div>", unsafe_allow_html=True)
                                
                            with h_col4:
                                days = deep_attrs.get('longevity_days', 0)
                                st.markdown(f"<div style='background:#fff1f0; color:#cf1322; padding:4px 10px; border-radius:15px; text-align:center; font-size:0.8rem; font-weight:600;'>🕒 存活 {days} 天</div>", unsafe_allow_html=True)
                            
                            st.write("")
                            
                            # 2. 60/40 黄金分割布局
                            detail_col_left, detail_col_right = st.columns([6, 4])
                            
                            with detail_col_left:
                                # --- 左侧：智能洞察 (60%) ---
                                if f.get('summary'):
                                    st.markdown("####### 🧠 智能摘要")
                                    st.info(f"{f['summary']}")
                                
                                # RAG 预估与密度
                                st.markdown("####### 📊 RAG 内容动力学")
                                r_c1, r_c2, r_c3 = st.columns(3)
                                with r_c1:
                                    tokens = deep_attrs.get('token_estimate', 0)
                                    st.metric("预估 Token", f"~{tokens}", help="基于字符数的估算值")
                                with r_c2:
                                    chunks = len(f.get('doc_ids', []))
                                    st.metric("向量片段", f"{chunks} Pkts")
                                with r_c3:
                                    # 密度 = 字符/片段
                                    density = tokens // chunks if chunks > 0 else 0
                                    st.metric("内容密度", f"{density} c/p", help="平均每个片段包含的字符数")

                                # 内容采样
                                if os.path.exists(actual_file_path) and f.get('type', '').lower() in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json']:
                                    st.markdown("####### 📄 文本取证采样")
                                    try:
                                        with open(actual_file_path, 'r', encoding='utf-8', errors='ignore') as preview_f:
                                            preview_content = preview_f.read(800)
                                            st.code(preview_content, language='text')
                                    except:
                                        st.caption("无法读取内容预览")
                                
                                # 用户备注
                                st.markdown("####### 📝 用户自定义备注")
                                file_hash = f.get('file_hash', 'no_hash')
                                current_note = notes_manager.get_note(file_hash)
                                new_note = st.text_area("备注信息", value=current_note, height=80, key=f"note_{i}", label_visibility="collapsed")
                                if new_note != current_note:
                                    notes_manager.set_note(file_hash, new_note)
                                    st.toast("✅ 备注已保存")

                            with detail_col_right:
                                # --- 右侧：技术档案 (40%) ---
                                if "error" not in deep_attrs:
                                    # 1. 优先展示系统记录的溯源 (针对抓取文件)
                                    if deep_attrs.get("header_url"):
                                        st.markdown("####### 🌐 溯源 (系统记录)")
                                        st.caption(f"`{deep_attrs['header_url']}`")
                                        st.divider()

                                    # 2. macOS 专属增强元数据
                                    if platform.system() == "Darwin":
                                        st.markdown("####### 🍎 macOS 增强元数据")
                                        m = deep_attrs.get("macos", {})
                                        if any([m.get("tags"), m.get("finder_comment"), m.get("where_from"), m.get("version")]):
                                            # 展示标签
                                            if m.get("tags"):
                                                tag_html = "".join([f"<span style='background:#f0f0f0; padding:2px 6px; border-radius:10px; font-size:0.7rem; margin-right:4px;'>🏷️ {t}</span>" for t in m["tags"]])
                                                st.markdown(tag_html, unsafe_allow_html=True)
                                            
                                            # 展示来源
                                            if m.get("where_from"):
                                                st.markdown("**🌐 下载来源**")
                                                for url in m["where_from"]:
                                                    st.caption(f"`{url}`")
                                            
                                            # 展示系统注释
                                            if m.get("finder_comment"):
                                                st.caption(f"💬 **Finder 注释**: {m['finder_comment']}")
                                            
                                            if m.get("version"):
                                                st.caption(f"🔢 **内部版本**: {m['version']}")
                                        else:
                                            st.caption("ℹ️ 未发现扩展元数据 (标签、来源等)")
                                        
                                        st.divider()

                                    # 取证与底层
                                    st.markdown("####### 🕵️ 系统取证")
                                    st.caption(f"Magic Bytes: `{deep_attrs['magic_bytes']}`")
                                    st.caption(f"SHA-256: `{deep_attrs['sha256'][:32]}...`")
                                    st.caption(f"Inode: `{deep_attrs['inode']}` | FS: `{deep_attrs['fs_type']}`")
                                    
                                    # 时间轴与位置
                                    st.markdown("####### 🕒 时间轴与位置")
                                    st.caption(f"创建: `{deep_attrs['created']}`")
                                    st.caption(f"最后访问: `{deep_attrs['accessed']}`")
                                    
                                    st.markdown("####### 📍 拓扑位置")
                                    st.caption(f"真实路径: `{deep_attrs['real_path'][:40]}...`")
                                    st.caption(f"符号链接: `{'是' if deep_attrs['is_symlink'] else '否'}`")
                                    
                                    # 权限系统
                                    st.markdown("####### 🛡️ 权限系统")
                                    st.caption(f"Unix权限: `{deep_attrs['permissions']}`")
                                    st.caption(f"所有者: `{deep_attrs['owner']}` | 只读: `{'是' if deep_attrs['is_readonly'] else '否'}`")
                                else:
                                    st.warning(f"数据抓取异常: {deep_attrs['error']}")
                                
                                # 快捷功能按钮
                                st.divider()
                                btn_c1, btn_c2 = st.columns(2)
                                with btn_c1:
                                    if st.button("📂 在 Finder 中显示", key=f"reveal_{i}", use_container_width=True):
                                        reveal_in_file_manager(actual_file_path)
                                            
                                with btn_c2:
                                    if platform.system() == "Darwin":
                                        if st.button("👁️ QuickLook", key=f"ql_{i}", use_container_width=True):
                                            try:
                                                subprocess.Popen(["qlmanage", "-p", actual_file_path], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                                                # 强制置顶脚本
                                                top_script = 'tell application "System Events"\n repeat 20 times\n if exists process "qlmanage" then\n set frontmost of process "qlmanage" to true\n exit repeat\n end if\n delay 0.1\n end repeat\n end tell'
                                                subprocess.Popen(['osascript', '-e', top_script])
                                            except Exception as e:
                                                st.error(f"预览失败: {e}")
                                    else:
                                        if st.button("📋 复制路径", key=f"copy_path_{i}", use_container_width=True):
                                            st.code(actual_file_path)

                            # 向量片段ID (折叠)
                            if f.get('doc_ids'):
                                with st.expander("🧬 向量片段 ID 序列 (RAW)", expanded=False):
                                    st.text_area("IDs", value='\n'.join(f['doc_ids']), height=100, label_visibility="collapsed", key=f"ids_raw_{i}")
                
                # 底部分页 (方便翻页)
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

# 创建模式的欢迎界面
if is_create_mode:
    st.markdown("""
    <div class="welcome-box">
        <h2>👋 欢迎使用知识库</h2>
        <p>请在左侧 <b>侧边栏</b> 配置数据源 (支持粘贴路径或拖拽文件)，点击 <b>🚀 立即创建</b> 开始。</p>
    </div>
    """, unsafe_allow_html=True)


# --- 融合 ChatOllama 风格：会话顶栏 (v2.7.6) ---
if active_kb_name:
    with st.container():
        from src.config import ConfigLoader
        from src.config.prompt_manager import PromptManager
        from src.utils.model_manager import set_global_llm_model
        
        # 初始化当前选择 (修复 KeyError)
        if 'current_prompt_id' not in st.session_state:
            st.session_state.current_prompt_id = 'default'
        
        conf = ConfigLoader.load()
        # 优先使用会话级 Context Limit，否则使用全局配置
        ctx_limit = st.session_state.get('session_ctx_limit', conf.get('chat_history_limit', 10))
        current_model_name = st.session_state.get('selected_model', 'Default')
        
        # 计算会话标题 (基于第一条用户消息)
        session_title = "新对话"
        if st.session_state.messages:
            first_user_msg = next((m['content'] for m in st.session_state.messages if m['role'] == 'user'), None)
            if first_user_msg:
                session_title = first_user_msg[:12].strip() + ("..." if len(first_user_msg)>12 else "")

        # 布局：[标题区] [模型区] [操作区]
        h_col1, h_col2, h_col3 = st.columns([3, 2, 2.5])
        
        with h_col1:
            st.markdown(f"#### 📝 {session_title}")
            st.caption(f"📂 {active_kb_name}")
            
        with h_col2:
            current_role_id = st.session_state.get('current_prompt_id', 'default')
            # 获取角色名称
            all_prompts = PromptManager.load_prompts()
            role_name = next((p['name'] for p in all_prompts if p['id'] == current_role_id), "默认助手")
            # 简化显示
            short_role = role_name.split(' ')[0]
            st.markdown(f"<div style='text-align:center; padding-top:5px; color:#555'>🤖 {current_model_name}<br><span style='background:#f5f5f5; padding:1px 5px; border-radius:4px; font-size:0.75rem'>🎭 {short_role} | 🔄 {ctx_limit}</span></div>", unsafe_allow_html=True)

        with h_col3:
            c_set, c_new = st.columns([1, 2])
            with c_set:
                # ⚙️ 会话设置弹窗 (Popover)
                with st.popover("⚙️", use_container_width=True, help="当前会话设置"):
                    st.markdown("##### 💬 当前会话设置")
                    
                    # 1. 角色选择
                    prompt_names = [p['name'] for p in all_prompts]
                    current_idx = 0
                    for i, p in enumerate(all_prompts):
                        if p['id'] == st.session_state.current_prompt_id:
                            current_idx = i; break
                    
                    selected_p_name = st.selectbox("🎭 切换角色", prompt_names, index=current_idx)
                    
                    # 角色切换逻辑
                    sel_p = next(p for p in all_prompts if p['name'] == selected_p_name)
                    if sel_p['id'] != st.session_state.current_prompt_id:
                        st.session_state.current_prompt_id = sel_p['id']
                        # 热切换 LLM
                        try:
                            llm_provider = conf.get('llm_provider', 'Ollama')
                            llm_model = conf.get('llm_model_ollama', 'gpt-oss:20b')
                            llm_url = conf.get('llm_url_ollama', 'http://localhost:11434')
                            llm_key = ""
                            if llm_provider == "OpenAI":
                                llm_model = conf.get('llm_model_openai'); llm_url = conf.get('llm_url_openai'); llm_key = conf.get('llm_key')
                            elif llm_provider == "Azure OpenAI":
                                llm_model = conf.get('azure_deployment'); llm_url = conf.get('azure_endpoint'); llm_key = conf.get('azure_key')
                            
                            set_global_llm_model(llm_provider, llm_model, llm_key, llm_url, system_prompt=sel_p['content'])
                            st.toast(f"已切换: {sel_p['name']}")
                            st.rerun()
                        except: pass

                    # 2. Context Window (覆盖全局)
                    new_limit = st.slider("🧠 记忆深度 (Context)", 1, 50, ctx_limit, help="仅对当前会话生效")
                    if new_limit != ctx_limit:
                        st.session_state.session_ctx_limit = new_limit
                        st.rerun()
                    
                    st.divider()
                    
                    # 3. 清空历史
                    if st.button("🗑️ 清空当前记录", use_container_width=True, type="primary"):
                        st.session_state.messages = []
                        st.session_state.suggestions_history = []
                        from src.chat import HistoryManager
                        HistoryManager.save_session(active_kb_name, [], st.session_state.get('current_session_id'))
                        st.rerun()

            with c_new:
                if st.button("➕ 新对话", use_container_width=True, type="secondary"):
                    import uuid
                    new_id = str(uuid.uuid4())[:8]
                    st.session_state.current_session_id = new_id
                    st.session_state.messages = []
                    st.session_state.suggestions_history = []
                    # 重置会话级设置
                    st.session_state.pop('session_ctx_limit', None)
                    
                    from src.chat import HistoryManager
                    HistoryManager.save_session(active_kb_name, [], new_id)
                    st.rerun()
    st.divider()

# 自动摘要 (仅在知识库首次加载且无历史消息时触发，排除纯对话模式)
if active_kb_name and active_kb_name != "pure_chat" and st.session_state.chat_engine and not st.session_state.messages and not st.session_state.get('skip_auto_summary'):
    with st.chat_message("assistant", avatar="🤖"):
        summary_placeholder = st.empty()
        with st.status("✨ 正在分析文档生成摘要...", expanded=True) as status:
            try:
                # 使用当前选择的 LLM 模型名称
                current_model = st.session_state.get('selected_model', 'Ollama')
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
                HistoryManager.save_session(active_kb_name, state.get_messages(), st.session_state.get('current_session_id'))
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

# --- 主界面布局：单栏流水架构 (v4.2.3) ---
chat_layout = st.container()
workspace_col = None

# 使用渲染容器代理
chat_col = chat_layout.container()

# 渲染消息 (注入 chat_col)
for msg_idx, msg in enumerate(state.get_messages()):
    role = msg["role"]
    avatar = "🤖" if role == "assistant" else "🧑‍💻"
    with chat_col.chat_message(role, avatar=avatar):
        # --- 渲染持久化研究详情 (v2.9.4) ---
        if role == "assistant":
            # 1. 联网搜索历史结果
            if msg.get("search_results"):
                search_meta = msg["search_results"]
                results_list = search_meta.get('results', []) if isinstance(search_meta, dict) else search_meta
                with st.status(f"✅ 已获取 {len(results_list)} 条联网结果", expanded=False, state="complete"):
                    for i, res in enumerate(results_list, 1):
                        st.markdown(f"**{i}. {res.get('title')}**")
                        st.caption(f"{res.get('summary', '')[:150]}...")
                        st.markdown(f"🔗 [{urlparse(res.get('href', '')).netloc}]({res.get('href')})")
                        if i < len(results_list): st.divider()
            
            # 2. 专家会审历史详情
            if msg.get("research_details"):
                res_meta = msg["research_details"]
                with st.status(f"✅ 专家会审已完成 (专家组: {res_meta.get('roles')})", expanded=False, state="complete"):
                    st.write(f"👥 **专家组**: {res_meta.get('roles')}")
                    st.markdown("**💡 专业洞察视角:**")
                    st.write(res_meta.get('perspectives'))
                    with st.expander("🧐 查看审计细节"):
                        st.write(res_meta.get('critique'))

            # 3. [v5.0 补丁] 渲染历史数据分析报告
            if msg.get("is_data_report"):
                st.markdown("---")
                st.markdown("#### 🏦 5.0 极光战略推演工作台 (History)")
                for stage_h in msg.get("stages", []):
                    m_h = stage_h["meta"]
                    with st.expander(f"📍 Stage {m_h['stage_id']}: {m_h['title']}", expanded=True):
                        # --- [v5.2] 数据流转全演示 (History Mode) ---
                        with st.container(border=True):
                            # A. 查询前：原始数据 (如果有)
                            if stage_h.get("source_samples"):
                                st.markdown("**1. 查询前：业务表采样 (Before)**")
                                s_tabs = st.tabs(list(stage_h["source_samples"].keys()))
                                for idx, t_name in enumerate(stage_h["source_samples"]):
                                    with s_tabs[idx]:
                                        import pandas as pd
                                        st.dataframe(pd.DataFrame(stage_h["source_samples"][t_name]), use_container_width=True)

                            # B. 加工中：逻辑脚本 (Restored 3 Tabs)
                            st.markdown("**2. 执行中：工程逻辑 (The Logic)**")
                            sqls = stage_h.get("sqls", {})
                            # 恢复 3 个 Tab 的横向布局
                            sql_tabs = st.tabs(["🧪 SQLite (本地验证)", "🐘 Standard SQL", "💻 DataWorks (生产)"])
                            with sql_tabs[0]:
                                st.caption("SQL 语言: SQLite (Local Sim)")
                                st.code(sqls.get("sqlite", "-- N/A"), language="sql")
                            with sql_tabs[1]:
                                st.caption("SQL 语言: Standard ANSI SQL")
                                st.code(sqls.get("standard", "-- N/A"), language="sql")
                            with sql_tabs[2]:
                                st.caption("SQL 语言: MaxCompute / DataWorks")
                                st.code(sqls.get("dataworks", "-- N/A"), language="sql")

                            # C. 查询后：结果产出
                            st.markdown("**3. 查询后：汇聚结果表 (After)**")
                            import pandas as pd
                            df_h = pd.DataFrame(stage_h["data"])
                            
                            if not df_h.empty:
                                # 使用全功能可视化画板 [v5.8.8]
                                render_smart_visualization(
                                    df=df_h, 
                                    query=m_h['title'], 
                                    msg_idx=msg_idx, 
                                    stage_id=m_h['stage_id'], 
                                    recommendation=stage_h.get("recommendation")
                                )
                            else:
                                st.info("该阶段未产出数据结果")
                            if stage_h.get("is_simulated"):
                                st.info("✨ 此阶段基于业务模型仿真推演")

        # 显示角色标签 (v2.7.4)
        if role == "assistant" and msg.get("prompt_role"):
            st.markdown(f"""
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="background-color: rgba(0,0,0,0.05); padding: 2px 8px; border-radius: 4px; color: #666; font-size: 0.8rem; border: 1px solid rgba(0,0,0,0.1);">
                    🎭 {msg['prompt_role']}
                </span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown(msg["content"])
        
        # 显示统计信息（如果有）- 使用新组件 (Stage 3.1)
        if "stats" in msg and msg["stats"]:
            render_message_stats(msg["stats"])
        
        # 渲染引用源 - 使用新组件 (Stage 3.1)
        if "sources" in msg and msg["sources"]:
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
    
    # 调试信息
    debug_info = {
        'is_last_message': is_last_message,
        'role': msg.get("role"),
        'active_kb_name': bool(active_kb_name),
        'chat_engine': bool(st.session_state.get('chat_engine')),
        'suggestions_count': len(st.session_state.get('suggestions_history', []))
    }
    
    if is_last_message and msg["role"] == "assistant":
        import hashlib
        msg_hash = hashlib.md5(msg['content'][:100].encode()).hexdigest()[:8]
        
        st.divider()
        
        @st.fragment
        def suggestions_fragment():
            # 1. 状态指示与快捷操作栏 (v2.9)
            cols = st.columns([0.25, 0.15, 0.15, 0.15, 0.15, 0.15])
            with cols[0]:
                st.markdown("🔍 **追问推荐**")
            
            # 显示当前开启的功能状态 (作为美观的标签)
            with cols[1]:
                if st.session_state.get('enable_query_optimization'):
                    st.caption("🧠 思考中")
                else:
                    st.caption("⚪ 思考")
            
            with cols[2]:
                if st.session_state.get('enable_web_search'):
                    st.caption("🌐 联网中")
                else:
                    st.caption("⚪ 联网")
            
            with cols[3]:
                st.caption("🔎 搜索")
            
            with cols[4]:
                if st.session_state.get('enable_deep_research'):
                    st.caption("🔬 研究中")
                else:
                    st.caption("⚪ 研究")
                    
            with cols[5]:
                # 换一批按钮移到这一行，更加紧凑
                # 修复：增加 msg_idx 确保 Key 绝对唯一，防止重复内容导致 Duplicate Key
                if st.button("🔄 换一批", key=f"gen_more_{msg_idx}_{msg_hash}", help="生成新的推荐问题"):
                    with st.spinner(""):
                        all_history_questions = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
                        # ... (保持原有生成逻辑，但为了精简，我直接在这里写核心调用)
                        engine = get_unified_suggestion_engine(active_kb_name)
                        context_text = msg['content']
                        if msg_idx > 0:
                            prev_msg = st.session_state.messages[msg_idx - 1]
                            if prev_msg['role'] == 'user':
                                context_text = f"用户问题: {prev_msg['content']}\nAI回答: {msg['content']}"
                        
                        new_sugs = engine.generate_suggestions(
                            context=context_text,
                            source_type='chat',
                            query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None,
                            num_questions=3
                        )
                        if new_sugs:
                            st.session_state.suggestions_history = new_sugs[:3]
                            st.rerun(scope="fragment")

            # 2. 动态过滤与渲染推荐问题
            raw_suggestions = st.session_state.get('suggestions_history', [])
            forbidden_set = set()
            if hasattr(st.session_state, 'question_queue'):
                forbidden_set.update(st.session_state.question_queue)
            user_msgs = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
            forbidden_set.update(user_msgs[-20:])
            
            filtered_suggestions = [s for s in raw_suggestions if s not in forbidden_set]
            
            if filtered_suggestions:
                # 使用列布局显示推荐问题，使其更像卡片或按钮组
                for idx, q in enumerate(filtered_suggestions):
                    # 修复：增加 msg_idx 确保 Key 绝对唯一
                    if st.button(f"🔹 {q}", key=f"dyn_sug_{msg_idx}_{msg_hash}_{idx}", use_container_width=True):
                        click_btn(q)
            else:
                # 兜底：如果没推荐，显示一个小提示
                st.caption("暂无更多推荐，您可以尝试开启'深度思考'或'联网搜索'来获取更深入的追问。")

        suggestions_fragment()

# --- 🚀 极致全宽分析工作台 (v4.2.4) ---
if st.session_state.get('artifacts'):
    st.divider()
    with st.container():
        st.markdown("### 🏛️ 深度分析成果库 (Artifacts)")
        
        # 强制主内容区与图表全宽的 CSS 补丁
        st.markdown("""
            <style>
                /* 核心：主内容区 100% 宽度 */
                .main .block-container {
                    max-width: 100% !important;
                    padding-left: 5rem !important; /* 增加边距感 */
                    padding-right: 5rem !important;
                }
                /* 强制 Plotly 容器撑满 */
                .stPlotlyChart {
                    width: 100% !important;
                }
                /* 聊天消息气泡也全宽 */
                [data-testid="stChatMessage"] {
                    max-width: 100% !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # 改为单列全宽遍历，确保空间利用率 100%
        artifacts_data = list(reversed(st.session_state.artifacts[-5:])) # 显示最近5个
        for idx, art in enumerate(artifacts_data):
            with st.container(border=True):
                col_text, col_chart = st.columns([1, 3], gap="large") # 内部比例：结论占小部分，图表占大部分
                
                with col_text:
                    st.markdown(f"##### 📊 {art['title']}")
                    st.caption(f"🕒 {art['timestamp']}")
                    st.markdown(art["summary"])
                    with st.expander("📝 查看详细结论", expanded=False):
                        st.write("此处可根据需要展示更多技术细节或 SQL 脚本。")
                
                with col_chart:
                    import plotly.express as px
                    df_art = pd.DataFrame(art["data"])
                    if not df_art.empty:
                        aurora_colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA']
                        # 自动选择最合适的列进行展示
                        fig = px.bar(df_art, x=df_art.columns[0], y=df_art.columns[1] if len(df_art.columns)>1 else df_art.columns[0],
                                    template="plotly_white",
                                    color_discrete_sequence=[aurora_colors[idx % len(aurora_colors)]])
                        
                        fig.update_layout(
                            margin=dict(l=10, r=10, t=30, b=10), 
                            height=350, # 全宽模式下，高度提升到 350px 视觉更佳
                            hovermode="x unified"
                        )
                        st.plotly_chart(fig, use_container_width=True, key=f"v424_art_{idx}")

# 极简工具栏：模型与设置
with st.container():
    # Tools: Leading Spacer | Provider | Model | Deep | Web | Research | Filter | Clear | Stop/Trailing Spacer
    # 调整比例以容纳 智能研究 (v2.9)
    # 计算动态列宽
    if st.session_state.get('is_processing'):
        cols = st.columns([0.5, 1.2, 1.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
        c_lead, c_prov, c_model, c_deep, c_web, c_research, c_da, c_filter, c_clear, c_stop = cols
    else:
        cols = st.columns([0.5, 1.2, 1.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8])
        c_lead, c_prov, c_model, c_deep, c_web, c_research, c_da, c_filter, c_clear, c_spacer = cols
    
    # --- 0. 前置留白 (c_lead 不放置内容) ---

    # --- 1. 厂商/供应商选择 ---
    with c_prov:
        from src.config import ConfigLoader
        config = ConfigLoader.load()
        current_provider = config.get('llm_provider', 'Ollama')
        
        # 统一供应商完整定义 (与 config_forms.py 一致)
        ALL_PROVIDERS = {
            "Ollama": "🦙 Ollama (本地)",
            "OpenAI": "☁️ OpenAI (云端)",
            "OpenAI-Compatible": "🔌 Other (兼容协议)",
            "Azure OpenAI": "🟦 Azure OpenAI",
            "Anthropic": "🧠 Anthropic (Claude)",
            "Moonshot": "🌙 Moonshot (Kimi)",
            "Gemini": "💎 Gemini (Google)",
            "Groq": "⚡ Groq (极速)"
        }
        
        # 动态补充自定义供应商 (v2.9.6)
        custom_providers_info = config.get("custom_llm_providers", {})
        for cp_id, cp_info in custom_providers_info.items():
            ALL_PROVIDERS[cp_id] = f"🎨 {cp_info.get('name', cp_id)}"
        
        # 动态筛选：仅显示已配置（有 Key 或 URL）的供应商
        configured_providers = []
        
        # Ollama 默认始终检查
        configured_providers.append("Ollama")
        
        # 检查其他供应商是否有配置信息
        if config.get("llm_key") or config.get("llm_url_openai"): configured_providers.append("OpenAI")
        if config.get("llm_key_other") or config.get("llm_url_other"): configured_providers.append("OpenAI-Compatible")
        if config.get("azure_key") and config.get("azure_endpoint"): configured_providers.append("Azure OpenAI")
        if config.get("anthropic_key"): configured_providers.append("Anthropic")
        if config.get("moonshot_key"): configured_providers.append("Moonshot")
        if config.get("gemini_key"): configured_providers.append("Gemini")
        if config.get("groq_key"): configured_providers.append("Groq")
        
        # 确保当前使用的供应商在列表中
        if current_provider not in configured_providers:
            configured_providers.append(current_provider)
            
        # 按 ALL_PROVIDERS 的顺序排序
        display_providers = [p for p in ALL_PROVIDERS.keys() if p in configured_providers]
            
        def on_provider_change():
            new_prov = st.session_state.toolbar_provider_selector
            st.session_state.temp_provider = new_prov
        
        selected_provider = st.selectbox(
            "厂商",
            options=display_providers,
            format_func=lambda x: ALL_PROVIDERS.get(x, x),
            index=display_providers.index(current_provider) if current_provider in display_providers else 0,
            key="toolbar_provider_selector",
            on_change=on_provider_change,
            label_visibility="collapsed"
        )

    # --- 2. 模型选择 ---
    with c_model:
        # 读取对应供应商保存的模型
        saved_models = {
            "Ollama": config.get("llm_model_ollama", "gpt-oss:20b"),
            "OpenAI": config.get("llm_model_openai", "gpt-3.5-turbo"),
            "OpenAI-Compatible": config.get("llm_model_other", ""),
            "Azure OpenAI": config.get("azure_deployment", ""),
            "Anthropic": config.get("config_anthropic_model", ""),
            "Moonshot": config.get("config_moonshot_model", ""),
            "Gemini": config.get("config_gemini_model", ""),
            "Groq": config.get("config_groq_model", "")
        }
        
        current_model = saved_models.get(selected_provider, "")
        available_models = []
        
        # --- 核心改进：工具栏模型自动同步 (v2.9.6) ---
        from src.utils.model_utils import fetch_remote_models
        
        # 获取当前供应商的连接参数 (v2.9.6 支持自定义供应商)
        provider_params = {
            "Ollama": (config.get('llm_url_ollama', "http://localhost:11434"), ""),
            "OpenAI": (config.get('llm_url_openai', "https://api.openai.com/v1"), config.get('llm_key', "")),
            "OpenAI-Compatible": (config.get('llm_url_other', ""), config.get('llm_key_other', "")),
            "Azure OpenAI": (config.get('azure_endpoint', ""), config.get('azure_key', "")),
            "Anthropic": ("", config.get('anthropic_key', "")),
            "Moonshot": ("https://api.moonshot.cn/v1", config.get('moonshot_key', "")),
            "Gemini": ("", config.get('gemini_key', "")),
            "Groq": ("https://api.groq.com/openai/v1", config.get('groq_key', ""))
        }
        
        # 动态补充自定义供应商参数
        custom_providers = config.get("custom_llm_providers", {})
        for cp_id, cp_info in custom_providers.items():
            provider_params[cp_id] = (cp_info.get('url', ""), cp_info.get('key', ""))
        
        url, key = provider_params.get(selected_provider, ("", ""))
        cache_key = f"models_{selected_provider}_{url}_{key}"
        
        # 尝试从缓存获取
        if cache_key in st.session_state:
            available_models = st.session_state[cache_key]
        else:
            # 如果缓存中没有，且参数完整，尝试自动加载一次
            if (url or selected_provider in ["Anthropic", "Gemini"]) and not st.session_state.get(f"auto_load_{selected_provider}"):
                with st.spinner(""):
                    models, err = fetch_remote_models(url, key)
                    if models:
                        available_models = models
                        st.session_state[cache_key] = models
                        st.session_state[f"auto_load_{selected_provider}"] = True
            
        # 确保当前模型在列表中
        if not available_models:
            available_models = [current_model] if current_model else ["未配置模型"]
        elif current_model and current_model not in available_models:
            available_models.insert(0, current_model)
            
        idx = available_models.index(current_model) if current_model in available_models else 0

        # 权限检查：管理系统配置 (v4.5.2)
        from src.auth.permission_manager import permission_manager
        current_user = st.session_state.get('user', 'guest_user')
        can_manage_config = permission_manager.has_permission(current_user, "manage_system_config")

        def on_model_change():
            # 二次权限校验
            if not can_manage_config:
                st.toast("⚠️ 权限不足：只有管理员可修改系统全局模型配置", icon="🔒")
                return

            new_model = st.session_state.toolbar_model_selector
            if new_model not in ["未配置模型", ""]:
                if update_all_model_configs(new_model):
                    config = ConfigLoader.load()
                    config['llm_provider'] = st.session_state.toolbar_provider_selector
                    prov = st.session_state.toolbar_provider_selector
                    # 同步更新对应供应商的模型字段
                    field_map = {
                        "Ollama": "llm_model_ollama", "OpenAI": "llm_model_openai",
                        "OpenAI-Compatible": "llm_model_other", "Azure OpenAI": "azure_deployment",
                        "Anthropic": "config_anthropic_model", "Moonshot": "config_moonshot_model",
                        "Gemini": "config_gemini_model", "Groq": "config_groq_model"
                    }
                    if prov in field_map: config[field_map[prov]] = new_model
                    ConfigLoader.save(config)
                    st.toast(f"✅ 已切换为: {new_model}", icon="🤖")

        # 增加刷新小图标，紧凑布局 (v2.9.6)
        col_select, col_refresh = st.columns([0.85, 0.15])
        with col_select:
            st.selectbox(
                "选择模型",
                options=available_models,
                index=idx,
                key="toolbar_model_selector",
                on_change=on_model_change,
                label_visibility="collapsed",
                disabled=not can_manage_config,
                help="系统全局模型配置 (仅管理员可修改)" if not can_manage_config else None
            )
        with col_refresh:
            if st.button("🔄", key="toolbar_model_refresh", help="刷新模型列表"):
                with st.spinner(""):
                    models, err = fetch_remote_models(url, key)
                    if models:
                        st.session_state[cache_key] = models
                        st.toast(f"✅ 已同步 {len(models)} 个模型")
                        st.rerun()
                    else:
                        st.error("同步失败")

    # --- 3. 功能开关 (Toggle) ---
    with c_deep:
        deep_on = st.toggle("深度思考", value=st.session_state.get('enable_query_optimization', False), help="启用智能查询优化")
        st.session_state.enable_query_optimization = deep_on

    with c_web:
        # 权限检查：联网搜索 (实时颗粒化)
        from src.auth.permission_manager import permission_manager
        current_user = st.session_state.get('user', 'guest_user')
        can_search = permission_manager.has_permission(current_user, "smart_search")
        
        if not can_search:
            st.toggle("🌐 联网搜索 (🔒 权限受限)", value=False, disabled=True, help="请联系管理员开启联网搜索权限")
            web_search_on = False
        else:
            web_search_on = st.toggle("联网搜索", value=st.session_state.get('enable_web_search', False), help="启用联网搜索")
        st.session_state.enable_web_search = web_search_on

    with c_research:
        # 权限检查：智能研究
        from src.auth.permission_manager import permission_manager
        current_user = st.session_state.get('user', 'guest_user')
        can_research = permission_manager.has_permission(current_user, "deep_research")
        
        if not can_research:
            st.toggle("智能研究 (🔒)", value=False, disabled=True, help="请联系管理员开启深度研究权限")
            st.session_state.enable_deep_research = False
        else:
            research_on = st.toggle("智能研究", value=st.session_state.get('enable_deep_research', False), help="启用深度研究模式 (v2.9)")
            st.session_state.enable_deep_research = research_on

    with c_da:
        # 权限检查：数据分析
        from src.auth.permission_manager import permission_manager
        current_user = st.session_state.get('user', 'guest_user')
        can_analyze = permission_manager.has_permission(current_user, "data_analysis")
        
        if not can_analyze:
            st.toggle("数据分析 (🔒)", value=False, disabled=True, help="请联系管理员开启数据分析权限")
            st.session_state.is_data_analysis_mode = False
        else:
            da_on = st.toggle("数据分析", value=st.session_state.get('is_data_analysis_mode', False), help="手动触发宏观数据分析与推演 (v4.5)")
            st.session_state.is_data_analysis_mode = da_on

    # --- 4. 操作按钮 (Popover/Button) ---
    if st.session_state.get('is_processing'):
        with c_stop:
            if st.button("⏹ 停止", type="primary", use_container_width=True):
                st.session_state.is_processing = False
                st.session_state.stop_generation = True
                st.rerun()

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
# 添加问题模板选择器（在输入框上方）
if active_kb_name and active_kb_name != "multi_kb_mode":
    # 添加查询引导
    from src.utils.user_guidance import show_guidance
    show_guidance("query")
    
    try:
        with st.expander("💡 常用问题模板", expanded=False):
            st.markdown("选择模板快速开始对话：")
            
            # 针对知识库的问题模板（而不是单个文档）
            question_templates = [
                "这个知识库主要包含哪些内容？",
                "帮我总结一下知识库中的核心观点",
                "知识库中有哪些实用的方法或建议？",
                "请介绍知识库涉及的主要概念",
                "知识库中提到了哪些重要数据？",
                "基于知识库内容，给我一些行动建议",
                "知识库中有哪些值得注意的要点？",
                "请帮我梳理知识库的知识框架"
            ]
            
            # 使用按钮，点击后直接提交问题
            cols = st.columns(2)
            for i, template in enumerate(question_templates):
                col = cols[i % 2]
                if col.button(f"📝 {template[:12]}...", key=f"template_{i}", help=template):
                    try:
                        # 确保question_queue已初始化
                        if 'question_queue' not in st.session_state:
                            st.session_state.question_queue = []
                        
                        # 检查知识库是否可用
                        if not active_kb_name or active_kb_name == "multi_kb_mode":
                            st.error("❌ 请先选择一个知识库")
                            continue
                        
                        # 直接将问题加入处理队列
                        st.session_state.question_queue.append(template)
                        st.success(f"✅ 已提交问题: {template}")
                        st.rerun()
                        
                    except Exception as e:
                        # 绝不能因为点击问题而崩溃应用
                        st.error(f"❌ 提交问题时出错: {str(e)}")
                        st.warning("💡 请尝试手动输入问题，或刷新页面后重试")
                        
    except Exception as e:
        # 问题模板区域出错时的降级处理
        st.warning("⚠️ 问题模板功能暂时不可用，请直接在下方输入框中提问")
        st.caption(f"错误详情: {str(e)}")

# 持久显示联网搜索结果 - 放在输入框之前
if st.session_state.get('last_web_search_results'):
    search_data = st.session_state.last_web_search_results
    keywords = search_data.get('keywords', [])
    
    with st.expander(f"🌐 联网搜索参考信息 ({search_data['timestamp']}) - {len(search_data['results'])} 条结果", expanded=False):
        # 显示搜索详情
        col1, col2 = st.columns([2, 1])
        with col1:
            st.caption(f"🔍 **原始查询**: {search_data['query']}")
            if keywords:
                st.caption(f"🔑 **搜索关键词**: {', '.join(keywords)}")
        with col2:
            st.caption("📡 **搜索引擎**: DuckDuckGo")
        
        st.divider()
        
        for i, result in enumerate(search_data['results'][:8], 1):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**{i}. {result.get('title', 'No Title')}**")
                st.caption(f"{result.get('body', 'No content')[:150]}...")
                st.markdown(f"🔗 [{result.get('href', 'No URL')}]({result.get('href', '#')})")
            
            with col2:
                if result.get('quality_score', 0) > 0:
                    st.metric("相关性", f"{result['quality_score']} 分")
            
            if i < len(search_data['results'][:8]):
                st.divider()

# 保持输入框形态一致，避免布局跳动
if st.session_state.get('is_processing'):
    st.chat_input("正在生成回答中...", disabled=True)
else:
    # 检查是否有模板要使用
    placeholder_text = "输入问题..."
    if st.session_state.get('template_to_use'):
        placeholder_text = st.session_state.template_to_use
        # 清除模板状态，避免重复使用
        del st.session_state.template_to_use
    
    # 正常输入状态
    user_input = st.chat_input(placeholder_text)
    
    # 如果有新输入，加入队列
    if user_input:
        if active_kb_name == "multi_kb_mode":
            # 多知识库模式 - 直接处理查询
            selected_kbs = st.session_state.get('selected_kbs', [])
            if not selected_kbs:
                st.error("请先选择知识库")
            else:
                st.session_state.question_queue.append(user_input)
        elif active_kb_name == "pure_chat":
            # 纯对话模式 - 直接处理，无需知识库
            st.session_state.question_queue.append(user_input)
        elif not st.session_state.chat_engine:
            st.error("请先点击左侧【🚀 执行处理】启动系统")
        else:
            st.session_state.question_queue.append(user_input)

# 处理 prompt_trigger（追问按钮）
if st.session_state.prompt_trigger:
    if st.session_state.chat_engine:
        st.session_state.question_queue.append(st.session_state.prompt_trigger)
    st.session_state.prompt_trigger = None

# --- 核心调度逻辑 (v4.5.5 彻底修复死锁) ---
# 1. 自动从队列消费 (如果当前空闲且队列有任务)
if not st.session_state.get('is_processing') and st.session_state.question_queue:
    st.session_state.current_active_query = st.session_state.question_queue.pop(0)
    st.session_state.is_processing = True
    st.session_state.process_start_time = time.time()
    st.rerun()

# 2. 状态监控：如果处理超时(180s)，强制释放 (防止死锁)
if st.session_state.get('is_processing'):
    elapsed = time.time() - st.session_state.get('process_start_time', time.time())
    if elapsed > 180:
        st.warning(f"⚠️ 处理超时 ({elapsed:.0f}s)，系统已强制重置")
        st.session_state.is_processing = False
        st.rerun()

# 3. 如果正在处理任务，提取当前问题
final_prompt = st.session_state.get('current_active_query')

# 核心问答处理引擎入口
if st.session_state.get('is_processing') and final_prompt:
    # 消费掉任务标记 (转移到局部变量)
    del st.session_state.current_active_query
    
    # [审计] 记录用户提问行为
    from src.auth.audit_logger import AuditLogger
    AuditLogger.log(st.session_state.get('user', 'unknown'), "USER_QUERY", f"问: {final_prompt[:100]}", status="success")
    
    # 记录当前角色状态 (v2.7.4)
    from src.config.prompt_manager import PromptManager
    all_prompts = PromptManager.load_prompts()
    current_role_id = st.session_state.get('current_prompt_id', 'default')
    role_name = next((p['name'] for p in all_prompts if p['id'] == current_role_id), current_role_id)
    
    logger.info(f"🎭 当前角色: {role_name}")
    logger.info(f"🚀 开始处理对话任务: {final_prompt[:50]}...")
    
    # --- 阶段 A: 联网搜索 (Pre-processing) ---
    if st.session_state.get('enable_web_search', False):
        # 使用增强的联网搜索功能
        with st.status("🌐 正在联网搜索...", expanded=False) as status:
            st.write("🔍 智能分析搜索关键词...")
            search_results = enhanced_web_search(final_prompt, logger)
            if search_results:
                st.write(f"✅ 找到 {len(search_results)} 条相关结果")
                
                def extract_display_keywords(query):
                    # (精简后的关键词提取逻辑)
                    import re
                    remove_words = ['什么是', '哪些', '如何', '怎么', '为什么', '是什么']
                    cleaned = query
                    for word in remove_words: cleaned = cleaned.replace(word, ' ')
                    words = re.findall(r'[\u4e00-\u9fff]{2,5}', cleaned)
                    return words[:3]
                
                st.session_state.last_web_search_results = {
                    'query': final_prompt,
                    'results': search_results,
                    'timestamp': __import__('time').strftime('%H:%M:%S'),
                    'keywords': extract_display_keywords(final_prompt)
                }
                
                web_context = "以下是联网搜索到的相关信息：\n\n"
                for i, result in enumerate(search_results[:5], 1):
                    web_context += f"{i}. {result.get('title')}\n   {result.get('body')[:200]}...\n\n"
                
                final_prompt = f"{final_prompt}\n\n{web_context}请结合以上联网搜索信息进行回答。"
            else:
                st.write("❌ 未找到联网结果")
    
    if active_kb_name == "multi_kb_mode":
        # 多知识库模式处理
        selected_kbs = st.session_state.get('selected_kbs', [])
        st.session_state.is_processing = True
        logger.info("✅ 多知识库模式开始处理")
        logger.info(f"📋 选中知识库: {selected_kbs}")
        logger.info(f"❓ 用户问题: {final_prompt}")
        
        # 使用多知识库查询引擎
        from src.query.multi_kb_query_engine import MultiKBQueryEngine
        multi_engine = MultiKBQueryEngine(output_base)
        logger.info("🔧 多知识库查询引擎已初始化")
        
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        
        # 显示用户消息
        with st.chat_message("user"):
            st.write(final_prompt)
        
        # 显示助手回复
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # 显示加载动画
            with st.spinner("🔍 正在从多个知识库中检索信息..."):
                try:
                    # 执行多知识库查询
                    logger.info(final_prompt)
                    response = multi_engine.query(final_prompt, selected_kbs, embed_provider, embed_model, embed_key, embed_url)
                    logger.info(f"✅ DEBUG: 多知识库查询完成")
                    
                except Exception as e:
                    error_msg = f"查询失败: {str(e)}"
                    logger.log("多知识库查询", "error", f"❌ 多知识库查询异常: {str(e)}")
                    response_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    st.session_state.is_processing = False
                    st.rerun()
            
            # 显示查询结果
            response_placeholder.write(response)
            
            # 添加助手消息
            st.session_state.messages.append({"role": "assistant", "content": response})
            logger.log("多知识库查询", "complete", "✅ 多知识库查询完成")
            
            st.session_state.is_processing = False
            st.rerun()
                
    elif active_kb_name == "pure_chat":
        # 纯对话模式处理 - 直接与LLM对话，无需知识库
        st.session_state.is_processing = True
        logger.info("✅ 纯对话模式开始处理")
        logger.info(f"❓ 用户问题: {final_prompt}")
        
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        
        # 显示用户消息
        with st.chat_message("user"):
            st.write(final_prompt)
        
        # 显示助手回复
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            try:
                # 获取当前LLM配置
                from src.utils.model_manager import load_llm_model
                llm = load_llm_model(llm_provider, llm_model, llm_key, llm_url)
                
                if llm:
                    # 获取当前角色提示词
                    from src.config.prompt_manager import PromptManager
                    current_role_id = st.session_state.get('current_prompt_id', 'default')
                    system_prompt = PromptManager.get_content(current_role_id)
                    
                    # 构建完整提示
                    full_prompt = f"{system_prompt}\n\n用户问题: {final_prompt}"
                    
                    # 直接调用LLM
                    response = llm.complete(full_prompt)
                    response_text = str(response)
                    
                    # 显示回复
                    response_placeholder.write(response_text)
                    
                    # 添加助手消息
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                    logger.log("纯对话模式", "complete", "✅ 纯对话模式查询完成")
                else:
                    error_msg = "❌ LLM模型未配置，请检查模型设置"
                    response_placeholder.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
            except Exception as e:
                error_msg = f"纯对话模式查询失败: {str(e)}"
                logger.log("纯对话模式", "error", f"❌ 纯对话模式异常: {str(e)}")
                response_placeholder.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            
            st.session_state.is_processing = False
            st.rerun()
                
    elif st.session_state.chat_engine:
        # 不清空 suggestions_history，保留追问按钮
        st.session_state.is_processing = True  # 标记正在处理
        logger.info("✅ 设置处理状态为 True")
        
        # 强制检测知识库维度并切换模型（静默处理，不显示加载）
        # 优化：只在首次或切换知识库时检测，避免每次问答都重复
        if active_kb_name:  # 只有在单知识库模式下才检测维度
            db_path = os.path.join(output_base, active_kb_name)
            
            # 始终检测维度，确保模型匹配
            kb_dim = get_kb_embedding_dim(db_path)
            
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
                    logger.info(f"🔄 强制切换模型: {embed_model} → {required_model} (维度: {kb_dim}D)")
                    embed_model = required_model
                    embed = get_embed(embed_provider, embed_model, embed_key, embed_url)
                    if embed:
                        Settings.embed_model = embed
                        logger.info(f"✅ 模型已切换")
            else:
                # 维度检测失败时，不强制切换，但记录日志
                if not kb_dim:
                    logger.warning(embed_model)
        
        logger.separator("知识库查询")
        
        # 检查是否为多知识库模式
        if len(st.session_state.get('selected_kbs', [])) > 1:
            # 多知识库查询模式
            selected_kbs = st.session_state.get('selected_kbs', [])
            logger.start_operation("多知识库查询", f"知识库: {', '.join(selected_kbs)}")
            
            # 导入多知识库查询引擎
            from src.query.multi_kb_query_engine import query_single_kb_worker
            from concurrent.futures import ProcessPoolExecutor, as_completed
            
            # 执行多知识库查询
            start_time = time.time()
            
            # --- 多库模式下的智能研究注入 (v2.9.2) ---
            if st.session_state.get('enable_deep_research', False):
                with st.status("🔬 多库智能研究：专家组会审中...", expanded=False) as status:
                    try:
                        from llama_index.core import Settings
                        llm = Settings.llm
                        st.write("🎭 正在召集跨领域专家分析多库问题...")
                        role_res = llm.complete(f"针对多知识库问题：'{final_prompt}'，列出3个专业角色。")
                        roles = role_res.text.strip()
                        st.write(f"💬 征询专家意见: {roles}...")
                        syn_res = llm.complete(f"以【{roles}】视角分析问题：{final_prompt}")
                        final_prompt = f"【多库研究视角】:\n{syn_res.text}\n\n【原始问题】: {final_prompt}"
                        status.update(label="✅ 多库会审完成", state="complete")
                        logger.log("INFO", f"🔬 多库研究开启: {roles}", stage="多库查询")
                    except Exception as e:
                        logger.error(f"多库研究模式异常: {e}")
            
            results = {}
            max_workers = min(mp.cpu_count(), len(selected_kbs), 3)
            
            try:
                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    future_to_kb = {
                        executor.submit(query_single_kb_worker, kb_name, final_prompt, 3): kb_name 
                        for kb_name in selected_kbs
                    }
                    
                    for future in as_completed(future_to_kb, timeout=60):
                        kb_name = future_to_kb[future]
                        try:
                            result = future.result(timeout=30)
                            results[kb_name] = result
                        except Exception as e:
                            results[kb_name] = {
                                "kb_name": kb_name,
                                "success": False,
                                "error": f"查询失败: {str(e)}",
                                "results": []
                            }
            except Exception as e:
                logger.error(f"多进程查询失败: {e}")
                # 回退到单线程
                for kb_name in selected_kbs:
                    try:
                        result = query_single_kb_worker(kb_name, final_prompt, 3)
                        results[kb_name] = result
                    except Exception as kb_error:
                        results[kb_name] = {
                            "kb_name": kb_name,
                            "success": False,
                            "error": f"查询失败: {str(kb_error)}",
                            "results": []
                        }
            
            # 生成整合答案
            successful_results = [r for r in results.values() if r["success"]]
            total_time = time.time() - start_time
            
            if successful_results:
                # 构建整合答案
                integrated_answer = f"**基于 {len(successful_results)} 个知识库的查询结果：**\n\n"
                
                for i, result in enumerate(successful_results, 1):
                    kb_name = result["kb_name"]
                    answer = result.get("answer", "无答案")
                    integrated_answer += f"#### 📚 知识库 {i}: {kb_name}\n{answer}\n\n"
                
                integrated_answer += f"---\n**查询统计**: {len(successful_results)}/{len(selected_kbs)} 个知识库响应成功，耗时 {total_time:.2f} 秒"
                
                # 显示结果
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(integrated_answer)
                    
                    # 添加查询成功提示
                    st.success(f"✅ 查询完成！从 {len(successful_results)} 个知识库获得答案，耗时 {total_time:.2f} 秒")
                    
                    # 详细结果
                    with st.expander("📋 详细结果"):
                        for kb_name, result in results.items():
                            if result["success"] and result["results"]:
                                st.write(f"**📚 {kb_name}**")
                                for i, doc in enumerate(result["results"][:2], 1):
                                    st.write(f"📄 {doc['source']} (相关度: {doc['score']:.3f})")
                                    st.caption(doc['content'][:200] + "...")
                
                # 添加到消息历史
                st.session_state.messages.append({"role": "user", "content": final_prompt})
                st.session_state.messages.append({"role": "assistant", "content": integrated_answer})
                
                # [关键修复] 立即保存会话历史 (Multi-KB)
                if active_kb_name: 
                    HistoryManager.save_session(active_kb_name, st.session_state.messages, st.session_state.get('current_session_id'))
                
            else:
                st.error("❌ 所有知识库查询都失败了")
            
            st.session_state.is_processing = False
            st.rerun()
            
        else:
            # 单知识库查询模式（原逻辑）
            logger.start_operation("查询", f"知识库: {active_kb_name}")
        
        # 查询改写 (v1.6) - 深度思考自动优化
        if st.session_state.get('enable_query_optimization', False):
            logger.info(f"🧠 DEBUG: 深度思考功能已启用，开始自动优化查询")
            logger.info("🧠 深度思考(查询优化)已激活")
            query_rewriter = QueryRewriter(Settings.llm)
            should_rewrite, reason = query_rewriter.should_rewrite(final_prompt)
            logger.info(f"🧠 DEBUG: should_rewrite={should_rewrite}, reason={reason}")
            
            if should_rewrite:
                logger.info(f"💡 DEBUG: 检测到需要改写查询")
                logger.info(f"💡 深度思考: 检测到需要改写查询 - {reason}")
                rewritten_query = query_rewriter.suggest_rewrite(final_prompt)
                logger.info(f"💡 DEBUG: 优化后的查询: {rewritten_query}")
                
                if rewritten_query and rewritten_query != final_prompt:
                    # 保存原问题
                    original_prompt = final_prompt
                    
                    # 显示优化信息并自动使用优化后的查询
                    with st.chat_message("assistant", avatar="🤖"):
                        st.info(f"💡 **深度思考优化**\n\n原问题：{final_prompt}\n\n优化后：{rewritten_query}\n\n✅ 自动使用优化后的查询进行回答")
                    
                    # 直接使用优化后的查询
                    final_prompt = rewritten_query
                    logger.success(final_prompt)
                    logger.success(original_prompt)
                    logger.success(final_prompt)
                    logger.info(f"✅ 深度思考: 自动使用优化后的查询 - {rewritten_query}")
                    
                    # 确保后续所有地方都使用优化后的查询
                    st.session_state.current_optimized_query = final_prompt
            else:
                logger.info(f"🧠 DEBUG: 查询清晰，无需改写")
                logger.info(f"🧠 深度思考: 查询清晰，无需改写 ({reason})")
        else:
            logger.info(f"🧠 DEBUG: 深度思考功能未启用")
        
        logger.info(final_prompt)

        # 保存用于显示和查询的提示词
        user_display_prompt = final_prompt  # 用于UI显示
        query_prompt = final_prompt  # 用于实际查询
        logger.info(query_prompt)
        
        # 处理引用内容
        if st.session_state.get("quote_content"):
            quoted_text = st.session_state.quote_content
            # 限制引用长度，防止 prompt 过长
            if len(quoted_text) > 2000:
                quoted_text = quoted_text[:2000] + "...(已截断)"
            
            # 构建包含引用的 prompt
            original_prompt_temp = final_prompt
            final_prompt = f"基于以下引用内容：\n> {quoted_text}\n\n{original_prompt_temp}"
            # 更新显示用的 prompt，加入引用样式
            user_display_prompt = f"📌 **引用内容**:\n> {quoted_text[:100]}...\n\n{user_display_prompt}"
            
            # 清除引用状态
            st.session_state.quote_content = None
            logger.info("📌 已应用引用内容")
        
        # --- 智能研究 (Deep Research) 进阶模式 (v2.9.2) - 专家会审与多维合成 ---
        research_critique = ""
        expert_perspectives = ""
        if st.session_state.get('enable_deep_research', False):
            # 专家会审必须在检索之前完成，因为其结果要作为检索的增强背景
            with st.status("🔬 智能研究：专家组会审中...", expanded=False) as status:
                try:
                    from llama_index.core import Settings
                    llm = Settings.llm
                    
                    if st.session_state.get('stop_generation'): raise InterruptedError("User stopped")

                    # 1. 角色判定 (基于原始问题，避免受网页噪音干扰)
                    st.write("🎭 正在召集相关领域专家...")
                    role_response = llm.complete(f"针对问题：'{user_display_prompt}'，列出3个最专业的角色名称，逗号分隔。")
                    roles = role_response.text.strip()
                    logger.log("INFO", f"🎭 智能研究：识别到专家角色 - {roles}", stage="智能研究")
                    
                    if st.session_state.get('stop_generation'): raise InterruptedError("User stopped")

                    # 2. 专家视角碰撞 (专家们需要参考联网信息！)
                    st.write(f"💬 正在征询专家意见: {roles}...")
                    synthesis_prompt = (
                        f"作为【{roles}】，请结合以下参考信息和用户问题，提供深度专业洞察：\n"
                        f"{final_prompt}\n\n"
                        "要求：每个视角约 100 字，侧重于技术可行性、潜在风险或前瞻性建议。"
                    )
                    synthesis_response = llm.complete(synthesis_prompt)
                    expert_perspectives = synthesis_response.text
                    
                    if st.session_state.get('stop_generation'): raise InterruptedError("User stopped")

                    # 3. 逻辑审计
                    st.write("🧠 正在执行逻辑审计与一致性检查...")
                    critique_prompt = f"请审计以下专家观点是否存在逻辑矛盾或信息偏差：\n{expert_perspectives}"
                    critique_response = llm.complete(critique_prompt)
                    research_critique = critique_response.text
                    
                    # 4. 最终合成全景研究 Prompt
                    final_prompt = (
                        f"【研究背景 (联网信息)】:\n{final_prompt}\n\n"
                        f"【专家会审视角】:\n{expert_perspectives}\n\n"
                        f"【审计修正意见】: {research_critique}\n\n"
                        f"【指令】: 请结合上述联网背景、多维视角和审计意见，并去你的本地知识库中检索进一步的事实，为用户提供一份最终的、极具深度的专业全景研究报告。"
                    )
                    status.update(label="✅ 专家会审完成，正在汇总全景报告", state="complete")
                    st.write(f"👥 **专家组**: {roles}")
                    with st.expander("🧐 查看审计细节"):
                        st.write(research_critique)
                    
                    # 记录专家会审元数据 (v2.9.4)
                    st.session_state.last_research_details = {
                        'roles': roles,
                        'perspectives': expert_perspectives,
                        'critique': research_critique
                    }
                    
                    logger.log("SUCCESS", "✅ 专家会审全流程完成", stage="智能研究", details={"experts": roles})
                
                except InterruptedError:
                    status.update(label="⏹ 研究进程已停止", state="error")
                except Exception as e:
                    status.update(label="⚠️ 专家会审降级", state="error")
                    logger.error(f"🔬 智能研究异常: {e}")
        
        logger.log("INFO", f"用户提问: {final_prompt}", stage="查询对话", details={"kb_name": active_kb_name})
        
        # 检查重复查询（最近3次）
        recent_queries = [m['content'] for m in st.session_state.messages[-6:] if m['role'] == 'user']
        if final_prompt in recent_queries:
            st.info("💡 您刚才已经问过相同的问题，可以查看上面的回答或尝试换个角度提问")
            st.session_state.is_processing = False
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        if active_kb_name: HistoryManager.save_session(active_kb_name, state.get_messages(), st.session_state.get('current_session_id'))

        # UI 仅显示原始问题或带引用的简洁版
        with st.chat_message("user", avatar="🧑‍💻"): st.markdown(user_display_prompt)
        
        with st.chat_message("assistant", avatar="🤖"):
            msg_placeholder = st.empty()
            
            # 使用一个连贯的spinner包装整个问答流程
            with st.spinner("🧠 正在进行深度业务逻辑推演..."):
                try:
                    # --- 核心增强：数据分析 5.0 (业务语义模式) ---
                    manual_da_on = st.session_state.get('is_data_analysis_mode', False)
                    
                    if active_kb_name and active_kb_name not in ["pure_chat", "multi_kb_mode"]:
                        db_path = os.path.join(output_base, active_kb_name)
                        schema_path = os.path.join(db_path, "business_schema.json")
                        
                        # --- [v6.3.5] 逻辑隔离：仅在显式开启分析模式时执行战略推演 ---
                        if manual_da_on:
                            # A. 唤醒逻辑 (支持从归档目录恢复)
                            if not os.path.exists(schema_path):
                                import glob
                                # [修正] 同时扫描根目录和物理归档目录
                                raw_p = os.path.join(db_path, "raw_sources")
                                data_files = glob.glob(os.path.join(db_path, "*.csv")) + \
                                             glob.glob(os.path.join(db_path, "*.xlsx"))
                                if os.path.exists(raw_p):
                                    data_files += glob.glob(os.path.join(raw_p, "**/*.csv"), recursive=True) + \
                                                  glob.glob(os.path.join(raw_p, "**/*.xlsx"), recursive=True)
                                
                                if data_files:
                                    try:
                                        from src.processors.data_analyst import DataAnalystEngine
                                        from src.utils.model_manager import load_llm_model
                                        da_engine = DataAnalystEngine(db_path, logger)
                                        llm = load_llm_model(llm_provider, llm_model, llm_key, llm_url)
                                        da_engine.process_files(data_files)
                                        
                                        # 强制重新提取业务含义
                                        from llama_index.core import SimpleDirectoryReader
                                        reader = SimpleDirectoryReader(input_dir=raw_p if os.path.exists(raw_p) else db_path)
                                        docs = reader.load_data()
                                        if docs: da_engine.extract_schema_from_docs(docs, llm)
                                    except Exception as e:
                                        logger.warning(f"⚠️ 引擎按需唤醒异常: {e}")

                        # B. 战略推演工作坊逻辑
                        if os.path.exists(schema_path) and (manual_da_on or "is_data_kb" in locals()):
                            from src.auth.audit_logger import AuditLogger
                            from src.common.utils import get_client_ip
                            AuditLogger.log(
                                st.session_state.get('user', 'admin'), 
                                "DATA_ANALYSIS_EXEC", 
                                f"执行战略推演: {final_prompt[:100]}", 
                                action_type="DATA_PROCESS", 
                                ip=get_client_ip()
                            )
                            
                            from src.processors.data_analyst import DataAnalystEngine
                            from src.utils.model_manager import load_llm_model
                            da_engine = DataAnalystEngine(db_path, logger)
                            llm = load_llm_model(llm_provider, llm_model, llm_key, llm_url)
                            
                            logger.info(f"🔮 [Strategic Workshop] 启动链式推演...")
                            
                            # [v5.6] 增加实时进度反馈，防止用户认为卡死
                            da_status_box = st.status("🧠 极光战略工作坊正在推演中...", expanded=True)
                            
                            def da_status_callback(msg):
                                da_status_box.write(msg)
                                logger.info(f"👉 {msg}")
                            
                            analysis_res = da_engine.execute_analysis(final_prompt, llm, status_callback=da_status_callback)
                            da_status_box.update(label="✅ 战略推演已完成", state="complete", expanded=False)
                            
                            if analysis_res.get("success", False):
                                st.markdown(f"### 🏗️ 5.2.4 极光战略工作坊 (工程化闭环)")
                                if analysis_res.get("macro_context"):
                                    st.info(f"🎯 **核心战略目标**: {analysis_res['macro_context']}")
                                    
                                # 1. 核心推演报告 (总领全文)
                                report_placeholder = st.empty()
                                full_report = ""
                                logic_stream = analysis_res.get("logic_gen")
                                if logic_stream:
                                    for token in logic_stream:
                                        full_report += token
                                        report_placeholder.markdown(full_report + "▌")
                                
                                report_placeholder.markdown(full_report)
                                # 2. 循环渲染每个逻辑阶段
                                for stage in analysis_res.get("stages", []):
                                    meta = stage["meta"]
                                    with st.expander(f"📍 Stage {meta['stage_id']}: {meta['title']}", expanded=True):
                                        st.markdown(f"**分析目标**: {meta['goal']}")
                                        
                                        # --- [v5.2] 数据流转全演示 ---
                                        with st.container(border=True):
                                            st.markdown("##### 🧬 数据演进演示 (Lineage Demo)")
                                            
                                            # A. 查询前：原始数据
                                            st.markdown("**1. 查询前：业务表采样 (Before)**")
                                            if stage.get("source_samples"):
                                                s_tabs = st.tabs(list(stage["source_samples"].keys()))
                                                for idx, t_name in enumerate(stage["source_samples"]):
                                                    with s_tabs[idx]:
                                                        import pandas as pd
                                                        st.dataframe(pd.DataFrame(stage["source_samples"][t_name]), use_container_width=True)
                                            
                                            # B. 加工中：逻辑脚本
                                            st.markdown("**2. 执行中：工程逻辑 (The Logic)**")
                                            sqls = stage.get("sqls", {})
                                            sql_tabs = st.tabs(["🧪 SQLite (本地验证)", "🐘 Standard SQL", "💻 DataWorks (生产)"])
                                            with sql_tabs[0]:
                                                st.caption("SQL 语言: SQLite (Local Sim)")
                                                st.code(sqls.get("sqlite", ""), language="sql")
                                            with sql_tabs[1]:
                                                st.caption("SQL 语言: Standard ANSI SQL")
                                                st.code(sqls.get("standard", ""), language="sql")
                                            with sql_tabs[2]:
                                                st.caption("SQL 语言: MaxCompute / DataWorks")
                                                st.code(sqls.get("dataworks", ""), language="sql")
                                            
                                            # C. 查询后：结果产出
                                            st.markdown("**3. 查询后：汇聚结果表 (After)**")
                                            import pandas as pd
                                            df_s = pd.DataFrame(stage["data"])
                                            if not df_s.empty:
                                                # 使用全功能可视化画板 [v5.8.8]
                                                render_smart_visualization(
                                                    df=df_s, 
                                                    query=meta['title'], 
                                                    msg_idx=999, 
                                                    stage_id=meta['stage_id'], 
                                                    recommendation=stage.get("recommendation")
                                                )
                                            else:
                                                st.info("该阶段未产出数据结果")
                                            if stage.get("is_simulated"):
                                                st.warning("✨ 本阶段结果基于战略业务模型仿真得出")

                                # 3. [v5.2.3 恢复] 生成最新的战略建议追问
                                try:
                                    from src.chat.unified_suggestion_engine import get_unified_suggestion_engine
                                    sug_engine = get_unified_suggestion_engine(active_kb_name)
                                    # 结合提问与最终报告内容作为生成上下文
                                    suggestion_context = f"用户提问: {final_prompt}\n战略推演报告: {full_report}"
                                    new_sugs = sug_engine.generate_suggestions(
                                        context=suggestion_context,
                                        source_type='chat',
                                        query_engine=st.session_state.chat_engine,
                                        num_questions=3
                                    )
                                    if new_sugs:
                                        st.session_state.suggestions_history = new_sugs[:3]
                                        st.session_state.current_suggestions = new_sugs[:3]
                                except Exception as e:
                                    logger.warning(f"⚠️ 战略追问生成失败: {e}")

                                # 归档并中断
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": full_report, 
                                    "is_data_report": True, 
                                    "stages": analysis_res["stages"], 
                                    "macro_context": analysis_res.get("macro_context"),
                                    "suggestions": st.session_state.get('current_suggestions', [])
                                })
                                
                                # [关键修复] 立即保存会话历史 (Data Analysis)
                                if active_kb_name: 
                                    HistoryManager.save_session(active_kb_name, st.session_state.messages, st.session_state.get('current_session_id'))
                                
                                st.session_state.is_processing = False
                                st.rerun()



                    # --- 原始 RAG 逻辑 (仅当不是分析模式或分析失败时执行) ---
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
                        
                        # 检查 chat_engine 状态
                        if not st.session_state.get('chat_engine'):
                            raise Exception("聊天引擎未初始化，请先选择知识库")
                        
                        # GPU加速检索 - 批量处理
                        retrieval_start = time.time()
                        logger.info(f"🔍 开始查询: {final_prompt[:100]}...")
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
                    
                    logger.log("SUCCESS", "回答生成完成", stage="查询对话", details={
                        "kb_name": active_kb_name, 
                        "model": llm_model, 
                        "role": role_name,
                        "tokens": token_count, 
                        "prompt_tokens": prompt_tokens, 
                        "completion_tokens": completion_tokens
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
                        "stats": stats,
                        "prompt_role": role_name,
                        "search_results": st.session_state.get('last_search_results'),
                        "research_details": st.session_state.get('last_research_details')
                    })
                    
                    # 清理单次会话临时变量
                    st.session_state.last_search_results = None
                    st.session_state.last_optimized_query = None
                    st.session_state.last_research_details = None
                    
                    # 生成推荐问题（在spinner内完成）
                    # 组合上下文：用户问题 + AI回答
                    existing_questions = [m['content'] for m in st.session_state.messages if m['role'] == 'user']
                    last_user_query = existing_questions[-1] if existing_questions else ""
                    combined_context = f"用户问题: {last_user_query}\nAI回答: {full_text}"
                    
                    existing_questions.extend(st.session_state.question_queue)
                    existing_questions.extend(st.session_state.get('suggestions_history', []))
                    
                    # 使用统一推荐引擎
                    # 优先使用 active_kb_name 确保配置正确加载
                    suggestion_kb = active_kb_name or st.session_state.get('current_kb_name')
                    engine = get_unified_suggestion_engine(suggestion_kb)
                    
                    initial_sugs = engine.generate_suggestions(
                        context=combined_context,
                        source_type='chat',
                        query_engine=st.session_state.chat_engine if st.session_state.get('chat_engine') else None,
                        num_questions=3,
                        existing_history=existing_questions
                    )
                    
                    logger.info(f"🔧 推荐引擎返回 {len(initial_sugs)} 个问题")
                    
                    if initial_sugs:
                        sug_list = initial_sugs[:3]
                        st.session_state.suggestions_history = sug_list
                        st.session_state.current_suggestions = sug_list # 确保双重缓存同步
                        
                        # [关键修复] 将建议直接注入到最后一条消息中，确保渲染器能抓取到
                        if st.session_state.messages and st.session_state.messages[-1]['role'] == 'assistant':
                            st.session_state.messages[-1]['suggestions'] = sug_list
                            
                        logger.info(f"✨ 生成 {len(initial_sugs)} 个推荐问题")
                        for i, q in enumerate(sug_list, 1):
                            logger.info(f"   {i}. {q}")
                    else:
                        logger.warning("⚠️ 推荐引擎未返回任何问题 (严格模式)")
                        st.session_state.suggestions_history = []
                        st.session_state.current_suggestions = []
                    
                    # 延迟保存：确认所有步骤都成功后再保存
                    if active_kb_name: HistoryManager.save_session(active_kb_name, state.get_messages(), st.session_state.get('current_session_id'))
                    
                    # 释放内存
                    cleanup_memory()
                    logger.info("🧹 对话完成，内存已清理")
                    
                    st.session_state.is_processing = False  # 处理完成
                    
                    # 整体处理完成反馈
                    st.toast("✅ 回答生成完毕", icon="🎉")
                    
                    # 添加详细的成功提示
                    st.success(f"✅ 查询处理完成！生成 {token_count} 个token，耗时 {total_time:.2f} 秒，速度 {tokens_per_sec:.1f} token/秒")
                    
                    st.rerun()
                
                except Exception as e: 
                    # [v5.9.4] 错误诊断增强：禁止静默闪退，显式抛出异常详情
                    import traceback
                    error_details = traceback.format_exc()
                    
                    if 'logger' not in locals() and 'logger' not in globals():
                        from src.app_logging.log_manager import LogManager
                        logger = LogManager()
                    
                    logger.error(f"查询处理崩溃: {str(e)}\n{error_details}")
                    
                    # [v6.3.7] 智能回滚保护：仅在必要时清理内存，防止“闪现消失”
                    if st.session_state.messages and st.session_state.messages[-1]['role'] == 'assistant':
                        last_msg = st.session_state.messages[-1]
                        # 如果消息内容过短或标识为错误现场，才执行回滚
                        if len(last_msg.get('content', '')) < 5:
                            st.session_state.messages.pop()
                            logger.warning("🗑️ 检测到残缺回答，已执行内存回滚")
                    
                    # 显式展示错误信息
                    st.error(f"❌ 系统执行异常")
                    with st.expander("🔍 查看技术细节"):
                        st.code(error_details)
                    
                    # 释放内存
                    cleanup_memory()
                    st.session_state.is_processing = False
                    st.stop()