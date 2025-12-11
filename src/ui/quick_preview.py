#!/usr/bin/env python3
"""快速预览功能"""

import streamlit as st
from typing import Dict, Any

class QuickPreview:
    """快速预览组件"""
    
    @staticmethod
    def render_hover_preview(doc: Dict[str, Any], key: str):
        """渲染悬停预览"""
        preview_content = QuickPreview.generate_preview_content(doc)
        
        # 使用streamlit的popover功能（如果可用）
        with st.popover(f"📄 {doc.get('name', '文档')}", use_container_width=False):
            st.markdown("### 📋 文档预览")
            st.markdown(preview_content)
            
            # 快速操作按钮
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 查看详情", key=f"preview_detail_{key}"):
                    st.session_state[f'show_detail_{key}'] = True
            with col2:
                if st.button("💬 开始对话", key=f"preview_chat_{key}"):
                    st.session_state['chat_with_doc'] = doc.get('id')
            with col3:
                if st.button("📊 分析", key=f"preview_analyze_{key}"):
                    st.session_state['analyze_doc'] = doc.get('id')
    
    @staticmethod
    def generate_preview_content(doc: Dict[str, Any]) -> str:
        """生成预览内容"""
        content = []
        
        # 基本信息
        content.append(f"**📊 基本信息**")
        content.append(f"• 类型: {doc.get('type', '未知')}")
        content.append(f"• 大小: {doc.get('size_mb', 0):.1f}MB")
        content.append(f"• 片段: {doc.get('chunks', 0)} 个")
        content.append("")
        
        # 质量信息
        content.append(f"**🎯 质量评估**")
        content.append(f"• 质量: {doc.get('quality', '未知')}")
        content.append(f"• 健康度: {doc.get('health', 'N/A')}")
        content.append("")
        
        # 使用统计
        content.append(f"**📈 使用统计**")
        content.append(f"• 命中: {doc.get('hits', 0)} 次")
        content.append(f"• 热度: {doc.get('temperature', '❄️')}")
        content.append("")
        
        # 关键词
        keywords = doc.get('keywords', [])
        if keywords:
            content.append(f"**🏷️ 关键词**")
            content.append(" • ".join(keywords[:5]))
            content.append("")
        
        # 摘要
        summary = doc.get('summary', '')
        if summary:
            content.append(f"**📝 摘要**")
            content.append(f"> {summary[:100]}{'...' if len(summary) > 100 else ''}")
        
        return "\n".join(content)
    
    @staticmethod
    def render_inline_preview(doc: Dict[str, Any], expanded: bool = False):
        """渲染内联预览"""
        if expanded:
            # 展开状态
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**📊 详细信息**")
                st.write(f"📄 类型: {doc.get('type', '未知')}")
                st.write(f"💾 大小: {doc.get('size_mb', 0):.1f}MB")
                st.write(f"📦 片段: {doc.get('chunks', 0)} 个")
                st.write(f"🔤 字符: ~{doc.get('chars', 0):,}")
                
                # 质量指标
                st.markdown("**🎯 质量指标**")
                quality = doc.get('quality', '未知')
                health = doc.get('health_score', 0)
                st.write(f"🎉 质量: {quality}")
                st.progress(health / 100 if isinstance(health, (int, float)) else 0)
            
            with col2:
                st.markdown("**📈 使用分析**")
                st.write(f"🔥 命中: {doc.get('hits', 0)} 次")
                st.write(f"⭐ 平均得分: {doc.get('avg_score', 0):.3f}")
                st.write(f"🕐 最后访问: {doc.get('last_access', '从未')}")
                
                # 标签
                tags = doc.get('tags', [])
                if tags:
                    st.markdown("**🏷️ 标签**")
                    for tag in tags[:3]:
                        st.markdown(f"`{tag}`")
            
            # 摘要
            summary = doc.get('summary', '')
            if summary:
                st.markdown("**📝 智能摘要**")
                st.info(summary)
            
            # 关键词云
            keywords = doc.get('keywords', [])
            if keywords:
                st.markdown("**🔍 关键词**")
                keyword_text = " • ".join(keywords[:10])
                st.markdown(f"*{keyword_text}*")
            
            st.markdown("---")
        else:
            # 折叠状态 - 显示简要信息
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.caption(f"📦 {doc.get('chunks', 0)} 片段")
            with col2:
                st.caption(f"💾 {doc.get('size_mb', 0):.1f}MB")
            with col3:
                st.caption(f"🎉 {doc.get('quality', '未知')}")
            with col4:
                st.caption(f"🔥 {doc.get('hits', 0)} 命中")

# 全局实例
quick_preview = QuickPreview()
