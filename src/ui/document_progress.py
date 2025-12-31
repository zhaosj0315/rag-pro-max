#!/usr/bin/env python3
"""
文档处理进度显示组件
"""

import streamlit as st
import time
import os
from pathlib import Path

class DocumentProcessingProgress:
    def __init__(self):
        self.progress_bar = None
        self.status_text = None
        
    def start_processing(self, files):
        """开始处理文档，显示进度"""
        # 创建进度显示组件
        self.progress_bar = st.progress(0)
        self.status_text = st.empty()
        
        total_files = len(files) if isinstance(files, list) else 1
        
        for i, file in enumerate(files if isinstance(files, list) else [files]):
            # 更新进度
            progress = (i + 1) / total_files
            self.progress_bar.progress(progress)
            
            # 显示当前状态
            file_name = file.name if hasattr(file, 'name') else str(file)
            self.status_text.text(f"正在处理: {file_name} ({i+1}/{total_files})")
            
            # 模拟处理步骤
            self._process_file_with_steps(file, file_name)
        
        # 完成处理
        self.progress_bar.progress(1.0)
        self.status_text.success(f"✅ 处理完成！共处理 {total_files} 个文件")
        
        # 显示统计信息
        self._show_processing_stats(files)
    
    def _process_file_with_steps(self, file, file_name):
        """分步骤处理文件，显示详细状态"""
        steps = [
            "正在读取文件...",
            "正在分析内容...", 
            "正在提取文本...",
            "正在构建索引...",
            "正在保存数据..."
        ]
        
        for step in steps:
            self.status_text.text(f"{step} - {file_name}")
            time.sleep(0.3)  # 模拟处理时间
    
    def _show_processing_stats(self, files):
        """显示处理统计信息"""
        if not isinstance(files, list):
            files = [files]
        
        total_size = 0
        file_types = {}
        
        for file in files:
            if hasattr(file, 'size'):
                total_size += file.size
            
            if hasattr(file, 'name'):
                ext = Path(file.name).suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
        
        # 显示统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("文件数量", len(files))
        
        with col2:
            size_mb = total_size / (1024 * 1024) if total_size > 0 else 0
            st.metric("总大小", f"{size_mb:.1f} MB")
        
        with col3:
            st.metric("文件类型", len(file_types))
        
        # 显示文件类型分布
        if file_types:
            st.write("📊 文件类型分布:")
            for ext, count in file_types.items():
                st.write(f"  • {ext or '无扩展名'}: {count} 个")

# 全局实例
doc_progress = DocumentProcessingProgress()
