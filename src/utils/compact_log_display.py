#!/usr/bin/env python3
"""
紧凑日志显示组件
使用折叠式布局减少空间占用
"""

import streamlit as st
from pathlib import Path
from datetime import datetime
import re
from typing import List, Dict, Optional

class CompactLogDisplay:
    """紧凑日志显示器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.max_lines_preview = 3  # 预览显示的最大行数
        self.max_char_per_line = 80  # 每行最大字符数
    
    def render_compact_logs(self):
        """渲染紧凑的日志显示"""
        
        # 获取日志文件
        log_files = self._get_log_files()
        
        if not log_files:
            st.info("📝 暂无日志文件")
            return
        
        # 日志概览 - 紧凑显示
        st.markdown("### 📋 日志概览")
        
        # 使用列布局显示统计信息
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📄 日志文件", len(log_files))
        
        with col2:
            total_size = sum(f.stat().st_size for f in log_files if f.exists())
            st.metric("💾 总大小", f"{total_size/1024:.1f}KB")
        
        with col3:
            latest_file = max(log_files, key=lambda f: f.stat().st_mtime if f.exists() else 0)
            latest_time = datetime.fromtimestamp(latest_file.stat().st_mtime).strftime("%H:%M")
            st.metric("🕐 最新", latest_time)
        
        # 日志文件列表 - 折叠显示
        for log_file in sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True):
            self._render_log_file_compact(log_file)
    
    def _render_log_file_compact(self, log_file: Path):
        """渲染单个日志文件的紧凑显示"""
        
        # 获取文件基本信息
        file_size = log_file.stat().st_size if log_file.exists() else 0
        file_time = datetime.fromtimestamp(log_file.stat().st_mtime).strftime("%m-%d %H:%M")
        
        # 读取日志内容预览
        preview_lines = self._get_log_preview(log_file)
        error_count = self._count_log_levels(log_file)
        
        # 状态指示器
        status_icon = "🔴" if error_count.get('ERROR', 0) > 0 else "🟡" if error_count.get('WARNING', 0) > 0 else "🟢"
        
        # 紧凑的标题行
        title = f"{status_icon} {log_file.name} ({file_size//1024}KB, {file_time})"
        
        with st.expander(title, expanded=False):
            # 错误统计
            if any(error_count.values()):
                col1, col2, col3 = st.columns(3)
                with col1:
                    if error_count.get('ERROR', 0) > 0:
                        st.error(f"❌ 错误: {error_count['ERROR']}")
                with col2:
                    if error_count.get('WARNING', 0) > 0:
                        st.warning(f"⚠️ 警告: {error_count['WARNING']}")
                with col3:
                    if error_count.get('INFO', 0) > 0:
                        st.info(f"ℹ️ 信息: {error_count['INFO']}")
            
            # 日志预览
            if preview_lines:
                st.markdown("**最新日志:**")
                for line in preview_lines:
                    # 截断过长的行
                    if len(line) > self.max_char_per_line:
                        line = line[:self.max_char_per_line] + "..."
                    st.code(line, language=None)
            
            # 操作按钮
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📖 查看全部", key=f"view_full_{log_file.name}"):
                    self._show_full_log(log_file)
            with col2:
                if st.button("🗑️ 清空", key=f"clear_{log_file.name}"):
                    self._clear_log_file(log_file)
            with col3:
                if st.button("💾 下载", key=f"download_{log_file.name}"):
                    self._download_log_file(log_file)
    
    def _get_log_files(self) -> List[Path]:
        """获取日志文件列表"""
        if not self.log_dir.exists():
            return []
        
        return [f for f in self.log_dir.glob("*.log") if f.is_file()]
    
    def _get_log_preview(self, log_file: Path) -> List[str]:
        """获取日志文件预览"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 返回最后几行
                return [line.strip() for line in lines[-self.max_lines_preview:] if line.strip()]
        except Exception:
            return ["无法读取日志内容"]
    
    def _count_log_levels(self, log_file: Path) -> Dict[str, int]:
        """统计日志级别数量"""
        counts = {'ERROR': 0, 'WARNING': 0, 'INFO': 0, 'DEBUG': 0}
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for level in counts.keys():
                    counts[level] = len(re.findall(rf'\b{level}\b', content, re.IGNORECASE))
        except Exception:
            pass
        
        return counts
    
    def _show_full_log(self, log_file: Path):
        """显示完整日志"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 使用模态框显示完整日志
            with st.container():
                st.markdown(f"### 📖 {log_file.name} - 完整日志")
                
                # 日志级别过滤
                filter_level = st.selectbox(
                    "过滤级别",
                    ["全部", "ERROR", "WARNING", "INFO", "DEBUG"],
                    key=f"filter_{log_file.name}"
                )
                
                # 过滤日志内容
                if filter_level != "全部":
                    lines = content.split('\n')
                    filtered_lines = [line for line in lines if filter_level.upper() in line.upper()]
                    content = '\n'.join(filtered_lines)
                
                # 显示日志内容
                st.text_area(
                    "日志内容",
                    content,
                    height=400,
                    key=f"log_content_{log_file.name}"
                )
        except Exception as e:
            st.error(f"读取日志失败: {e}")
    
    def _clear_log_file(self, log_file: Path):
        """清空日志文件"""
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("")
            st.success(f"✅ 已清空 {log_file.name}")
            st.rerun()
        except Exception as e:
            st.error(f"清空失败: {e}")
    
    def _download_log_file(self, log_file: Path):
        """下载日志文件"""
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            st.download_button(
                label=f"💾 下载 {log_file.name}",
                data=content,
                file_name=log_file.name,
                mime="text/plain",
                key=f"download_btn_{log_file.name}"
            )
        except Exception as e:
            st.error(f"下载失败: {e}")

def render_compact_log_management():
    """渲染紧凑的日志管理界面"""
    
    # 创建紧凑日志显示器
    log_display = CompactLogDisplay()
    
    # 渲染紧凑日志
    log_display.render_compact_logs()
    
    # 全局操作
    st.markdown("---")
    st.markdown("### 🔧 日志管理")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🗑️ 清空所有日志", type="secondary"):
            if st.confirm("确定要清空所有日志吗？"):
                _clear_all_logs()
    
    with col2:
        if st.button("📦 打包下载", type="secondary"):
            _package_all_logs()
    
    with col3:
        if st.button("🔄 刷新", type="primary"):
            st.rerun()

def _clear_all_logs():
    """清空所有日志"""
    try:
        log_dir = Path("logs")
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write("")
        st.success("✅ 已清空所有日志")
    except Exception as e:
        st.error(f"清空失败: {e}")

def _package_all_logs():
    """打包所有日志"""
    try:
        import zipfile
        import io
        
        log_dir = Path("logs")
        if not log_dir.exists():
            st.warning("没有找到日志目录")
            return
        
        # 创建ZIP文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for log_file in log_dir.glob("*.log"):
                zip_file.write(log_file, log_file.name)
        
        zip_buffer.seek(0)
        
        # 提供下载
        st.download_button(
            label="📦 下载日志包",
            data=zip_buffer.getvalue(),
            file_name=f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip"
        )
    except Exception as e:
        st.error(f"打包失败: {e}")

# 全局紧凑日志显示器
compact_log_display = CompactLogDisplay()
