#!/usr/bin/env python3
"""
统一文档处理组件
整合文档上传、预览、处理的所有相关功能
"""

import streamlit as st
import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import mimetypes

class UnifiedDocumentProcessor:
    """统一文档处理器"""
    
    def __init__(self, upload_dir: str = "temp_uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(exist_ok=True)
        
        # 支持的文件类型
        self.supported_types = {
            'pdf': ['.pdf'],
            'text': ['.txt', '.md', '.rtf'],
            'office': ['.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
            'code': ['.py', '.js', '.html', '.css', '.json', '.xml']
        }
    
    def render_upload_interface(self, key_prefix: str = "upload") -> List[Any]:
        """渲染统一的文件上传界面"""
        st.markdown("##### 📁 文档上传")
        
        # 上传方式选择
        upload_method = st.radio(
            "选择上传方式",
            ["单文件上传", "批量上传", "文件夹上传"],
            key=f"{key_prefix}_method"
        )
        
        uploaded_files = []
        
        if upload_method == "单文件上传":
            uploaded_file = st.file_uploader(
                "选择文件",
                type=self._get_all_extensions(),
                key=f"{key_prefix}_single"
            )
            if uploaded_file:
                uploaded_files = [uploaded_file]
        
        elif upload_method == "批量上传":
            uploaded_files = st.file_uploader(
                "选择多个文件",
                type=self._get_all_extensions(),
                accept_multiple_files=True,
                key=f"{key_prefix}_multiple"
            )
        
        elif upload_method == "文件夹上传":
            st.info("📂 请使用批量上传功能选择文件夹中的所有文件")
            uploaded_files = st.file_uploader(
                "选择文件夹中的所有文件",
                type=self._get_all_extensions(),
                accept_multiple_files=True,
                key=f"{key_prefix}_folder"
            )
        
        # 显示上传的文件
        if uploaded_files:
            self._show_upload_preview(uploaded_files, key_prefix)
        
        return uploaded_files
    
    def _show_upload_preview(self, uploaded_files: List[Any], key_prefix: str):
        """显示上传文件预览"""
        st.write(f"**已选择 {len(uploaded_files)} 个文件:**")
        
        for i, file in enumerate(uploaded_files):
            with st.expander(f"📄 {file.name}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**大小**: {self._format_file_size(file.size)}")
                    st.write(f"**类型**: {self._get_file_category(file.name)}")
                
                with col2:
                    if st.button("👁️ 预览", key=f"{key_prefix}_preview_{i}"):
                        self._show_file_preview(file)
                
                with col3:
                    if st.button("🗑️ 移除", key=f"{key_prefix}_remove_{i}"):
                        st.session_state[f"remove_{key_prefix}_{i}"] = True
    
    def _show_file_preview(self, uploaded_file):
        """显示文件预览"""
        file_ext = Path(uploaded_file.name).suffix.lower()
        
        if file_ext in ['.txt', '.md', '.py', '.js', '.html', '.css', '.json']:
            # 文本文件预览
            try:
                content = uploaded_file.read().decode('utf-8')
                st.code(content[:1000] + "..." if len(content) > 1000 else content)
            except:
                st.error("无法预览此文件")
        
        elif file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            # 图片预览
            st.image(uploaded_file, caption=uploaded_file.name, use_column_width=True)
        
        elif file_ext == '.pdf':
            st.info("PDF文件预览需要处理后才能显示")
        
        else:
            st.info(f"不支持预览 {file_ext} 格式的文件")
    
    def process_uploaded_files(self, uploaded_files: List[Any], 
                             options: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理上传的文件"""
        if not uploaded_files:
            return {"success": False, "message": "没有文件需要处理"}
        
        options = options or {}
        results = {
            "success": True,
            "processed_files": [],
            "failed_files": [],
            "total_files": len(uploaded_files)
        }
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                # 更新进度
                progress = (i + 1) / len(uploaded_files)
                progress_bar.progress(progress)
                status_text.text(f"处理中: {uploaded_file.name} ({i+1}/{len(uploaded_files)})")
                
                # 保存文件到临时目录
                temp_path = self._save_temp_file(uploaded_file)
                
                # 处理文件
                processed_result = self._process_single_file(
                    temp_path, 
                    uploaded_file.name,
                    options
                )
                
                if processed_result["success"]:
                    results["processed_files"].append(processed_result)
                else:
                    results["failed_files"].append({
                        "filename": uploaded_file.name,
                        "error": processed_result.get("error", "处理失败")
                    })
            
            except Exception as e:
                results["failed_files"].append({
                    "filename": uploaded_file.name,
                    "error": str(e)
                })
        
        # 清理进度显示
        progress_bar.empty()
        status_text.empty()
        
        # 显示处理结果
        self._show_processing_results(results)
        
        return results
    
    def _save_temp_file(self, uploaded_file) -> str:
        """保存上传文件到临时目录"""
        temp_path = self.upload_dir / uploaded_file.name
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return str(temp_path)
    
    def _process_single_file(self, file_path: str, filename: str, 
                           options: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个文件"""
        try:
            file_ext = Path(filename).suffix.lower()
            file_category = self._get_file_category(filename)
            
            result = {
                "success": True,
                "filename": filename,
                "path": file_path,
                "category": file_category,
                "size": os.path.getsize(file_path),
                "processed_content": None
            }
            
            # 根据文件类型进行处理
            if file_category == "text":
                result["processed_content"] = self._process_text_file(file_path)
            elif file_category == "pdf":
                result["processed_content"] = self._process_pdf_file(file_path, options)
            elif file_category == "office":
                result["processed_content"] = self._process_office_file(file_path)
            elif file_category == "image":
                result["processed_content"] = self._process_image_file(file_path, options)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "filename": filename,
                "error": str(e)
            }
    
    def _process_text_file(self, file_path: str) -> str:
        """处理文本文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _process_pdf_file(self, file_path: str, options: Dict[str, Any]) -> str:
        """处理PDF文件"""
        # 这里可以集成现有的PDF处理逻辑
        return f"PDF文件已处理: {file_path}"
    
    def _process_office_file(self, file_path: str) -> str:
        """处理Office文件"""
        # 这里可以集成现有的Office文件处理逻辑
        return f"Office文件已处理: {file_path}"
    
    def _process_image_file(self, file_path: str, options: Dict[str, Any]) -> str:
        """处理图片文件 - 使用OCR提取文字"""
        try:
            # 导入多模态处理器
            from .multimodal_processor import MultimodalProcessor
            
            processor = MultimodalProcessor()
            result = processor.extract_text_from_image(file_path)
            
            if result.get('error'):
                return f"图片OCR处理失败: {result['error']}"
            
            extracted_text = result.get('text', '')
            confidence = result.get('confidence', 0)
            
            if not extracted_text.strip():
                return "图片中未检测到文字内容"
            
            # 返回格式化的OCR结果
            return f"""图片OCR提取结果 (置信度: {confidence:.1f}%):

{extracted_text}

--- 图片信息 ---
文件: {os.path.basename(file_path)}
尺寸: {result.get('image_size', 'Unknown')}
格式: {result.get('format', 'Unknown')}
字数: {result.get('word_count', 0)}
"""
            
        except ImportError:
            return "OCR功能不可用，请安装相关依赖包 (pillow, pytesseract)"
        except Exception as e:
            return f"图片处理失败: {str(e)}"
    
    def _show_processing_results(self, results: Dict[str, Any]):
        """显示处理结果"""
        if results["success"]:
            st.success(f"✅ 处理完成！成功: {len(results['processed_files'])}, 失败: {len(results['failed_files'])}")
        
        if results["processed_files"]:
            with st.expander("✅ 处理成功的文件"):
                for file_result in results["processed_files"]:
                    st.write(f"📄 {file_result['filename']} ({file_result['category']})")
        
        if results["failed_files"]:
            with st.expander("❌ 处理失败的文件"):
                for failed_file in results["failed_files"]:
                    st.error(f"📄 {failed_file['filename']}: {failed_file['error']}")
    
    def _get_file_category(self, filename: str) -> str:
        """获取文件类别"""
        ext = Path(filename).suffix.lower()
        
        for category, extensions in self.supported_types.items():
            if ext in extensions:
                return category
        
        return "unknown"
    
    def _get_all_extensions(self) -> List[str]:
        """获取所有支持的文件扩展名"""
        extensions = []
        for ext_list in self.supported_types.values():
            extensions.extend([ext[1:] for ext in ext_list])  # 移除点号
        return extensions
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

# 全局实例
unified_document_processor = UnifiedDocumentProcessor()

# 便捷函数
def render_upload_interface(key_prefix: str = "upload") -> List[Any]:
    """渲染文档上传界面 - 便捷函数"""
    return unified_document_processor.render_upload_interface(key_prefix)

def process_uploaded_files(uploaded_files: List[Any], 
                         options: Dict[str, Any] = None) -> Dict[str, Any]:
    """处理上传文件 - 便捷函数"""
    return unified_document_processor.process_uploaded_files(uploaded_files, options)

def show_file_preview(uploaded_file):
    """显示文件预览 - 便捷函数"""
    return unified_document_processor._show_file_preview(uploaded_file)
