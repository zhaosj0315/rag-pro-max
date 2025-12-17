"""
高级功能配置组件
Stage 3.2.3 - 低风险重构
提取自 apppro.py
"""

import streamlit as st
from typing import Tuple, Optional


def render_rerank_config() -> Tuple[bool, Optional[str]]:
    """
    渲染 Re-ranking 配置
    
    Returns:
        Tuple[bool, Optional[str]]: (是否启用, 模型名称)
    """
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
    
    rerank_model = None
    if enable_rerank:
        st.caption("📊 **工作原理**：先检索10个候选 → 智能重排序 → 返回最相关的3个")
        
        rerank_model_display = st.selectbox(
            "模型选择",
            ["BAAI/bge-reranker-base（推荐）", "BAAI/bge-reranker-v2-m3（更强）"],
            key="rerank_model_display",
            help="首次使用会自动下载模型（约 1GB）"
        )
        
        # 保存实际模型名
        if "推荐" in rerank_model_display:
            rerank_model = "BAAI/bge-reranker-base"
        else:
            rerank_model = "BAAI/bge-reranker-v2-m3"
        
        # 保存到 session_state（向后兼容）
        st.session_state.rerank_model = rerank_model
    
    return enable_rerank, rerank_model


def render_bm25_config() -> bool:
    """
    渲染 BM25 配置
    
    Returns:
        bool: 是否启用
    """
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
    
    return enable_bm25


def render_advanced_features() -> dict:
    """
    渲染完整的高级功能配置区域
    
    Returns:
        dict: 配置字典 {
            'enable_rerank': bool,
            'rerank_model': str,
            'enable_bm25': bool
        }
    """
    with st.expander("🎯 高级功能", expanded=False):
        # Re-ranking 配置
        enable_rerank, rerank_model = render_rerank_config()
        
        st.markdown("---")
        
        # BM25 配置
        enable_bm25 = render_bm25_config()
    
    return {
        'enable_rerank': enable_rerank,
        'rerank_model': rerank_model,
        'enable_bm25': enable_bm25
    }
