"""
v2.1 功能集成模块
整合实时监控、批量OCR、表格解析、多模态向量化功能
"""

import streamlit as st
from typing import Dict, List, Optional, Any
import os
from pathlib import Path
import logging

# 导入v2.1新功能
try:
    from ..monitoring.file_watcher import FileWatcherManager, file_watcher_manager
    from ..processors.batch_ocr_processor import BatchOCRProcessor, GPUAcceleratedOCR
    from ..processors.table_parser import SmartTableParser
    from ..processors.multimodal_vectorizer import MultiModalVectorizer, CrossModalRetriever
    V21_AVAILABLE = True
except ImportError as e:
    logging.warning(f"v2.1功能不可用: {e}")
    V21_AVAILABLE = False

class V21FeatureManager:
    """v2.1功能管理器"""
    
    def __init__(self):
        self.available = V21_AVAILABLE
        self.file_watcher = None
        self.ocr_processor = None
        self.table_parser = None
        self.multimodal_vectorizer = None
        self.cross_modal_retriever = None
        
        if self.available:
            self._initialize_components()
    
    def _initialize_components(self):
        """初始化v2.1组件"""
        try:
            # 文件监控
            self.file_watcher = file_watcher_manager
            
            # OCR处理器
            self.ocr_processor = BatchOCRProcessor()
            
            # 表格解析器
            self.table_parser = SmartTableParser()
            
            # 多模态向量化
            self.multimodal_vectorizer = MultiModalVectorizer()
            self.cross_modal_retriever = CrossModalRetriever(self.multimodal_vectorizer)
            
            logging.info("v2.1功能组件初始化完成")
            
        except Exception as e:
            logging.error(f"v2.1组件初始化失败: {e}")
            self.available = False
    
    def render_v21_sidebar(self):
        """渲染v2.1功能侧边栏"""
        if not self.available:
            st.sidebar.warning("⚠️ v2.1功能不可用")
            return
        
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🚀 v2.1 新功能")
        
        # 实时文件监控
        with st.sidebar.expander("📁 实时文件监控", expanded=False):
            self._render_file_watcher_controls()
        
        # 批量OCR优化
        with st.sidebar.expander("🔍 批量OCR处理", expanded=False):
            self._render_ocr_controls()
        
        # 表格智能解析
        with st.sidebar.expander("📊 表格智能解析", expanded=False):
            self._render_table_parser_controls()
        
        # 多模态检索
        with st.sidebar.expander("🎯 多模态检索", expanded=False):
            self._render_multimodal_controls()
    
    def _render_file_watcher_controls(self):
        """文件监控控制面板"""
        st.write("自动检测文件变化并更新知识库")
        
        # 监控状态
        if self.file_watcher:
            status = self.file_watcher.get_status()
            if status['is_running']:
                st.success(f"✅ 监控中 ({status['total_watchers']} 个路径)")
                if st.button("停止监控", key="stop_watcher"):
                    self.file_watcher.stop_watching()
                    st.rerun()
            else:
                st.info("📴 监控已停止")
                
                # 选择监控路径
                watch_path = st.text_input("监控路径", value="./temp_uploads")
                if st.button("开始监控", key="start_watcher"):
                    if os.path.exists(watch_path):
                        # 需要传入kb_manager
                        kb_manager = st.session_state.get('kb_manager')
                        if kb_manager:
                            success = self.file_watcher.start_watching(
                                watch_path, kb_manager, 
                                lambda msg: st.toast(msg)
                            )
                            if success:
                                st.success("监控已启动")
                                st.rerun()
                        else:
                            st.error("请先创建知识库")
                    else:
                        st.error("路径不存在")
    
    def _render_ocr_controls(self):
        """OCR控制面板"""
        st.write("批量处理图片文件，GPU加速OCR")
        
        # OCR设置
        max_workers = st.slider("并行线程数", 1, 16, 8, key="ocr_workers")
        use_gpu = st.checkbox("使用GPU加速", value=True, key="ocr_gpu")
        
        # 批量处理
        uploaded_images = st.file_uploader(
            "选择图片文件", 
            type=['png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            key="batch_ocr_upload"
        )
        
        if uploaded_images and st.button("开始批量OCR", key="start_batch_ocr"):
            self._process_batch_ocr(uploaded_images, max_workers, use_gpu)
    
    def _render_table_parser_controls(self):
        """表格解析控制面板"""
        st.write("智能解析表格结构和内容")
        
        # 表格文件上传
        table_file = st.file_uploader(
            "选择表格文件",
            type=['xlsx', 'csv', 'pdf'],
            key="table_upload"
        )
        
        if table_file and st.button("解析表格", key="parse_table"):
            self._process_table_file(table_file)
    
    def _render_multimodal_controls(self):
        """多模态控制面板"""
        st.write("跨模态内容检索")
        
        # 检索设置
        search_modalities = st.multiselect(
            "检索模态",
            ['text', 'image', 'table'],
            default=['text', 'image'],
            key="search_modalities"
        )
        
        similarity_threshold = st.slider(
            "相似度阈值", 0.0, 1.0, 0.7, 0.1,
            key="multimodal_threshold"
        )
        
        # 存储统计
        if self.cross_modal_retriever:
            stats = self.cross_modal_retriever.get_statistics()
            st.write("**内容统计:**")
            for modality, count in stats.items():
                st.write(f"- {modality}: {count} 项")
    
    def _process_batch_ocr(self, uploaded_images, max_workers: int, use_gpu: bool):
        """处理批量OCR"""
        if not self.ocr_processor:
            st.error("OCR处理器未初始化")
            return
        
        # 保存上传的图片
        temp_paths = []
        for img in uploaded_images:
            temp_path = f"./temp_uploads/{img.name}"
            with open(temp_path, "wb") as f:
                f.write(img.getbuffer())
            temp_paths.append(temp_path)
        
        # 创建进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(current, total):
            progress = current / total
            progress_bar.progress(progress)
            status_text.text(f"处理中: {current}/{total}")
        
        try:
            # 批量处理
            self.ocr_processor.max_workers = max_workers
            self.ocr_processor.use_gpu = use_gpu
            
            results = self.ocr_processor.process_batch(temp_paths, progress_callback)
            
            # 显示结果
            st.success(f"✅ 处理完成，共 {len(results)} 个文件")
            
            for result in results:
                if result['error']:
                    st.error(f"❌ {Path(result['path']).name}: {result['error']}")
                else:
                    with st.expander(f"📄 {Path(result['path']).name}"):
                        st.write(f"**置信度:** {result.get('confidence', 0):.1f}%")
                        st.text_area("识别文本", result['text'], height=100)
        
        except Exception as e:
            st.error(f"批量OCR处理失败: {e}")
        
        finally:
            # 清理临时文件
            for path in temp_paths:
                try:
                    os.remove(path)
                except:
                    pass
    
    def _process_table_file(self, table_file):
        """处理表格文件"""
        if not self.table_parser:
            st.error("表格解析器未初始化")
            return
        
        # 保存文件
        temp_path = f"./temp_uploads/{table_file.name}"
        with open(temp_path, "wb") as f:
            f.write(table_file.getbuffer())
        
        try:
            # 解析表格
            results = self.table_parser.parse_table(temp_path)
            
            if not results:
                st.warning("未检测到表格")
                return
            
            st.success(f"✅ 检测到 {len(results)} 个表格")
            
            # 显示解析结果
            for i, result in enumerate(results):
                with st.expander(f"📊 表格 {i+1}"):
                    # 基本信息
                    structure = result['structure']
                    st.write(f"**行数:** {structure['rows']}")
                    st.write(f"**列数:** {structure['columns']}")
                    st.write(f"**列名:** {', '.join(structure['headers'])}")
                    
                    # 数据预览
                    st.write("**数据预览:**")
                    st.dataframe(result['data'].head(10))
                    
                    # 结构信息
                    with st.expander("结构分析"):
                        st.json(structure)
        
        except Exception as e:
            st.error(f"表格解析失败: {e}")
        
        finally:
            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass
    
    def enhance_knowledge_base(self, kb_manager, file_path: str) -> Dict:
        """增强知识库处理（集成v2.1功能）"""
        enhancements = {
            'ocr_results': [],
            'table_results': [],
            'multimodal_vectors': []
        }
        
        if not self.available:
            return enhancements
        
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # 图片OCR处理
            if file_ext in ['.png', '.jpg', '.jpeg']:
                if self.ocr_processor:
                    ocr_result = self.ocr_processor.process_single_image(file_path)
                    enhancements['ocr_results'].append(ocr_result)
            
            # 表格解析
            if file_ext in ['.xlsx', '.csv', '.pdf']:
                if self.table_parser:
                    table_results = self.table_parser.parse_table(file_path)
                    enhancements['table_results'].extend(table_results)
            
            # 多模态向量化
            if self.multimodal_vectorizer:
                # 文本向量
                if hasattr(kb_manager, 'get_document_text'):
                    text = kb_manager.get_document_text(file_path)
                    if text:
                        text_vector = self.multimodal_vectorizer.encode_text(text)
                        
                        # 图片向量
                        image_vector = None
                        if file_ext in ['.png', '.jpg', '.jpeg']:
                            image_vector = self.multimodal_vectorizer.encode_image(file_path)
                        
                        # 融合向量
                        if text_vector is not None or image_vector is not None:
                            fused_vector = self.multimodal_vectorizer.create_multimodal_vector(
                                text_vector=text_vector,
                                image_vector=image_vector
                            )
                            if fused_vector is not None:
                                enhancements['multimodal_vectors'].append({
                                    'file_path': file_path,
                                    'vector': fused_vector,
                                    'modalities': ['text'] + (['image'] if image_vector is not None else [])
                                })
        
        except Exception as e:
            logging.error(f"v2.1增强处理失败: {e}")
        
        return enhancements

# 全局v2.1功能管理器
v21_manager = V21FeatureManager()
