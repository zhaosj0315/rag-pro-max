"""v2.0 功能集成模块"""

import streamlit as st
from typing import List, Dict, Any, Optional
import os

from ..kb.kb_manager import KBManager
from ..processors.multimodal_processor import MultimodalProcessor
from ..logging import LogManager

logger = LogManager()


class V2Integration:
    """v2.0 功能集成器"""
    
    def __init__(self):
        self.kb_manager = KBManager()
        self.multimodal_processor = MultimodalProcessor()
    
    def render_incremental_update_ui(self, kb_name: str):
        """渲染增量更新UI"""
        if not kb_name:
            st.warning("请先选择知识库")
            return
        
        st.subheader("📈 增量更新")
        
        # 获取增量统计
        updater = self.kb_manager.get_incremental_updater(kb_name)
        if updater:
            stats = updater.get_stats()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("已跟踪文件", stats['total_files'])
            with col2:
                if stats['last_update']:
                    import datetime
                    last_update = datetime.datetime.fromtimestamp(stats['last_update'])
                    st.metric("最后更新", last_update.strftime('%Y-%m-%d %H:%M'))
                else:
                    st.metric("最后更新", "从未")
        
        # 文件上传区域
        uploaded_files = st.file_uploader(
            "选择要增量更新的文件",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'docx', 'md', 'xlsx', 'pptx', 'csv', 'html', 'json', 'zip']
        )
        
        if uploaded_files:
            # 保存临时文件
            temp_files = []
            for uploaded_file in uploaded_files:
                temp_path = os.path.join("temp_uploads", uploaded_file.name)
                os.makedirs("temp_uploads", exist_ok=True)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                temp_files.append(temp_path)
            
            # 检查变化
            if st.button("🔍 检查文件变化"):
                with st.spinner("检查文件变化中..."):
                    changes = self.kb_manager.check_incremental_changes(kb_name, temp_files)
                    
                    if changes:
                        st.success("文件变化检查完成")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write("**新文件:**")
                            for f in changes['new']:
                                st.write(f"✨ {os.path.basename(f)}")
                        
                        with col2:
                            st.write("**修改文件:**")
                            for f in changes['modified']:
                                st.write(f"📝 {os.path.basename(f)}")
                        
                        with col3:
                            st.write("**未变化:**")
                            for f in changes['unchanged']:
                                st.write(f"✅ {os.path.basename(f)}")
                        
                        # 存储到session state
                        st.session_state.incremental_changes = changes
                        st.session_state.temp_files = temp_files
            
            # 执行增量更新
            if hasattr(st.session_state, 'incremental_changes'):
                changes = st.session_state.incremental_changes
                files_to_process = changes['new'] + changes['modified']
                
                if files_to_process:
                    force_update = st.checkbox("强制更新所有文件")
                    
                    if st.button("🚀 执行增量更新"):
                        with st.spinner("执行增量更新中..."):
                            try:
                                # TODO: 集成实际的文档处理逻辑
                                # 这里需要调用文档处理器来处理文件
                                
                                # 标记文件已处理
                                self.kb_manager.mark_files_processed(kb_name, files_to_process)
                                
                                st.success(f"✅ 成功更新 {len(files_to_process)} 个文件")
                                
                                # 清理临时文件
                                for temp_file in st.session_state.get('temp_files', []):
                                    if os.path.exists(temp_file):
                                        os.remove(temp_file)
                                
                                # 清理session state
                                if 'incremental_changes' in st.session_state:
                                    del st.session_state.incremental_changes
                                if 'temp_files' in st.session_state:
                                    del st.session_state.temp_files
                                
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"增量更新失败: {str(e)}")
                                logger.log_error("增量更新失败", str(e))
                else:
                    st.info("没有需要更新的文件")
    
    def render_multimodal_ui(self, kb_name: str):
        """渲染多模态UI"""
        if not kb_name:
            st.warning("请先选择知识库")
            return
        
        st.subheader("🎨 多模态支持")
        
        # 显示支持的格式
        formats = self.multimodal_processor.get_supported_formats()
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**支持的图片格式:**")
            st.write(", ".join(formats['images']))
            st.write(f"OCR可用: {'✅' if formats['ocr_available'] else '❌'}")
        
        with col2:
            st.write("**支持的表格格式:**")
            st.write(", ".join(formats['tables']))
            st.write(f"表格提取可用: {'✅' if formats['table_extraction_available'] else '❌'}")
        
        # 多模态文件上传
        multimodal_files = st.file_uploader(
            "上传多模态文件（图片、表格等）",
            accept_multiple_files=True,
            type=['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'gif', 'pdf', 'xlsx', 'xls', 'csv']
        )
        
        if multimodal_files:
            if st.button("🔄 处理多模态文件"):
                with st.spinner("处理多模态文件中..."):
                    for uploaded_file in multimodal_files:
                        # 保存临时文件
                        temp_path = os.path.join("temp_uploads", uploaded_file.name)
                        os.makedirs("temp_uploads", exist_ok=True)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 处理文件
                        result = self.multimodal_processor.process_multimodal_file(temp_path)
                        
                        # 显示结果
                        st.write(f"**文件: {uploaded_file.name}**")
                        st.write(f"类型: {result['file_type']}")
                        
                        if result['text_content']:
                            with st.expander("提取的文本内容"):
                                st.text_area("", result['text_content'], height=200, key=f"text_{uploaded_file.name}")
                        
                        if result['images']:
                            with st.expander("图片OCR结果"):
                                for img in result['images']:
                                    ocr = img['ocr_result']
                                    st.write(f"置信度: {ocr.get('confidence', 0):.1f}%")
                                    st.write(f"词数: {ocr.get('word_count', 0)}")
                        
                        if result['tables']:
                            with st.expander("提取的表格"):
                                for table in result['tables']:
                                    st.write(f"表格 {table['table_id']} - 形状: {table['shape']}")
                                    st.dataframe(pd.DataFrame(table['data']))
                        
                        # 清理临时文件
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
        
        # 多模态查询
        st.subheader("🔍 多模态查询")
        
        query = st.text_input("输入查询问题")
        
        col1, col2 = st.columns(2)
        with col1:
            include_images = st.checkbox("包含图片内容", value=True)
        with col2:
            include_tables = st.checkbox("包含表格内容", value=True)
        
        if query and st.button("🚀 多模态查询"):
            with st.spinner("执行多模态查询中..."):
                try:
                    # TODO: 实现实际的多模态查询
                    st.info("多模态查询功能正在开发中...")
                    
                except Exception as e:
                    st.error(f"多模态查询失败: {str(e)}")
                    logger.log_error("多模态查询失败", str(e))
    
    def render_v2_features(self, kb_name: str):
        """渲染v2.0所有新功能"""
        st.header("🚀 RAG Pro Max v2.0 新功能")
        
        tab1, tab2 = st.tabs(["📈 增量更新", "🎨 多模态支持"])
        
        with tab1:
            self.render_incremental_update_ui(kb_name)
        
        with tab2:
            self.render_multimodal_ui(kb_name)
