#!/usr/bin/env python3
"""
用户引导组件
在关键位置提供操作指导和帮助信息
"""

import streamlit as st

class UserGuidance:
    """用户引导助手"""
    
    @staticmethod
    def show_first_time_guidance():
        """首次使用引导"""
        if 'first_time_user' not in st.session_state:
            st.session_state.first_time_user = True
        
        if st.session_state.first_time_user:
            with st.info("👋 欢迎使用 RAG Pro Max！"):
                st.write("**快速开始：**")
                st.write("1. 点击左侧 '➕ 新建知识库' 创建您的第一个知识库")
                st.write("2. 上传文档或输入文本内容")
                st.write("3. 等待处理完成后开始提问")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🚀 开始使用", key="start_using"):
                        st.session_state.first_time_user = False
                        st.rerun()
                with col2:
                    if st.button("📖 查看详细教程", key="view_tutorial"):
                        st.session_state.show_tutorial = True
    
    @staticmethod
    def show_empty_kb_guidance():
        """空知识库引导"""
        st.info("📚 **知识库为空**")
        st.write("您的知识库还没有任何内容，请先添加文档：")
        st.write("• 点击 '📤 添加文档' 上传文件")
        st.write("• 或使用 '📝 粘贴文本' 直接输入内容")
        st.write("• 也可以通过 '🌐 网页抓取' 从网站获取内容")
    
    @staticmethod
    def show_no_kb_selected_guidance():
        """未选择知识库引导"""
        st.warning("🎯 **请选择知识库**")
        st.write("要开始对话，请先：")
        st.write("1. 在左侧选择一个现有的知识库")
        st.write("2. 或点击 '➕ 新建知识库' 创建新的知识库")
        st.write("3. 选择后系统会自动加载，显示 ✅ 表示准备就绪")
    
    @staticmethod
    def show_processing_guidance():
        """处理中引导"""
        st.info("⏳ **正在处理中**")
        st.write("系统正在处理您的请求，请稍候...")
        st.write("• 大文件可能需要更长时间")
        st.write("• 请不要关闭浏览器或刷新页面")
        st.write("• 处理完成后会自动显示结果")
    
    @staticmethod
    def show_upload_guidance():
        """文件上传引导"""
        with st.expander("💡 上传提示", expanded=False):
            st.write("**支持的文件格式：**")
            st.write("• PDF文档 (.pdf)")
            st.write("• Word文档 (.docx, .doc)")
            st.write("• 文本文件 (.txt, .md)")
            st.write("• Excel表格 (.xlsx, .xls)")
            
            st.write("**上传建议：**")
            st.write("• 单个文件建议不超过50MB")
            st.write("• 可以同时上传多个文件")
            st.write("• 图片较多的PDF建议开启OCR识别")
    
    @staticmethod
    def show_query_guidance():
        """查询引导"""
        with st.expander("💡 提问技巧", expanded=False):
            st.write("**如何提出好问题：**")
            st.write("• 尽量具体明确，避免过于宽泛")
            st.write("• 可以指定要查找的内容类型")
            st.write("• 使用关键词有助于提高准确性")
            
            st.write("**示例问题：**")
            st.write("• '产品的主要功能有哪些？'")
            st.write("• '如何配置数据库连接？'")
            st.write("• '文档中提到的注意事项'")
    
    @staticmethod
    def show_contextual_help(context: str):
        """根据上下文显示相关帮助"""
        help_content = {
            "knowledge_base_creation": {
                "title": "创建知识库帮助",
                "content": [
                    "知识库是存储和管理文档的容器",
                    "建议按主题或项目创建不同的知识库",
                    "名称要有意义，便于后续管理"
                ]
            },
            "document_upload": {
                "title": "文档上传帮助", 
                "content": [
                    "支持拖拽上传，更加便捷",
                    "可以同时选择多个文件",
                    "上传后会自动进行内容分析"
                ]
            },
            "query_interface": {
                "title": "查询界面帮助",
                "content": [
                    "在输入框中输入您的问题",
                    "系统会自动搜索相关内容",
                    "可以进行多轮对话"
                ]
            }
        }
        
        if context in help_content:
            help_info = help_content[context]
            with st.expander(f"❓ {help_info['title']}", expanded=False):
                for item in help_info['content']:
                    st.write(f"• {item}")

# 便捷函数
def show_guidance(guidance_type: str, **kwargs):
    """显示指定类型的用户引导"""
    guidance_methods = {
        "first_time": UserGuidance.show_first_time_guidance,
        "empty_kb": UserGuidance.show_empty_kb_guidance,
        "no_kb_selected": UserGuidance.show_no_kb_selected_guidance,
        "processing": UserGuidance.show_processing_guidance,
        "upload": UserGuidance.show_upload_guidance,
        "query": UserGuidance.show_query_guidance
    }
    
    if guidance_type in guidance_methods:
        guidance_methods[guidance_type]()
    
def contextual_help(context: str):
    """显示上下文相关帮助"""
    UserGuidance.show_contextual_help(context)
