"""
批量上传UI组件
"""

import streamlit as st
import os
from pathlib import Path
from src.utils.batch_operations import batch_ops
from src.utils.memory_guard import memory_guard

def render_batch_upload_ui():
    """渲染批量上传界面"""
    st.markdown("### 📁 批量文件夹上传")
    
    # 文件夹路径输入
    folder_path = st.text_input(
        "📂 文件夹路径", 
        placeholder="/path/to/your/documents",
        help="输入包含文档的文件夹路径，支持拖拽文件夹到此处"
    )
    
    # 扫描按钮
    col1, col2 = st.columns([1, 1])
    
    with col1:
        scan_clicked = st.button("🔍 扫描文件夹", use_container_width=True)
    
    with col2:
        if 'batch_scan_result' in st.session_state:
            upload_clicked = st.button("📤 批量上传", use_container_width=True, type="primary")
        else:
            st.button("📤 批量上传", use_container_width=True, disabled=True)
    
    # 扫描结果
    if scan_clicked and folder_path:
        if os.path.exists(folder_path):
            with st.spinner("🔍 正在扫描文件夹..."):
                scan_result = batch_ops.scan_folder(folder_path)
                st.session_state.batch_scan_result = scan_result
                st.session_state.batch_folder_path = folder_path
        else:
            st.error("❌ 文件夹路径不存在")
    
    # 显示扫描结果
    if 'batch_scan_result' in st.session_state:
        result = st.session_state.batch_scan_result
        
        # 统计信息
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📁 总文件", result['total'])
        with col2:
            st.metric("✅ 支持格式", result['supported'])
        with col3:
            st.metric("❌ 不支持", result['unsupported'])
        with col4:
            if result['supported'] > 0:
                stats = batch_ops.get_file_stats(result['files'])
                st.metric("📊 总大小", f"{stats['total_size']/1024/1024:.1f}MB")
        
        # 文件类型分布
        if result['files']:
            stats = batch_ops.get_file_stats(result['files'])
            st.markdown("#### 📊 文件类型分布")
            
            type_data = []
            for file_type, info in stats['types'].items():
                type_data.append({
                    'type': file_type,
                    'count': info['count'],
                    'size_mb': info['size'] / 1024 / 1024
                })
            
            st.dataframe(type_data, use_container_width=True)
        
        # 文件预览
        if result['files']:
            st.markdown("#### 📄 文件预览 (前10个)")
            preview_files = result['files'][:10]
            
            preview_data = []
            for file_info in preview_files:
                preview_data.append({
                    'name': file_info['name'],
                    'path': file_info['relative_path'],
                    'type': file_info['type'],
                    'size_kb': file_info['size'] / 1024
                })
            
            st.dataframe(preview_data, use_container_width=True)
            
            if len(result['files']) > 10:
                st.info(f"📝 还有 {len(result['files']) - 10} 个文件未显示")
    
    # 批量上传处理
    if 'batch_scan_result' in st.session_state and st.button("📤 批量上传", key="batch_upload_btn"):
        result = st.session_state.batch_scan_result
        folder_path = st.session_state.batch_folder_path
        
        if result['files']:
            @memory_guard.monitor_process("批量上传")
            def process_batch_upload():
                # 创建临时目录
                temp_dir = "temp_uploads/batch_upload"
                
                # 复制文件
                copy_result = batch_ops.batch_copy_files(result['files'], temp_dir)
                
                return copy_result
            
            with st.spinner(f"📤 正在上传 {result['supported']} 个文件..."):
                copy_result = process_batch_upload()
                
                if copy_result:
                    if copy_result['success_count'] > 0:
                        st.success(f"✅ 成功上传 {copy_result['success_count']} 个文件")
                        
                        # 设置上传路径供后续处理
                        st.session_state.uploaded_path = os.path.abspath("temp_uploads/batch_upload")
                    
                    if copy_result['failed_count'] > 0:
                        st.warning(f"⚠️ {copy_result['failed_count']} 个文件上传失败")
                        with st.expander("查看失败详情"):
                            for failed in copy_result['failed_files']:
                                st.text(f"❌ {failed['file']}: {failed['error']}")
                    
                    # 清理扫描结果
                    del st.session_state.batch_scan_result
                    del st.session_state.batch_folder_path

def render_batch_management_ui():
    """渲染批量管理界面"""
    st.markdown("### 🗂️ 批量文档管理")
    
    # 获取当前知识库的文档列表
    if 'current_kb_id' in st.session_state and st.session_state.current_kb_id:
        kb_name = st.session_state.current_kb_id
        
        # 模拟文档列表（实际应该从知识库获取）
        documents = [
            {'name': 'document1.pdf', 'size': 1024000, 'date': '2024-12-14'},
            {'name': 'document2.docx', 'size': 512000, 'date': '2024-12-13'},
            {'name': 'document3.txt', 'size': 256000, 'date': '2024-12-12'},
        ]
        
        if documents:
            st.markdown(f"#### 📚 知识库: {kb_name}")
            
            # 全选/取消全选
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                select_all = st.checkbox("🔲 全选")
            with col2:
                if st.button("🗑️ 批量删除", type="secondary"):
                    st.session_state.show_delete_confirm = True
            
            # 文档列表
            selected_docs = []
            for i, doc in enumerate(documents):
                col1, col2, col3, col4 = st.columns([0.5, 3, 1, 1])
                
                with col1:
                    selected = st.checkbox("", key=f"doc_{i}", value=select_all)
                    if selected:
                        selected_docs.append(doc)
                
                with col2:
                    st.text(doc['name'])
                
                with col3:
                    st.text(f"{doc['size']/1024:.0f}KB")
                
                with col4:
                    st.text(doc['date'])
            
            # 删除确认
            if st.session_state.get('show_delete_confirm', False):
                st.warning(f"⚠️ 确定要删除 {len(selected_docs)} 个文档吗？")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ 确认删除", type="primary"):
                        st.success(f"🗑️ 已删除 {len(selected_docs)} 个文档")
                        st.session_state.show_delete_confirm = False
                        st.rerun()
                
                with col2:
                    if st.button("❌ 取消"):
                        st.session_state.show_delete_confirm = False
                        st.rerun()
        else:
            st.info("📝 当前知识库没有文档")
    else:
        st.info("📝 请先选择一个知识库")
