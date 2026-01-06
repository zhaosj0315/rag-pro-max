"""
知识库下载界面组件
"""

import streamlit as st
from src.services.kb_download_service import get_download_service

class KnowledgeBaseDownloadUI:
    def __init__(self):
        self.download_service = get_download_service()
    
    def show_download_dialog(self, kb_name: str):
        """显示单个知识库的下载对话框"""
        if not st.session_state.get(f'show_download_{kb_name}', False):
            return
        
        # 获取可下载项目
        items = self.download_service.get_downloadable_items(kb_name)
        
        st.markdown(f"### 📥 下载知识库: {kb_name}")
        st.caption("选择要下载的内容类型")
        
        if not any(items.values()):
            st.warning("该知识库没有可下载的内容")
            if st.button("关闭", key=f"close_download_{kb_name}"):
                st.session_state[f'show_download_{kb_name}'] = False
                st.rerun()
            return
        
        # 选择下载内容
        st.markdown("**选择要下载的内容:**")
        
        selected_items = []
        
        # 原始文件
        if items['original_files']:
            file_count = len(items['original_files'])
            total_size = sum(f.get('size', 0) for f in items['original_files'])  # 使用 get() 方法避免 KeyError
            size_mb = total_size / (1024 * 1024)
            
            if st.checkbox(f"📄 原始文件 ({file_count}个, {size_mb:.1f}MB)", 
                          value=True, key=f"dl_files_{kb_name}"):
                selected_items.append('original_files')
                
                # 显示文件列表
                with st.expander("查看文件列表"):
                    for file_info in items['original_files'][:10]:  # 最多显示10个
                        file_name = file_info.get('name', '未知文件')
                        st.write(f"• {file_name}")
                    if len(items['original_files']) > 10:
                        st.write(f"... 还有 {len(items['original_files']) - 10} 个文件")
        
        # 元数据
        if items['metadata']:
            if st.checkbox("📋 知识库信息", value=True, key=f"dl_meta_{kb_name}"):
                selected_items.append('metadata')
        
        # 向量数据
        if items['vector_data']:
            if st.checkbox("🔍 向量索引", value=False, key=f"dl_vector_{kb_name}"):
                selected_items.append('vector_data')
                st.caption("⚠️ 向量数据需要相同的嵌入模型才能使用")
        
        # 摘要
        if items['summaries']:
            if st.checkbox("📝 文档摘要", value=False, key=f"dl_summary_{kb_name}"):
                selected_items.append('summaries')
        
        # 聊天历史
        if items['chat_history']:
            chat_count = len(items['chat_history'])
            if st.checkbox(f"💬 聊天历史 ({chat_count}个文件)", value=False, key=f"dl_chat_{kb_name}"):
                selected_items.append('chat_history')
                st.caption("💡 包含与该知识库的所有对话记录")
        
        # 下载按钮
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("📥 下载", key=f"download_btn_{kb_name}", 
                        disabled=not selected_items, use_container_width=True):
                self._handle_download(kb_name, selected_items)
        
        with col2:
            if st.button("❌ 取消", key=f"cancel_download_{kb_name}", use_container_width=True):
                st.session_state[f'show_download_{kb_name}'] = False
                st.rerun()
        
        with col3:
            st.write("")  # 占位
    
    def _handle_download(self, kb_name: str, selected_items: list):
        """处理下载请求"""
        if not selected_items:
            st.warning("请选择要下载的内容")
            return
        
        with st.spinner("正在打包文件..."):
            zip_path = self.download_service.create_download_package(kb_name, selected_items)
        
        if zip_path:
            # 读取文件内容
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            
            # 提供下载
            st.download_button(
                label="💾 点击下载",
                data=zip_data,
                file_name=f"{kb_name}_export.zip",
                mime="application/zip",
                key=f"final_download_{kb_name}",
                use_container_width=True
            )
            
            st.success("✅ 下载包已准备就绪！")
            st.info("💡 下载完成后，请点击下方按钮关闭此对话框")
            
            # 下载完成后的关闭按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ 下载完成", key=f"close_after_download_{kb_name}", use_container_width=True, type="primary"):
                    st.session_state[f'show_download_{kb_name}'] = False
                    st.success("对话框已关闭")
                    st.rerun()
            with col2:
                if st.button("🔄 重新下载", key=f"redownload_{kb_name}", use_container_width=True):
                    # 重置下载状态，允许重新选择
                    st.rerun()
            
            # 清理临时文件
            import os
            try:
                os.remove(zip_path)
                os.rmdir(os.path.dirname(zip_path))
            except:
                pass
        else:
            st.error("创建下载包失败")

def show_download_button(kb_name: str):
    """显示下载按钮"""
    if st.button("📥 下载", help="下载知识库", key=f"show_download_btn_{kb_name}", use_container_width=True):
        st.session_state[f'show_download_{kb_name}'] = True
        st.rerun()

def render_download_dialogs():
    """渲染所有下载对话框"""
    download_ui = KnowledgeBaseDownloadUI()
    
    # 检查所有需要显示的下载对话框
    for key in st.session_state.keys():
        if key.startswith('show_download_') and st.session_state[key]:
            kb_name = key.replace('show_download_', '')
            download_ui.show_download_dialog(kb_name)
