"""
文档预览 UI 组件
"""

import streamlit as st
from src.kb.document_viewer import DocumentViewer, DocumentInfo


def show_upload_preview(uploaded_file) -> None:
    """显示上传预览 - 使用统一组件"""
    from src.processors.unified_document_processor import show_file_preview
    show_file_preview(uploaded_file)

@st.dialog("📄 文件预览")
def show_file_preview_dialog(uploaded_file):
    """显示文件预览对话框 - 使用统一组件"""
    from src.processors.unified_document_processor import show_file_preview
    show_file_preview(uploaded_file)


def show_kb_documents(kb_name: str) -> None:
    """显示知识库文档列表"""
    if not kb_name:
        return
    
    viewer = DocumentViewer()
    docs = viewer.get_kb_documents(kb_name)
    
    if not docs:
        st.info("📭 知识库中暂无文档")
        return
    
    st.markdown(f"##### 📚 文档列表 ({len(docs)})")
    
    for doc in docs:
        with st.container():
            # 使用更紧凑的列布局，增加一个预览按钮列
            col_name, col_view, col_native, col_del = st.columns([5, 0.8, 0.8, 0.8])
            
            # 文档名称和大小
            col_name.write(f"📄 {doc.name} ({doc.size_mb:.2f} MB)")
            
            # 详情按钮 (图标)
            if col_view.button("📝", key=f"view_{doc.name}", help="查看详情", use_container_width=True):
                from src.auth.audit_logger import AuditLogger
                AuditLogger.log(st.session_state.get('user'), "DOC_DETAIL_VIEW", f"查看文档详情: {doc.name} (KB: {kb_name})", action_type="PREVIEW")
                st.session_state['show_doc_detail'] = doc
                st.session_state['show_doc_kb'] = kb_name
            
            # 原生预览按钮 (图标)
            if col_native.button("👁️", key=f"native_{doc.name}", help="macOS 原生预览", use_container_width=True):
                from src.utils.app_utils import open_file_native
                from src.auth.audit_logger import AuditLogger
                # 重新验证路径，防止相对路径失效
                import os
                import glob
                
                # 优先级搜索候选
                file_name = doc.name
                candidates = [
                    doc.file_path,
                    os.path.join("temp_uploads", kb_name, file_name),
                    os.path.join("vector_db_storage", kb_name, file_name)
                ]
                # 增加模糊匹配
                candidates.extend(glob.glob(os.path.join("temp_uploads", "batch_*", file_name)))
                candidates.extend(glob.glob(os.path.join("temp_uploads", "Search_*", file_name)))
                candidates.extend(glob.glob(os.path.join("temp_uploads", "Web_*", file_name)))
                
                final_path = None
                for p in candidates:
                    if p and os.path.exists(os.path.abspath(p)):
                        final_path = os.path.abspath(p)
                        break
                
                if final_path and open_file_native(final_path):
                    AuditLogger.log(st.session_state.get('user'), "DOC_NATIVE_PREVIEW", f"调用macOS原生预览: {doc.name} (KB: {kb_name})", action_type="PREVIEW")
                    st.toast(f"🚀 正在调用系统预览: {doc.name}")
                else:
                    st.error(f"无法定位文件: {doc.name}")
            
            # 删除按钮 (图标)
            if col_del.button("🗑️", key=f"del_{doc.name}", help="删除文档", use_container_width=True):
                st.session_state['confirm_delete_doc'] = doc
                st.session_state['confirm_delete_kb'] = kb_name
            
            # 移除 st.divider() 以进一步压缩空间
    
    # 只显示一个对话框
    if 'show_doc_detail' in st.session_state and st.session_state.show_doc_detail:
        show_document_detail(st.session_state.show_doc_kb, st.session_state.show_doc_detail)
        st.session_state.show_doc_detail = None
    
    if 'confirm_delete_doc' in st.session_state and st.session_state.confirm_delete_doc:
        confirm_delete_document(st.session_state.confirm_delete_kb, st.session_state.confirm_delete_doc)
        st.session_state.confirm_delete_doc = None


@st.dialog("📄 文档详情")
def render_document_details(doc):
    """渲染文档详情"""
    st.markdown(f"##### {doc.name}")
    
    # 元数据
    col1, col2 = st.columns(2)
    col1.metric("📅 上传时间", doc.upload_time)
    col2.metric("📊 文件大小", f"{doc.size_mb:.2f} MB")
    
    # 文档预览
    st.markdown("##### 📖 内容预览")
    viewer = DocumentViewer()
    preview = viewer.preview_file(doc.file_path, max_chars=2000)
    st.text_area("内容", preview, height=300, disabled=True, label_visibility="collapsed")
    
    # 分块信息
    st.markdown("##### 🧩 文档分块")
    chunks = viewer.get_document_chunks(kb_name, doc.file_path, max_chunks=5)
    
    if chunks:
        st.info(f"共 {len(chunks)}+ 个分块（仅显示前 5 个）")
        for chunk in chunks:
            with st.expander(f"片段 {chunk['index']}"):
                st.text(chunk['text'][:500])
                if len(chunk['text']) > 500:
                    st.caption("... (已截断)")
    else:
        st.warning("无法获取分块信息")
    
    # 关闭按钮
    if st.button("关闭", type="primary"):
        st.rerun()


@st.dialog("⚠️ 确认删除")
def confirm_delete_document(kb_name: str, doc: DocumentInfo) -> None:
    """确认删除文档对话框"""
    st.warning(f"确定要删除文档 **{doc.name}** 吗？")
    st.caption("注意：此操作不可恢复，需要重建索引才能完全删除向量数据")
    
    col1, col2 = st.columns(2)
    
    if col1.button("✅ 确认删除", type="primary"):
        viewer = DocumentViewer()
        if viewer.delete_document(kb_name, doc.file_path):
            st.success("✅ 文档已从知识库移除")
            st.info("💡 建议重建索引以完全删除向量数据")
            st.rerun()
        else:
            st.error("❌ 删除失败")
    
    if col2.button("❌ 取消"):
        st.rerun()
