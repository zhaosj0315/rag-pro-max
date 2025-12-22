"""
统一UI组件 - 第一步
提取重复的文档详情对话框函数
"""

import streamlit as st
from typing import Dict, Any


@st.dialog("📄 文档详情")
def show_document_detail_dialog(kb_name: str, file_info: Dict[str, Any]) -> None:
    """
    显示文档详情对话框 - 统一版本
    
    Args:
        kb_name: 知识库名称
        file_info: 文档信息字典
    """
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
