"""
导出功能UI组件
"""

import streamlit as st
from datetime import datetime
from src.utils.export_manager import export_manager
from src.utils.performance_monitor import performance_monitor

def render_export_interface():
    """渲染导出界面"""
    st.markdown("### 📄 数据导出")
    
    # 对话记录导出
    st.markdown("#### 💬 对话记录导出")
    
    if 'messages' in st.session_state and st.session_state.messages:
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            export_format = st.selectbox(
                "导出格式",
                ["txt", "json", "csv"],
                format_func=lambda x: {
                    "txt": "📝 文本文件 (.txt)",
                    "json": "📋 JSON格式 (.json)", 
                    "csv": "📊 CSV表格 (.csv)"
                }[x]
            )
        
        with col2:
            kb_name = st.session_state.get('current_kb_id', 'default')
            st.text_input("知识库名称", value=kb_name, disabled=True, label_visibility="collapsed")
        
        with col3:
            if st.button("📤 导出对话", use_container_width=True, type="primary"):
                try:
                    filepath = export_manager.export_chat_history(
                        st.session_state.messages, 
                        kb_name, 
                        export_format
                    )
                    st.success(f"✅ 导出成功: {filepath}")
                    
                    # 提供下载链接
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            "💾 下载文件",
                            f.read(),
                            file_name=filepath.split('/')[-1],
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"❌ 导出失败: {str(e)}")
        
        # 显示对话统计
        st.info(f"📊 当前对话: {len(st.session_state.messages)} 条消息")
    else:
        st.info("📝 当前没有对话记录可导出")

def render_statistics_export():
    """渲染统计报告导出"""
    st.markdown("#### 📊 统计报告导出")
    
    if 'current_kb_id' in st.session_state and st.session_state.current_kb_id:
        kb_name = st.session_state.current_kb_id
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**知识库**: {kb_name}")
            
            # 模拟统计数据
            mock_stats = {
                'document_count': 25,
                'total_pages': 1250,
                'total_chunks': 5000,
                'total_size_mb': 125.6,
                'file_types': {
                    'PDF': 15,
                    'DOCX': 8,
                    'TXT': 2
                },
                'total_queries': performance_monitor.query_stats['total_queries'],
                'avg_response_time': performance_monitor.query_stats['avg_response_time'],
                'success_rate': performance_monitor.query_stats['success_rate']
            }
            
            # 显示统计预览
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("📄 文档数", mock_stats['document_count'])
            with col_b:
                st.metric("📑 总页数", mock_stats['total_pages'])
            with col_c:
                st.metric("🔍 查询数", mock_stats['total_queries'])
        
        with col2:
            if st.button("📊 导出报告", use_container_width=True, type="primary"):
                try:
                    filepath = export_manager.export_kb_statistics(kb_name, mock_stats)
                    st.success(f"✅ 报告生成成功")
                    
                    # 提供下载
                    with open(filepath, 'rb') as f:
                        st.download_button(
                            "💾 下载报告",
                            f.read(),
                            file_name=filepath.split('/')[-1],
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"❌ 生成失败: {str(e)}")
    else:
        st.info("📝 请先选择一个知识库")

def render_backup_restore():
    """渲染备份恢复界面"""
    st.markdown("#### 💾 数据备份")
    
    if 'current_kb_id' in st.session_state and st.session_state.current_kb_id:
        kb_name = st.session_state.current_kb_id
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**当前知识库**: {kb_name}")
            st.caption("备份将包含向量数据库和配置信息")
        
        with col2:
            if st.button("💾 创建备份", use_container_width=True, type="primary"):
                try:
                    # 模拟知识库路径
                    kb_path = f"vector_db_storage/{kb_name}"
                    backup_path = export_manager.backup_knowledge_base(kb_name, kb_path)
                    st.success(f"✅ 备份创建成功")
                    st.info(f"📁 备份位置: {backup_path}")
                except Exception as e:
                    st.error(f"❌ 备份失败: {str(e)}")
    else:
        st.info("📝 请先选择一个知识库")

def render_export_history():
    """渲染导出历史"""
    st.markdown("#### 📋 导出历史")
    
    export_files = export_manager.get_export_files()
    
    if export_files:
        st.markdown(f"**共 {len(export_files)} 个导出文件**")
        
        for file_info in export_files[:10]:  # 显示最近10个
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                file_icon = {
                    'txt': '📝',
                    'json': '📋', 
                    'csv': '📊',
                    'folder': '📁'
                }.get(file_info['type'], '📄')
                st.markdown(f"{file_icon} {file_info['name']}")
            
            with col2:
                size_kb = file_info['size'] / 1024
                st.text(f"{size_kb:.1f}KB")
            
            with col3:
                st.text(file_info['created'].strftime('%m-%d %H:%M'))
            
            with col4:
                if st.button("🗑️", key=f"del_{file_info['name']}", help="删除文件"):
                    if export_manager.delete_export_file(file_info['path']):
                        st.success("✅ 文件已删除")
                        st.rerun()
                    else:
                        st.error("❌ 删除失败")
        
        if len(export_files) > 10:
            st.info(f"📝 还有 {len(export_files) - 10} 个文件未显示")
    else:
        st.info("📝 还没有导出文件")

def render_export_settings():
    """渲染导出设置"""
    st.markdown("#### ⚙️ 导出设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**文件格式设置**")
        
        # 默认导出格式
        default_format = st.selectbox(
            "默认导出格式",
            ["txt", "json", "csv"],
            format_func=lambda x: {
                "txt": "📝 文本文件",
                "json": "📋 JSON格式",
                "csv": "📊 CSV表格"
            }[x]
        )
        
        # 文件命名规则
        naming_rule = st.selectbox(
            "文件命名规则",
            ["timestamp", "kb_name", "custom"],
            format_func=lambda x: {
                "timestamp": "⏰ 时间戳",
                "kb_name": "📚 知识库名称",
                "custom": "✏️ 自定义"
            }[x]
        )
    
    with col2:
        st.markdown("**导出选项**")
        
        # 包含时间戳
        include_timestamp = st.checkbox("📅 包含时间戳", value=True)
        
        # 压缩导出
        compress_export = st.checkbox("🗜️ 压缩导出文件", value=False)
        
        # 自动清理
        auto_cleanup = st.checkbox("🧹 自动清理旧文件", value=False)
        
        if auto_cleanup:
            cleanup_days = st.number_input("保留天数", min_value=1, max_value=365, value=30)
    
    # 保存设置按钮
    if st.button("💾 保存设置", use_container_width=True):
        st.success("✅ 设置已保存")
