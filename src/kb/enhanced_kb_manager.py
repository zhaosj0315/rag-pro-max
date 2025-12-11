#!/usr/bin/env python3
"""增强的知识库管理器"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any
import json
import os

class EnhancedKBManager:
    """增强的知识库管理器"""
    
    def __init__(self):
        self.selected_docs = set()
    
    def render_compact_stats(self, stats: Dict[str, Any]):
        """渲染紧凑统计卡片"""
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📄 文件", stats.get('total_files', 0))
        with col2:
            st.metric("📦 片段", stats.get('total_chunks', 0))
        with col3:
            st.metric("💾 大小", f"{stats.get('total_size_mb', 0):.1f}MB")
        with col4:
            st.metric("💚 健康度", f"{stats.get('health_score', 0):.0f}%")
        with col5:
            st.metric("🔥 活跃度", f"{stats.get('activity_score', 0):.1f}")
    
    def render_document_list_enhanced(self, documents: List[Dict]):
        """渲染增强的文档列表"""
        if not documents:
            st.info("📭 暂无文档")
            return
        
        # 批量操作工具栏
        self.render_batch_operations()
        
        # 文档列表
        for i, doc in enumerate(documents):
            self.render_document_item_enhanced(doc, i)
    
    def render_batch_operations(self):
        """渲染批量操作工具栏"""
        if len(self.selected_docs) > 0:
            st.markdown("---")
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.write(f"已选择 {len(self.selected_docs)} 个文档")
            
            with col2:
                if st.button("🏷️ 批量标签", key="batch_tag"):
                    self.batch_tag_documents()
            
            with col3:
                if st.button("📊 批量分析", key="batch_analyze"):
                    self.batch_analyze_documents()
            
            with col4:
                if st.button("🗑️ 批量删除", key="batch_delete"):
                    self.batch_delete_documents()
            
            st.markdown("---")
    
    def render_document_item_enhanced(self, doc: Dict, index: int):
        """渲染增强的文档项"""
        doc_id = doc.get('id', f'doc_{index}')
        
        # 文档选择框和基本信息
        col1, col2, col3 = st.columns([0.5, 3, 1])
        
        with col1:
            selected = st.checkbox("", key=f"select_{doc_id}", value=doc_id in self.selected_docs)
            if selected:
                self.selected_docs.add(doc_id)
            else:
                self.selected_docs.discard(doc_id)
        
        with col2:
            # 文档标题和快速信息
            st.markdown(f"**📄 {doc.get('name', '未知文档')}**")
            
            # 快速统计信息
            info_cols = st.columns(4)
            with info_cols[0]:
                st.caption(f"📦 {doc.get('chunks', 0)} 片段")
            with info_cols[1]:
                st.caption(f"💾 {doc.get('size_mb', 0):.1f}MB")
            with info_cols[2]:
                st.caption(f"🎉 {doc.get('quality', '未知')}")
            with info_cols[3]:
                st.caption(f"🔥 {doc.get('hits', 0)} 次命中")
        
        with col3:
            # 操作按钮
            if st.button("📊 详情", key=f"details_{doc_id}"):
                self.show_document_details(doc)
        
        # 可折叠的详细信息
        with st.expander(f"📋 {doc.get('name', '文档')} 详细信息", expanded=False):
            self.render_document_details(doc)
    
    def render_document_details(self, doc: Dict):
        """渲染文档详细信息"""
        detail_cols = st.columns(2)
        
        with detail_cols[0]:
            st.markdown("**📊 基本信息**")
            st.write(f"• 类型: {doc.get('type', '未知')}")
            st.write(f"• 大小: {doc.get('size_mb', 0):.1f}MB")
            st.write(f"• 片段数: {doc.get('chunks', 0)}")
            st.write(f"• 字符数: ~{doc.get('chars', 0):,}")
            
            st.markdown("**🏷️ 标签**")
            tags = doc.get('tags', ['无标签'])
            for tag in tags:
                st.markdown(f"`{tag}`")
        
        with detail_cols[1]:
            st.markdown("**📈 使用统计**")
            st.write(f"• 命中次数: {doc.get('hits', 0)}")
            st.write(f"• 平均得分: {doc.get('avg_score', 0):.3f}")
            st.write(f"• 最后访问: {doc.get('last_access', '从未')}")
            
            st.markdown("**🔍 关键词**")
            keywords = doc.get('keywords', ['暂无'])
            st.write(" • ".join(keywords[:5]))
        
        # 文档摘要
        if doc.get('summary'):
            st.markdown("**📝 智能摘要**")
            st.markdown(f"> {doc.get('summary', '暂无摘要')}")
    
    def render_knowledge_graph(self, documents: List[Dict]):
        """渲染知识图谱"""
        st.markdown("### 🕸️ 知识图谱")
        
        if len(documents) < 2:
            st.info("需要至少2个文档才能生成知识图谱")
            return
        
        # 创建简单的关系图
        fig = go.Figure()
        
        # 添加节点
        for i, doc in enumerate(documents):
            fig.add_trace(go.Scatter(
                x=[i], y=[0],
                mode='markers+text',
                marker=dict(size=doc.get('chunks', 10) * 0.1 + 10, color='lightblue'),
                text=doc.get('name', f'文档{i}')[:10] + '...',
                textposition="middle center",
                name=doc.get('name', f'文档{i}')
            ))
        
        # 添加连接线（基于相似度）
        for i in range(len(documents)):
            for j in range(i+1, len(documents)):
                similarity = self.calculate_similarity(documents[i], documents[j])
                if similarity > 0.3:  # 相似度阈值
                    fig.add_trace(go.Scatter(
                        x=[i, j], y=[0, 0],
                        mode='lines',
                        line=dict(width=similarity*5, color='gray'),
                        showlegend=False
                    ))
        
        fig.update_layout(
            title="文档关系图",
            showlegend=False,
            height=400,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def calculate_similarity(self, doc1: Dict, doc2: Dict) -> float:
        """计算文档相似度（简化版）"""
        # 基于关键词重叠计算相似度
        keywords1 = set(doc1.get('keywords', []))
        keywords2 = set(doc2.get('keywords', []))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def render_smart_recommendations(self, current_doc: Dict, all_docs: List[Dict]):
        """渲染智能推荐"""
        st.markdown("### 🎯 智能推荐")
        
        # 计算相似度并排序
        similarities = []
        for doc in all_docs:
            if doc.get('id') != current_doc.get('id'):
                sim = self.calculate_similarity(current_doc, doc)
                similarities.append((doc, sim))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # 显示前3个推荐
        for doc, sim in similarities[:3]:
            if sim > 0.1:  # 最低相似度阈值
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**📄 {doc.get('name', '未知文档')}**")
                    st.caption(f"相似度: {sim:.2f} | {doc.get('chunks', 0)} 片段")
                with col2:
                    if st.button("查看", key=f"rec_{doc.get('id')}"):
                        self.show_document_details(doc)
    
    def batch_tag_documents(self):
        """批量标签文档"""
        st.success(f"为 {len(self.selected_docs)} 个文档添加标签功能开发中...")
    
    def batch_analyze_documents(self):
        """批量分析文档"""
        st.success(f"批量分析 {len(self.selected_docs)} 个文档功能开发中...")
    
    def batch_delete_documents(self):
        """批量删除文档"""
        st.warning(f"批量删除 {len(self.selected_docs)} 个文档功能开发中...")
    
    def show_document_details(self, doc: Dict):
        """显示文档详情"""
        st.info(f"显示 {doc.get('name', '文档')} 的详细信息...")

# 全局实例
enhanced_kb_manager = EnhancedKBManager()
