#!/usr/bin/env python3
"""
统一显示组件
整合系统状态、文件列表等显示相关的UI组件
"""

import streamlit as st
import psutil
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

class UnifiedDisplayRenderer:
    """统一显示渲染器"""
    
    def render_system_stats(self, show_detailed: bool = False) -> None:
        """渲染系统状态统计"""
        col1, col2, col3 = st.columns(3)
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        with col1:
            st.metric(
                label="🖥️ CPU使用率",
                value=f"{cpu_percent:.1f}%",
                delta=None
            )
        
        # 内存使用率
        memory = psutil.virtual_memory()
        with col2:
            st.metric(
                label="💾 内存使用率", 
                value=f"{memory.percent:.1f}%",
                delta=f"{memory.used / 1024**3:.1f}GB"
            )
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        with col3:
            st.metric(
                label="💿 磁盘使用率",
                value=f"{disk.percent:.1f}%", 
                delta=f"{disk.free / 1024**3:.1f}GB 可用"
            )
        
        if show_detailed:
            with st.expander("📊 详细系统信息"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**CPU信息**")
                    st.write(f"- 核心数: {psutil.cpu_count()}")
                    st.write(f"- 频率: {psutil.cpu_freq().current:.0f} MHz")
                
                with col2:
                    st.write("**内存信息**") 
                    st.write(f"- 总内存: {memory.total / 1024**3:.1f}GB")
                    st.write(f"- 可用内存: {memory.available / 1024**3:.1f}GB")
    
    def render_file_list(self, files: List[Dict[str, Any]], 
                        show_actions: bool = True,
                        key_prefix: str = "files") -> Optional[str]:
        """渲染文件列表"""
        if not files:
            st.info("📁 暂无文件")
            return None
        
        selected_file = None
        
        for i, file_info in enumerate(files):
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    # 文件名和图标
                    icon = self._get_file_icon(file_info.get('name', ''))
                    st.write(f"{icon} **{file_info.get('name', 'Unknown')}")
                    
                    # 文件信息
                    size = file_info.get('size', 0)
                    size_str = self._format_file_size(size)
                    st.caption(f"大小: {size_str}")
                
                with col2:
                    # 文件状态
                    status = file_info.get('status', 'unknown')
                    status_color = {
                        'processed': '🟢',
                        'processing': '🟡', 
                        'error': '🔴',
                        'pending': '⚪'
                    }.get(status, '⚫')
                    
                    st.write(f"{status_color} {status.title()}")
                    
                    # 修改时间
                    if 'modified' in file_info:
                        st.caption(f"修改: {file_info['modified']}")
                
                with col3:
                    if show_actions:
                        # 操作按钮
                        if st.button("👁️", key=f"{key_prefix}_view_{i}", help="预览"):
                            selected_file = file_info.get('path')
                        
                        if st.button("🗑️", key=f"{key_prefix}_delete_{i}", help="删除"):
                            st.session_state[f"delete_{key_prefix}_{i}"] = True
        
        return selected_file
    
    def render_progress_panel(self, tasks: List[Dict[str, Any]], 
                            title: str = "📊 处理进度") -> None:
        """渲染进度面板"""
        st.markdown(f"##### {title}")
        
        if not tasks:
            st.info("暂无任务")
            return
        
        for task in tasks:
            task_name = task.get('name', 'Unknown Task')
            progress = task.get('progress', 0)
            status = task.get('status', 'pending')
            
            # 进度条
            st.write(f"**{task_name}**")
            progress_bar = st.progress(progress / 100)
            
            # 状态信息
            col1, col2 = st.columns([3, 1])
            with col1:
                if 'message' in task:
                    st.caption(task['message'])
            
            with col2:
                status_emoji = {
                    'completed': '✅',
                    'running': '🔄', 
                    'error': '❌',
                    'pending': '⏳'
                }.get(status, '❓')
                st.write(f"{status_emoji} {status.title()}")
    
    def _get_file_icon(self, filename: str) -> str:
        """获取文件图标"""
        ext = Path(filename).suffix.lower()
        icons = {
            '.pdf': '📄',
            '.txt': '📝', 
            '.docx': '📘',
            '.xlsx': '📊',
            '.pptx': '📋',
            '.md': '📖',
            '.json': '🔧',
            '.py': '🐍',
            '.jpg': '🖼️',
            '.png': '🖼️',
            '.gif': '🖼️'
        }
        return icons.get(ext, '📁')
    
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
unified_display_renderer = UnifiedDisplayRenderer()

# 便捷函数
def render_system_stats(show_detailed: bool = False) -> None:
    """渲染系统状态 - 便捷函数"""
    return unified_display_renderer.render_system_stats(show_detailed)

def render_file_list(files: List[Dict[str, Any]], 
                    show_actions: bool = True,
                    key_prefix: str = "files") -> Optional[str]:
    """渲染文件列表 - 便捷函数"""
    return unified_display_renderer.render_file_list(files, show_actions, key_prefix)

def render_progress_panel(tasks: List[Dict[str, Any]], 
                         title: str = "📊 处理进度") -> None:
    """渲染进度面板 - 便捷函数"""
    return unified_display_renderer.render_progress_panel(tasks, title)
