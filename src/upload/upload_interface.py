"""
文件上传界面管理器 - 负责文件上传相关的UI逻辑
"""

import streamlit as st
import os
import time


class UploadInterface:
    """文件上传界面管理器"""
    
    def __init__(self):
        """初始化上传界面"""
        self.upload_dir = "temp_uploads"
    
    def render_local_upload_tab(self):
        """渲染本地文件上传标签页"""
        local_type = st.radio(
            "方式", 
            ["📄 上传文件", "✍️ 粘贴文本"], 
            horizontal=True, 
            label_visibility="collapsed"
        )
        
        if "上传文件" in local_type:
            return self.render_file_upload()
        else:
            return self.render_text_input()
    
    def render_file_upload(self):
        """渲染文件上传"""
        uploaded_files = st.file_uploader(
            "拖入文件 (PDF, DOCX, TXT, MD)",
            accept_multiple_files=True,
            key="uploader",
            label_visibility="collapsed"
        )
        
        st.caption("支持格式: PDF, DOCX, TXT, MD, Excel | 单个文件最大 100MB")
        
        if uploaded_files:
            return self.process_uploaded_files(uploaded_files)
        
        return None
    
    def render_text_input(self):
        """渲染文本输入"""
        text_input_content = st.text_area(
            "直接输入文本内容", 
            height=200, 
            placeholder="在此粘贴或输入需要分析的文本内容..."
        )
        
        col_txt1, col_txt2 = st.columns([1, 4])
        txt_filename = col_txt1.text_input(
            "文件名", 
            value="manual_input.txt", 
            label_visibility="collapsed"
        )
        
        if col_txt2.button("💾 保存文本", use_container_width=True):
            if text_input_content.strip():
                return self.save_text_content(text_input_content, txt_filename)
            else:
                st.warning("内容不能为空")
        
        return None
    
    def process_uploaded_files(self, uploaded_files):
        """处理上传的文件"""
        if 'last_uploaded_names' not in st.session_state:
            st.session_state.last_uploaded_names = []
        
        current_names = [f.name for f in uploaded_files]
        
        # 只在文件列表变化时处理
        if set(current_names) != set(st.session_state.last_uploaded_names):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 使用 UploadHandler 处理上传
            from src.processors import UploadHandler
            from src.app_logging import LogManager
            
            logger = LogManager()
            handler = UploadHandler(self.upload_dir, logger)
            
            for idx, f in enumerate(uploaded_files):
                status_text.text(f"验证中: {f.name} ({idx+1}/{len(uploaded_files)})")
                progress_bar.progress((idx + 1) / len(uploaded_files))
            
            result = handler.process_uploads(uploaded_files)
            
            progress_bar.empty()
            status_text.empty()
            
            st.session_state.last_uploaded_names = current_names
            st.session_state.uploaded_path = os.path.abspath(result.batch_dir)
            
            # 显示上传结果
            if result.success_count > 0:
                st.success(f"✅ 成功上传 {result.success_count} 个文件")
            
            if result.skipped_count > 0:
                st.warning(f"⚠️ 跳过 {result.skipped_count} 个文件")
                with st.expander("查看跳过详情", expanded=True):
                    for reason in result.skip_reasons:
                        st.text(f"• {reason}")
            
            # 为文件上传场景生成智能名称
            if result.success_count > 0:
                try:
                    # 计算文件类型分布
                    file_types = {}
                    for filename in current_names:
                        ext = os.path.splitext(filename)[1].lower()
                        file_types[ext] = file_types.get(ext, 0) + 1
                    
                    # 使用上传的文件名生成智能名称
                    folder_name = os.path.basename(result.batch_dir)
                    auto_name = self.generate_smart_kb_name(
                        result.batch_dir, 
                        result.success_count, 
                        file_types, 
                        folder_name
                    )
                    
                    # 存储智能生成的名称
                    st.session_state.upload_auto_name = auto_name
                except Exception as e:
                    st.session_state.upload_auto_name = None
            
            time.sleep(1)
            if result.success_count > 0:
                st.rerun()
        
        return st.session_state.get('uploaded_path')
    
    def save_text_content(self, content: str, filename: str):
        """保存文本内容"""
        try:
            save_dir = os.path.join(self.upload_dir, f"text_{int(time.time())}")
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            from src.utils.document_processor import sanitize_filename
            safe_name = sanitize_filename(filename) or "manual_input.txt"
            if not safe_name.endswith('.txt'):
                safe_name += ".txt"
            
            file_path = os.path.join(save_dir, safe_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            st.session_state.uploaded_path = os.path.abspath(save_dir)
            st.session_state.upload_auto_name = f"Text_{safe_name.split('.')[0]}"
            
            st.success("✅ 文本已保存")
            time.sleep(0.5)
            st.rerun()
            
            return os.path.abspath(save_dir)
            
        except Exception as e:
            st.error(f"保存失败: {e}")
            return None
    
    def generate_smart_kb_name(self, target_path: str, cnt: int, file_types: dict, folder_name: str):
        """生成智能知识库名称"""
        try:
            from src.utils.kb_name_optimizer import KBNameOptimizer
            
            # 策略1：单文件特例处理
            if cnt == 1 and os.path.exists(target_path):
                try:
                    files = [f for f in os.listdir(target_path) 
                            if not f.startswith('.') and os.path.isfile(os.path.join(target_path, f))]
                    if len(files) >= 1:
                        single_file = files[0]
                        name_without_ext = os.path.splitext(single_file)[0]
                        suggested_name = self.sanitize_filename(name_without_ext)
                        
                        if suggested_name and len(suggested_name) > 1:
                            output_base = os.path.join(os.getcwd(), "vector_db_storage")
                            return KBNameOptimizer.generate_unique_name(suggested_name, output_base)
                except Exception:
                    pass
            
            # 使用优化器的建议名称功能
            suggested_name = KBNameOptimizer.suggest_name_from_content(
                target_path, cnt, list(file_types.keys())
            )
            
            # 如果没有建议名称，使用备用逻辑
            if not suggested_name:
                main_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
                if not main_types:
                    suggested_name = "文档知识库"
                else:
                    main_ext = main_types[0][0].replace('.', '').upper()
                    
                    type_names = {
                        'PDF': 'PDF文档库', 'DOCX': 'Word文档库', 'DOC': 'Word文档库',
                        'MD': 'Markdown笔记', 'TXT': '文本文档库',
                        'PY': 'Python代码库', 'JS': 'JavaScript代码库', 'JAVA': 'Java代码库',
                        'XLSX': 'Excel数据库', 'CSV': 'CSV数据集',
                        'PPT': 'PPT演示库', 'PPTX': 'PPT演示库',
                        'HTML': '网页文档库', 'JSON': 'JSON配置库'
                    }
                    
                    if len(main_types) == 1:
                        suggested_name = type_names.get(main_ext, f"{main_ext}文档库")
                    else:
                        suggested_name = f"混合文档库_{cnt}个文件"
            
            # 使用优化器确保名称唯一性
            output_base = os.path.join(os.getcwd(), "vector_db_storage")
            return KBNameOptimizer.generate_unique_name(suggested_name, output_base)
            
        except Exception as e:
            return f"知识库_{int(time.time())}"
    
    def sanitize_filename(self, filename: str):
        """清理文件名"""
        try:
            from src.utils.document_processor import sanitize_filename
            return sanitize_filename(filename)
        except:
            # 简单的文件名清理
            import re
            return re.sub(r'[^\w\s-]', '', filename).strip()
    
    def get_folder_stats(self, target_path: str):
        """获取文件夹统计信息"""
        try:
            from src.processors import UploadHandler
            return UploadHandler.get_folder_stats(target_path)
        except Exception:
            # 降级实现
            if not os.path.exists(target_path):
                return 0, {}, 0
            
            cnt = 0
            file_types = {}
            total_size = 0
            
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    if not file.startswith('.'):
                        cnt += 1
                        ext = os.path.splitext(file)[1].lower()
                        file_types[ext] = file_types.get(ext, 0) + 1
                        
                        try:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                        except:
                            pass
            
            return cnt, file_types, total_size
    
    def render_upload_preview(self, target_path: str):
        """渲染上传预览"""
        if not target_path or not os.path.exists(target_path):
            return
        
        # 获取文件统计
        cnt, file_types, total_size = self.get_folder_stats(target_path)
        
        if cnt == 0:
            st.warning("❌ 路径不存在或无有效文件")
            return
        
        # 美化显示
        size_mb = total_size / (1024 * 1024)
        folder_name = os.path.basename(target_path.rstrip('/'))
        
        # 智能计算名称
        auto_name = ""
        if hasattr(st.session_state, 'upload_auto_name') and st.session_state.upload_auto_name:
            auto_name = st.session_state.upload_auto_name
        elif cnt > 0:
            auto_name = self.generate_smart_kb_name(target_path, cnt, file_types, folder_name)
        else:
            auto_name = folder_name
        
        # 决定显示名称
        display_name = folder_name
        if folder_name.startswith(('batch_', 'Web_', 'Search_')) and auto_name:
            display_name = auto_name
        
        st.success(f"✅ **数据源已就绪**: `{display_name}`")
        
        # 三列统计卡片
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("📄 文件数", f"{cnt}")
        stat_col2.metric("💾 总大小", f"{size_mb:.1f}MB" if size_mb > 1 else f"{total_size/1024:.0f}KB")
        stat_col3.metric("📂 类型", f"{len(file_types)} 种")
        
        # 类型分布（只显示前5种）
        if file_types:
            st.caption("**文件类型分布**")
            sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:5]
            type_text = " · ".join([f"{ext.replace('.', '')}: {count}" for ext, count in sorted_types])
            if len(file_types) > 5:
                type_text += f" · 其他: {sum(c for _, c in sorted(file_types.items(), key=lambda x: x[1], reverse=True)[5:])}"
            st.caption(type_text)
    
    def render_batch_upload(self):
        """渲染批量上传"""
        st.markdown("##### 📦 批量上传")
        
        if st.button("📁 选择文件夹", use_container_width=True):
            st.info("💡 请使用文件路径输入框指定文件夹路径")
        
        # 拖拽提示
        st.markdown("""
        <div style="border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 10px 0;">
            <p>📁 拖拽文件夹到此处</p>
            <p style="color: #666; font-size: 0.8em;">或使用上方的文件路径输入</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_upload_progress(self, files_processed: int, total_files: int):
        """渲染上传进度"""
        if total_files > 0:
            progress = files_processed / total_files
            st.progress(progress)
            st.caption(f"处理进度: {files_processed}/{total_files} ({progress*100:.1f}%)")
    
    def validate_file(self, file):
        """验证文件"""
        # 文件大小检查 (100MB)
        max_size = 100 * 1024 * 1024
        if hasattr(file, 'size') and file.size > max_size:
            return False, f"文件 {file.name} 超过100MB限制"
        
        # 文件类型检查
        allowed_extensions = {'.pdf', '.txt', '.docx', '.md', '.xlsx', '.pptx', '.csv', '.html', '.json'}
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in allowed_extensions:
            return False, f"不支持的文件类型: {ext}"
        
        return True, ""
