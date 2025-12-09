"""
文档预览 UI 组件
"""

import streamlit as st
from typing import Optional
from src.kb.document_viewer import DocumentViewer, DocumentInfo


def show_upload_preview(uploaded_file) -> None:
    """显示上传文件的预览对话框"""
    if not uploaded_file:
        return
    
    show_file_preview_dialog(uploaded_file)


@st.dialog("📄 文件预览")
def show_file_preview_dialog(uploaded_file):
    """显示文件预览对话框"""
    st.subheader(uploaded_file.name)
    
    try:
        # 保存临时文件
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name
        
        viewer = DocumentViewer()
        preview = viewer.preview_file(tmp_path, max_chars=2000)
        
        # 文件信息
        col1, col2 = st.columns(2)
        col1.metric("📊 文件大小", f"{uploaded_file.size / 1024:.1f} KB")
        col2.metric("📂 文件类型", uploaded_file.type or "未知")
        
        st.divider()
        
        # 内容预览
        st.text_area("内容预览", preview, height=400, disabled=True)
        
        # 清理临时文件
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        
        if st.button("关闭", type="primary"):
            st.rerun()
            
    except Exception as e:
        st.error(f"预览失败: {e}")


def show_kb_documents(kb_name: str) -> None:
    """显示知识库文档列表"""
    if not kb_name:
        return
    
    viewer = DocumentViewer()
    docs = viewer.get_kb_documents(kb_name)
    
    if not docs:
        st.info("📭 知识库中暂无文档")
        return
    
    st.subheader(f"📚 文档列表 ({len(docs)})")
    
    for doc in docs:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            # 文档名称
            col1.write(f"📄 {doc.name}")
            
            # 文件大小
            col2.write(f"{doc.size_mb:.2f} MB")
            
            # 查看按钮
            if col3.button("👁️", key=f"view_{doc.name}", help="查看详情"):
                st.session_state['show_doc_detail'] = doc
                st.session_state['show_doc_kb'] = kb_name
            
            # 删除按钮
            if col4.button("🗑️", key=f"del_{doc.name}", help="删除文档"):
                st.session_state['confirm_delete_doc'] = doc
                st.session_state['confirm_delete_kb'] = kb_name
            
            st.divider()
    
    # 只显示一个对话框
    if 'show_doc_detail' in st.session_state and st.session_state.show_doc_detail:
        show_document_detail(st.session_state.show_doc_kb, st.session_state.show_doc_detail)
        st.session_state.show_doc_detail = None
    
    if 'confirm_delete_doc' in st.session_state and st.session_state.confirm_delete_doc:
        confirm_delete_document(st.session_state.confirm_delete_kb, st.session_state.confirm_delete_doc)
        st.session_state.confirm_delete_doc = None


@st.dialog("📄 文档详情")
def show_document_detail(kb_name: str, doc: DocumentInfo) -> None:
    """显示文档详情对话框"""
    st.subheader(doc.name)
    
    # 元数据
    col1, col2 = st.columns(2)
    col1.metric("📅 上传时间", doc.upload_time)
    col2.metric("📊 文件大小", f"{doc.size_mb:.2f} MB")
    
    # 文档预览
    st.subheader("📖 内容预览")
    viewer = DocumentViewer()
    preview = viewer.preview_file(doc.file_path, max_chars=2000)
    st.text_area("内容", preview, height=300, disabled=True, label_visibility="collapsed")
    
    # 分块信息
    st.subheader("🧩 文档分块")
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
