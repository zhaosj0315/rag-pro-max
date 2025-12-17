"""
文档管理界面 - 负责文档相关的UI逻辑
"""

import streamlit as st
import os
import time


class DocumentManagerUI:
    """文档管理界面"""
    
    def __init__(self):
        """初始化文档管理界面"""
        pass
    
    @staticmethod
    @st.dialog("📄 文档详情")
    def show_document_detail_dialog(kb_name: str, file_info: dict):
        """显示文档详情对话框"""
        st.subheader(f"📄 {file_info['name']}")
        
        # 基本信息 - 两列布局
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📊 基本信息")
            st.markdown(f"**📂 路径**: `{file_info.get('file_path', 'N/A')}`")
            st.markdown(f"**📏 大小**: {file_info.get('size', '未知')} ({file_info.get('size_bytes', 0):,} 字节)")
            st.markdown(f"**📄 类型**: {file_info.get('type', '未知')}")
            st.markdown(f"**🌐 语言**: {file_info.get('language', '未知')}")
            
        with col2:
            st.markdown("### 🕒 时间信息")
            st.markdown(f"**📅 添加时间**: {file_info.get('added_at', '未知')}")
            st.markdown(f"**🕒 最后访问**: {file_info.get('last_accessed', '从未访问') or '从未访问'}")
            st.markdown(f"**📁 目录**: {file_info.get('parent_folder', '未知')}")
            st.markdown(f"**🔐 哈希**: `{file_info.get('file_hash', 'N/A')}`")
        
        # 统计信息
        st.markdown("### 📈 统计信息")
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("🧩 向量片段", len(file_info.get('doc_ids', [])))
        stat_col2.metric("🔥 查询命中", file_info.get('hit_count', 0))
        stat_col3.metric("⭐ 平均评分", f"{file_info.get('avg_score', 0.0):.2f}" if file_info.get('avg_score') else 'N/A')
        
        # 分类和关键词
        if file_info.get('category') or file_info.get('keywords'):
            st.markdown("### 🏷️ 分类标签")
            tag_col1, tag_col2 = st.columns(2)
            tag_col1.markdown(f"**📚 分类**: {file_info.get('category', '未分类')}")
            if file_info.get('keywords'):
                tag_col2.markdown(f"**🏷️ 关键词**: {', '.join(file_info.get('keywords', [])[:8])}")
        
        # 向量片段ID
        if file_info.get('doc_ids'):
            st.markdown("### 🧬 向量片段ID")
            with st.expander(f"查看 {len(file_info['doc_ids'])} 个片段ID", expanded=False):
                st.text_area(
                    "片段ID列表", 
                    value='\n'.join(file_info['doc_ids']), 
                    height=200,
                    label_visibility="collapsed"
                )
        
        # 关闭按钮
        if st.button("✅ 关闭", use_container_width=True):
            st.session_state.show_doc_detail = None
            st.session_state.show_doc_detail_kb = None
            st.rerun()
    
    def render_document_list(self, kb_name: str):
        """渲染文档列表"""
        try:
            from src.documents.document_manager import DocumentManager
            
            output_base = os.path.join(os.getcwd(), "vector_db_storage")
            db_path = os.path.join(output_base, kb_name)
            
            if not os.path.exists(db_path):
                st.info("知识库不存在或为空")
                return
            
            doc_manager = DocumentManager(db_path)
            
            if not doc_manager.manifest['files']:
                st.info("暂无文件")
                return
            
            # 文档统计
            total_files = len(doc_manager.manifest['files'])
            ocr_files = sum(1 for f in doc_manager.manifest['files'] if f.get('used_ocr', False))
            metadata_files = sum(1 for f in doc_manager.manifest['files'] if f.get('keywords') or f.get('category'))
            summary_files = sum(1 for f in doc_manager.manifest['files'] if f.get('summary'))
            
            st.markdown("#### 🔧 高级选项处理统计")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("📄 总文档", total_files)
            with col2:
                ocr_percentage = (ocr_files / total_files * 100) if total_files > 0 else 0
                st.metric("🔍 OCR处理", f"{ocr_files}", delta=f"{ocr_percentage:.1f}%")
            with col3:
                metadata_percentage = (metadata_files / total_files * 100) if total_files > 0 else 0
                st.metric("📊 元数据提取", f"{metadata_files}", delta=f"{metadata_percentage:.1f}%")
            with col4:
                summary_percentage = (summary_files / total_files * 100) if total_files > 0 else 0
                st.metric("📝 生成摘要", f"{summary_files}", delta=f"{summary_percentage:.1f}%")
            
            # 处理建议
            if ocr_files == 0 and metadata_files == 0 and summary_files == 0:
                st.info("💡 **提示**: 在上传文档时启用高级选项，可以获得更丰富的文档信息和更好的检索效果")
            elif ocr_files < total_files // 2:
                st.info("💡 **建议**: 对于包含图片或扫描内容的PDF文档，建议启用OCR识别功能")
            
            # 文档列表
            self.render_file_list(doc_manager, kb_name)
            
        except Exception as e:
            st.error(f"加载文档列表失败: {str(e)}")
    
    def render_file_list(self, doc_manager, kb_name: str):
        """渲染文件列表"""
        files = doc_manager.manifest['files']
        
        # 搜索和筛选
        col1, col2, col3 = st.columns([3, 2, 2])
        
        with col1:
            search_term = st.text_input("🔍 搜索文件", placeholder="输入文件名...")
        
        with col2:
            file_types = sorted(set(f.get('type', 'Unknown') for f in files))
            filter_type = st.selectbox("📂 文件类型", ["全部"] + file_types)
        
        with col3:
            sort_options = ["时间↓", "时间↑", "大小↓", "大小↑", "名称", "热度↓"]
            sort_by = st.selectbox("排序", sort_options)
        
        # 筛选文件
        filtered_files = files
        
        if search_term:
            filtered_files = [f for f in filtered_files if search_term.lower() in f['name'].lower()]
        
        if filter_type != "全部":
            filtered_files = [f for f in filtered_files if f.get('type') == filter_type]
        
        # 排序
        if sort_by == "时间↓":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('added_at', ''), reverse=True)
        elif sort_by == "时间↑":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('added_at', ''))
        elif sort_by == "大小↓":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('size_bytes', 0), reverse=True)
        elif sort_by == "大小↑":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('size_bytes', 0))
        elif sort_by == "名称":
            filtered_files = sorted(filtered_files, key=lambda x: x['name'].lower())
        elif sort_by == "热度↓":
            filtered_files = sorted(filtered_files, key=lambda x: x.get('hit_count', 0), reverse=True)
        
        # 分页
        page_size = 10
        total_files = len(filtered_files)
        total_pages = (total_files + page_size - 1) // page_size if total_files > 0 else 1
        
        if 'file_page' not in st.session_state:
            st.session_state.file_page = 1
        
        if st.session_state.file_page > total_pages:
            st.session_state.file_page = 1
        
        # 分页控制
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page_cols = st.columns([1, 3, 1])
                if page_cols[0].button("⬅️ 上一页", disabled=st.session_state.file_page <= 1):
                    st.session_state.file_page -= 1
                page_cols[1].markdown(f"<div style='text-align:center'>第 {st.session_state.file_page}/{total_pages} 页</div>", unsafe_allow_html=True)
                if page_cols[2].button("下一页 ➡️", disabled=st.session_state.file_page >= total_pages):
                    st.session_state.file_page += 1
        
        # 显示文件
        if total_files == 0:
            st.info("❌ 无匹配文件")
            return
        
        start_idx = (st.session_state.file_page - 1) * page_size
        end_idx = min(start_idx + page_size, total_files)
        
        for i in range(start_idx, end_idx):
            f = filtered_files[i]
            self.render_file_item(f, i, kb_name, doc_manager)
    
    def render_file_item(self, file_info: dict, index: int, kb_name: str, doc_manager):
        """渲染单个文件项"""
        chunk_count = len(file_info.get('doc_ids', []))
        
        # 质量评估
        if chunk_count == 0:
            q_icon = "❌"
        elif chunk_count < 2:
            q_icon = "⚠️"
        elif chunk_count < 10:
            q_icon = "✅"
        else:
            q_icon = "🎉"
        
        with st.container(border=True):
            col_info, col_ops = st.columns([4, 1])
            
            with col_info:
                # 文件信息
                file_icon = file_info.get('icon', '📄')
                fname = file_info['name']
                if len(fname) > 40:
                    fname = fname[:37] + "..."
                
                st.markdown(f"**{file_icon} {fname}**")
                
                # 文件详情
                size = file_info.get('size', '未知')
                date = file_info.get('added_at', '未知')[:10] if file_info.get('added_at') else '未知'
                hit_count = file_info.get('hit_count', 0)
                
                st.caption(f"{size} • {chunk_count}片段 • {date} • {q_icon} • 命中{hit_count}次")
                
                # 显示摘要
                if file_info.get('summary'):
                    summary = file_info['summary']
                    if len(summary) > 100:
                        summary = summary[:97] + "..."
                    st.caption(f"📝 {summary}")
            
            with col_ops:
                # 详情按钮
                if st.button("🔍", key=f"detail_{index}", help="查看详情"):
                    st.session_state.show_doc_detail = file_info
                    st.session_state.show_doc_detail_kb = kb_name
                    st.rerun()
                
                # 删除按钮
                if st.button("🗑️", key=f"del_{index}", help="删除文件"):
                    self.delete_file(file_info, kb_name, doc_manager)
    
    def delete_file(self, file_info: dict, kb_name: str, doc_manager):
        """删除文件"""
        try:
            from llama_index.core import StorageContext, load_index_from_storage
            from src.utils.app_utils import remove_file_from_manifest
            
            output_base = os.path.join(os.getcwd(), "vector_db_storage")
            db_path = os.path.join(output_base, kb_name)
            
            with st.status("删除中...", expanded=True) as status:
                # 从索引中删除
                ctx = StorageContext.from_defaults(persist_dir=db_path)
                idx = load_index_from_storage(ctx)
                
                for doc_id in file_info.get('doc_ids', []):
                    idx.delete_ref_doc(doc_id, delete_from_docstore=True)
                
                idx.storage_context.persist(persist_dir=db_path)
                
                # 从清单中删除
                remove_file_from_manifest(db_path, file_info['name'])
                
                status.update(label="已删除", state="complete")
                
                # 清除聊天引擎缓存
                st.session_state.chat_engine = None
                
                st.success(f"✅ 已删除文件: {file_info['name']}")
                time.sleep(0.5)
                st.rerun()
                
        except Exception as e:
            st.error(f"删除失败: {str(e)}")
    
    def render_document_operations(self, kb_name: str):
        """渲染文档操作"""
        st.markdown("#### ⚡ 快速操作")
        
        col1, col2, col3, col4 = st.columns(4)
        
        # 打开目录
        with col1:
            if st.button("📂 打开目录", use_container_width=True):
                output_base = os.path.join(os.getcwd(), "vector_db_storage")
                db_path = os.path.join(output_base, kb_name)
                
                import webbrowser
                import urllib.parse
                try:
                    file_url = 'file://' + urllib.parse.quote(os.path.abspath(db_path))
                    webbrowser.open(file_url)
                    st.toast("✅ 已在Finder中打开")
                except Exception as e:
                    st.error(f"打开失败: {e}")
        
        # 复制路径
        with col2:
            if st.button("📋 复制路径", use_container_width=True):
                output_base = os.path.join(os.getcwd(), "vector_db_storage")
                db_path = os.path.join(output_base, kb_name)
                try:
                    import subprocess
                    subprocess.run(["pbcopy"], input=db_path.encode(), check=True)
                    st.toast("✅ 已复制路径")
                except Exception:
                    st.info(f"📁 路径: {db_path}")
        
        # 生成摘要
        with col3:
            if st.button("✨ 批量摘要", use_container_width=True):
                st.info("请在文档列表中选择文件后使用摘要功能")
        
        # 导出清单
        with col4:
            if st.button("📥 导出清单", use_container_width=True):
                self.export_manifest(kb_name)
