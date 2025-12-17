#!/usr/bin/env python3
"""知识图谱可视化组件"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Tuple
import numpy as np

class KnowledgeGraph:
    """知识图谱可视化"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.node_colors = px.colors.qualitative.Set3
    
    def create_document_graph(self, documents: List[Dict[str, Any]]) -> go.Figure:
        """创建文档关系图"""
        if len(documents) < 2:
            return self._create_empty_graph()
        
        # 清空图
        self.graph.clear()
        
        # 添加节点
        for doc in documents:
            doc_id = doc.get('id', doc.get('name', 'unknown'))
            self.graph.add_node(doc_id, **doc)
        
        # 添加边（基于相似度）
        for i, doc1 in enumerate(documents):
            for j, doc2 in enumerate(documents[i+1:], i+1):
                similarity = self._calculate_document_similarity(doc1, doc2)
                if similarity > 0.2:  # 相似度阈值
                    doc1_id = doc1.get('id', doc1.get('name', f'doc_{i}'))
                    doc2_id = doc2.get('id', doc2.get('name', f'doc_{j}'))
                    self.graph.add_edge(doc1_id, doc2_id, weight=similarity)
        
        return self._render_graph()
    
    def _calculate_document_similarity(self, doc1: Dict, doc2: Dict) -> float:
        """计算文档相似度"""
        # 基于关键词的相似度
        keywords1 = set(doc1.get('keywords', []))
        keywords2 = set(doc2.get('keywords', []))
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Jaccard相似度
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        jaccard = intersection / union if union > 0 else 0.0
        
        # 基于文档类型的相似度
        type_sim = 0.3 if doc1.get('type') == doc2.get('type') else 0.0
        
        # 基于大小的相似度（大小相近的文档可能相关）
        size1 = doc1.get('size_mb', 0)
        size2 = doc2.get('size_mb', 0)
        if size1 > 0 and size2 > 0:
            size_ratio = min(size1, size2) / max(size1, size2)
            size_sim = size_ratio * 0.2
        else:
            size_sim = 0.0
        
        return jaccard + type_sim + size_sim
    
    def _render_graph(self) -> go.Figure:
        """渲染图形"""
        if len(self.graph.nodes()) == 0:
            return self._create_empty_graph()
        
        # 使用spring布局
        pos = nx.spring_layout(self.graph, k=3, iterations=50)
        
        # 准备节点数据
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        node_color = []
        node_info = []
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            
            # 节点信息
            node_data = self.graph.nodes[node]
            name = node_data.get('name', node)[:15]
            chunks = node_data.get('chunks', 0)
            size_mb = node_data.get('size_mb', 0)
            
            node_text.append(name)
            node_size.append(max(10, chunks * 0.5 + 10))  # 基于片段数调整大小
            
            # 根据文档类型着色
            doc_type = node_data.get('type', 'unknown')
            type_colors = {
                'PDF': '#FF6B6B',
                'DOCX': '#4ECDC4', 
                'TXT': '#45B7D1',
                'MD': '#96CEB4',
                'XLSX': '#FFEAA7',
                'unknown': '#DDA0DD'
            }
            node_color.append(type_colors.get(doc_type, '#DDA0DD'))
            
            # 悬停信息
            info = f"<b>{name}</b><br>"
            info += f"类型: {doc_type}<br>"
            info += f"片段: {chunks}<br>"
            info += f"大小: {size_mb:.1f}MB<br>"
            info += f"质量: {node_data.get('quality', '未知')}"
            node_info.append(info)
        
        # 准备边数据
        edge_x = []
        edge_y = []
        edge_info = []
        
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
            weight = self.graph.edges[edge].get('weight', 0)
            edge_info.append(f"相似度: {weight:.3f}")
        
        # 创建图形
        fig = go.Figure()
        
        # 添加边
        fig.add_trace(go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color='rgba(125,125,125,0.5)'),
            hoverinfo='none',
            mode='lines',
            showlegend=False
        ))
        
        # 添加节点
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            marker=dict(
                size=node_size,
                color=node_color,
                line=dict(width=2, color='white'),
                opacity=0.8
            ),
            text=node_text,
            textposition="middle center",
            textfont=dict(size=10, color='white'),
            hoverinfo='text',
            hovertext=node_info,
            showlegend=False
        ))
        
        # 布局设置
        fig.update_layout(
            title={
                'text': "📊 知识库文档关系图",
                'x': 0.5,
                'xanchor': 'center'
            },
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            annotations=[ 
                dict(
                    text="节点大小表示片段数量，连线表示文档相似度",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.005, y=-0.002,
                    xanchor='left', yanchor='bottom',
                    font=dict(color='gray', size=12)
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            height=500
        )
        
        return fig
    
    def _create_empty_graph(self) -> go.Figure:
        """创建空图形"""
        fig = go.Figure()
        fig.add_annotation(
            text="📭 需要至少2个文档才能生成知识图谱",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color='gray')
        )
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=400
        )
        return fig
    
    def create_topic_clusters(self, documents: List[Dict[str, Any]]) -> go.Figure:
        """创建主题聚类图"""
        if len(documents) < 3:
            return self._create_empty_graph()
        
        # 模拟主题聚类（实际应用中可以使用LDA或其他聚类算法）
        topics = self._extract_topics(documents)
        
        # 创建散点图
        fig = go.Figure()
        
        colors = px.colors.qualitative.Set1
        
        for i, (topic, docs) in enumerate(topics.items()):
            x_coords = []
            y_coords = []
            names = []
            infos = []
            
            # 为每个主题的文档生成坐标
            angle_step = 2 * np.pi / len(docs)
            radius = 1 + i * 0.5
            
            for j, doc in enumerate(docs):
                angle = j * angle_step
                x = radius * np.cos(angle) + np.random.normal(0, 0.1)
                y = radius * np.sin(angle) + np.random.normal(0, 0.1)
                
                x_coords.append(x)
                y_coords.append(y)
                names.append(doc.get('name', 'unknown')[:15])
                
                info = f"<b>{doc.get('name', 'unknown')}</b><br>"
                info += f"主题: {topic}<br>"
                info += f"片段: {doc.get('chunks', 0)}<br>"
                info += f"大小: {doc.get('size_mb', 0):.1f}MB"
                infos.append(info)
            
            fig.add_trace(go.Scatter(
                x=x_coords, y=y_coords,
                mode='markers+text',
                marker=dict(
                    size=[max(10, doc.get('chunks', 0) * 0.3 + 8) for doc in docs],
                    color=colors[i % len(colors)],
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                text=names,
                textposition="middle center",
                textfont=dict(size=9, color='white'),
                hovertext=infos,
                hoverinfo='text',
                name=f"主题: {topic}"
            ))
        
        fig.update_layout(
            title="🎯 文档主题聚类分析",
            showlegend=True,
            height=500,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig
    
    def _extract_topics(self, documents: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
        """提取文档主题（简化版）"""
        topics = {}
        
        for doc in documents:
            # 基于文档类型和关键词简单分类
            doc_type = doc.get('type', 'unknown')
            keywords = doc.get('keywords', [])
            
            # 简单的主题分类逻辑
            if any(kw in ['技术', '代码', '开发', '编程'] for kw in keywords):
                topic = '技术文档'
            elif any(kw in ['管理', '流程', '规范', '制度'] for kw in keywords):
                topic = '管理文档'
            elif any(kw in ['学习', '教育', '培训', '知识'] for kw in keywords):
                topic = '学习资料'
            else:
                topic = f'{doc_type}文档'
            
            if topic not in topics:
                topics[topic] = []
            topics[topic].append(doc)
        
        return topics

# 全局实例
knowledge_graph = KnowledgeGraph()
