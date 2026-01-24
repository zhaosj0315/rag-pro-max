"""
增强的用户体验组件
"""

import streamlit as st
import time
from typing import List, Dict, Any, Optional

class UserExperienceEnhancer:
    """用户体验增强器"""
    
    @staticmethod
    def enhanced_file_uploader(
        label: str,
        accepted_types: List[str],
        max_size_mb: int = 100,
        multiple: bool = True
    ) -> Optional[List]:
        """增强的文件上传器"""
        
        st.markdown(f"### 📁 {label}")
        
        # 显示支持的文件类型
        with st.expander("📋 支持的文件类型"):
            cols = st.columns(3)
            for i, file_type in enumerate(accepted_types):
                cols[i % 3].write(f"• {file_type.upper()}")
        
        # 文件大小提示
        st.info(f"💡 单个文件最大 {max_size_mb}MB")
        
        # 文件上传器
        uploaded_files = st.file_uploader(
            "选择文件",
            type=accepted_types,
            accept_multiple_files=multiple,
            help=f"支持 {', '.join(accepted_types)} 格式"
        )
        
        if uploaded_files:
            files = uploaded_files if multiple else [uploaded_files]
            
            # 验证文件
            valid_files = []
            for file in files:
                size_mb = file.size / (1024 * 1024)
                
                if size_mb > max_size_mb:
                    st.error(f"❌ {file.name} 文件过大 ({size_mb:.1f}MB > {max_size_mb}MB)")
                else:
                    valid_files.append(file)
                    st.success(f"✅ {file.name} ({size_mb:.1f}MB)")
            
            return valid_files if valid_files else None
        
        return None
    
    @staticmethod
    def enhanced_progress_bar(
        current: int,
        total: int,
        label: str = "处理进度",
        show_eta: bool = True,
        start_time: Optional[float] = None
    ):
        """增强的进度条"""
        
        progress = current / total if total > 0 else 0
        
        # 进度条
        progress_bar = st.progress(progress)
        
        # 详细信息
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**{label}**: {current}/{total} ({progress*100:.1f}%)")
        
        with col2:
            if current > 0:
                st.write(f"✅ 已完成: {current}")
            else:
                st.write("⏳ 准备中...")
        
        with col3:
            if show_eta and start_time and current > 0:
                elapsed = time.time() - start_time
                speed = current / elapsed
                eta = (total - current) / speed if speed > 0 else 0
                st.write(f"⏱️ ETA: {eta:.0f}秒")
        
        return progress_bar
    
    @staticmethod
    def enhanced_error_display(
        error: Exception,
        context: str = "",
        show_details: bool = True,
        suggestions: List[str] = None
    ):
        """增强的错误显示"""
        
        # 主要错误信息
        error_msg = f"{context}: {str(error)}" if context else str(error)
        st.error(f"❌ {error_msg}")
        
        # 错误详情
        if show_details:
            with st.expander("🔍 错误详情"):
                st.code(str(error))
        
        # 解决建议
        if suggestions:
            st.info("💡 **解决建议:**")
            for i, suggestion in enumerate(suggestions, 1):
                st.write(f"{i}. {suggestion}")
    
    @staticmethod
    def enhanced_success_message(
        message: str,
        details: Dict[str, Any] = None,
        show_stats: bool = True
    ):
        """增强的成功消息"""
        
        st.success(f"✅ {message}")
        
        if details and show_stats:
            with st.expander("📊 详细信息"):
                for key, value in details.items():
                    st.write(f"**{key}**: {value}")
    
    @staticmethod
    def enhanced_sidebar_status():
        """增强的侧边栏状态"""
        
        with st.sidebar:
            st.markdown("---")
            st.markdown("##### 📊 系统状态")
            
            # 快速状态检查
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            # 状态指示器
            cpu_status = "🟢" if cpu_percent < 70 else "🟡" if cpu_percent < 90 else "🔴"
            mem_status = "🟢" if memory.percent < 70 else "🟡" if memory.percent < 85 else "🔴"
            
            st.write(f"{cpu_status} CPU: {cpu_percent:.1f}%")
            st.write(f"{mem_status} 内存: {memory.percent:.1f}%")
            
            # 快速操作
            if st.button("🧹 清理内存"):
                from ..utils.memory_manager_enhanced import memory_manager
                collected = memory_manager.cleanup_memory(force=True)
                st.success(f"已清理 {collected} 个对象")
    
    @staticmethod
    def enhanced_help_section():
        """增强的帮助部分"""
        
        with st.expander("❓ 使用帮助"):
            st.markdown("""
            ### 📖 快速指南
            
            **1. 上传文档**
            - 支持 PDF, DOCX, TXT, MD 等格式
            - 单个文件最大 100MB
            - 可批量上传多个文件
            
            **2. 创建知识库**
            - 输入知识库名称
            - 点击"创建新知识库"
            - 等待处理完成
            
            **3. 开始对话**
            - 选择已创建的知识库
            - 输入问题
            - 查看答案和引用来源
            
            ### 🔧 常见问题
            
            **Q: 上传失败怎么办？**
            A: 检查文件格式和大小，确保网络连接正常
            
            **Q: 处理速度慢？**
            A: 大文件需要更多时间，可以查看系统监控
            
            **Q: 找不到相关答案？**
            A: 尝试换个问法，或检查知识库是否包含相关内容
            """)
    
    @staticmethod
    def enhanced_welcome_message():
        """增强的欢迎消息"""
        
        st.markdown("""
        # 🚀 RAG Pro Max v1.7.3
        
        **智能文档问答系统** - 让您的文档变得更智能
        
        ### ✨ 主要特性
        - 📄 多格式文档支持 (PDF, DOCX, TXT, MD等)
        - 🔍 智能语义检索
        - 💬 多轮对话
        - 🎯 精确引用来源
        - 🚀 GPU加速处理
        
        ### 🎯 开始使用
        1. 在左侧上传您的文档
        2. 创建知识库
        3. 开始智能问答
        """)

# 全局用户体验增强器
ux_enhancer = UserExperienceEnhancer()
