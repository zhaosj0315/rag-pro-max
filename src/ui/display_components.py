"""
纯展示组件模块
只负责渲染 UI，不修改应用状态

Stage 3.1 - 低风险重构
提取自 apppro.py
"""

import streamlit as st
from typing import Dict, List, Any, Optional


def get_relevance_label(score: float) -> str:
    """
    根据相似度分数返回相关性标签
    
    Args:
        score: 相似度分数 (0-1)
        
    Returns:
        str: 相关性标签（高度相关/相关/一般相关）
    """
    if score >= 0.8:
        return "🔥 高度相关"
    elif score >= 0.6:
        return "✅ 相关"
    else:
        return "📌 一般相关"


def format_time_duration(seconds: float) -> str:
    """
    格式化时间显示
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化的时间字符串
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}秒"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}分{secs:.0f}秒"


def format_token_count(count: int) -> str:
    """
    格式化 token 数量显示
    
    Args:
        count: token 数量
        
    Returns:
        str: 格式化的字符串
    """
    if count < 1000:
        return f"{count} 字符"
    elif count < 10000:
        return f"{count/1000:.1f}K 字符"
    else:
        return f"{count/10000:.1f}万 字符"


def render_message_stats(stats: Dict[str, Any]) -> None:
    """
    渲染消息统计信息
    
    Args:
        stats: 统计信息字典，包含:
            - tokens: token 数量
            - time: 耗时（秒）
            - tokens_per_sec: 速度
            - prompt_tokens: 输入 tokens
            - completion_tokens: 输出 tokens
            - cpu: CPU 使用率
            - mem: 内存使用率
            - gpu: GPU 使用率
    """
    if not stats:
        return
    
    # 兼容旧版字段名
    token_count = stats.get('tokens', 0)
    total_time = stats.get('time', 0)
    
    # 1. 简单概览
    time_str = format_time_duration(total_time)
    token_str = format_token_count(token_count)
    stats_simple = f"⏱️ {time_str} | 📝 {token_str}"
    st.caption(stats_simple)
    
    # 2. 详细信息（折叠）
    with st.expander("📊 详细统计", expanded=False):
        # 速度信息
        tokens_per_sec = stats.get('tokens_per_sec', 0)
        if tokens_per_sec > 0:
            st.caption(f"🚀 速度: {tokens_per_sec:.1f} tokens/s")
        
        # Token 详情
        prompt_tokens = stats.get('prompt_tokens')
        completion_tokens = stats.get('completion_tokens')
        if prompt_tokens:
            st.caption(f"📥 输入: {prompt_tokens} | 📤 输出: {completion_tokens}")
        
        # 资源使用
        cpu = stats.get('cpu', 0)
        mem = stats.get('mem', 0)
        gpu = stats.get('gpu', 0)
        if cpu > 0 or mem > 0 or gpu > 0:
            st.caption(f"💻 资源: CPU {cpu:.1f}% | 内存 {mem:.1f}% | GPU {gpu:.1f}%")


def render_source_references(sources: List[Dict[str, Any]], expanded: bool = False) -> None:
    """
    渲染引用来源
    
    Args:
        sources: 来源列表，每个来源包含:
            - score: 相似度分数
            - file: 文件名
            - text: 引用文本
        expanded: 是否默认展开
    """
    if not sources:
        return
    
    with st.expander(f"📚 参考 {len(sources)} 个片段", expanded=expanded):
        for idx, src in enumerate(sources):
            score = src.get('score', 0)
            file_name = src.get('file', '未知文件')
            text = src.get('text', '')
            
            # 相关性标签 + 文件名
            st.markdown(f"**{get_relevance_label(score)}** | 📄 `{file_name}`")
            
            # 引用文本
            if text:
                # 限制显示长度
                display_text = text[:300] + "..." if len(text) > 300 else text
                st.caption(f"> {display_text}")
            
            # 分隔线（最后一个不显示）
            if idx < len(sources) - 1:
                st.divider()


def render_kb_info_card(kb_name: str, doc_count: int, total_chunks: int) -> None:
    """
    渲染知识库信息卡片
    
    Args:
        kb_name: 知识库名称
        doc_count: 文档数量
        total_chunks: 总片段数
    """
    st.info(f"""
    📚 **知识库**: {kb_name}
    📄 **文档数**: {doc_count}
    🧩 **片段数**: {total_chunks}
    """)


def render_system_stats(cpu: float, memory: float, gpu: float = 0) -> None:
    """
    渲染系统资源统计
    
    Args:
        cpu: CPU 使用率 (0-100)
        memory: 内存使用率 (0-100)
        gpu: GPU 使用率 (0-100)
    """
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("CPU", f"{cpu:.1f}%", delta=None)
    
    with col2:
        st.metric("内存", f"{memory:.1f}%", delta=None)
    
    with col3:
        if gpu > 0:
            st.metric("GPU", f"{gpu:.1f}%", delta=None)
        else:
            st.metric("GPU", "未使用", delta=None)


def render_error_message(error: str, details: Optional[str] = None) -> None:
    """
    渲染错误消息
    
    Args:
        error: 错误消息
        details: 详细信息（可选）
    """
    st.error(f"❌ {error}")
    
    if details:
        with st.expander("🔍 详细信息"):
            st.code(details)


def render_success_message(message: str, icon: str = "✅") -> None:
    """
    渲染成功消息
    
    Args:
        message: 成功消息
        icon: 图标（默认 ✅）
    """
    st.success(f"{icon} {message}")


def render_warning_message(message: str, icon: str = "⚠️") -> None:
    """
    渲染警告消息
    
    Args:
        message: 警告消息
        icon: 图标（默认 ⚠️）
    """
    st.warning(f"{icon} {message}")
