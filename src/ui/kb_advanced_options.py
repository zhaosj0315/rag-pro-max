"""知识库构建高级选项组件"""

import streamlit as st


def render_kb_advanced_options():
    """渲染知识库构建的高级选项，包括OCR和摘要控制"""
    
    with st.expander("🔧 高级选项", expanded=True):
        # 第一行：原有选项
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            force_reindex = st.checkbox(
                "🔄 强制重建索引", 
                False, 
                help="删除现有索引，重新构建（用于修复损坏的索引）"
            )
        
        with adv_col2:
            extract_metadata = st.checkbox(
                "📊 提取元数据", 
                value=False,
                help="开启后提取文件分类、关键词等信息，但会降低 30% 处理速度"
            )
        
        # 第二行：新增OCR和摘要选项
        st.write("")
        ocr_col1, ocr_col2 = st.columns(2)
        
        with ocr_col1:
            use_ocr = st.checkbox(
                "🔍 启用OCR识别",
                value=st.session_state.get('use_ocr', True),
                help="对PDF中的图片和扫描文档进行文字识别（耗时较长）",
                key="kb_use_ocr"
            )
            st.session_state.use_ocr = use_ocr
        
        with ocr_col2:
            generate_summary = st.checkbox(
                "📝 生成文档摘要",
                value=st.session_state.get('generate_summary', False),
                help="为每个文档生成AI摘要（需要LLM支持）",
                key="kb_generate_summary"
            )
            st.session_state.generate_summary = generate_summary
        
        # 处理模式提示
        st.write("")
        if use_ocr and generate_summary:
            st.info("🔍📝 **完整处理模式**：OCR识别 + 摘要生成（处理时间较长，功能最全面）")
        elif use_ocr:
            st.info("🔍 **OCR模式**：启用图片文字识别（适合扫描文档和图片较多的PDF）")
        elif generate_summary:
            st.info("📝 **摘要模式**：生成文档摘要（便于快速了解文档内容）")
        else:
            st.success("⚡ **快速模式**：跳过OCR和摘要，处理速度最快")
    
    return force_reindex, extract_metadata, use_ocr, generate_summary


def render_chat_controls_2x2(state, current_kb_name=None):
    """渲染2×2布局的聊天控制"""
    st.write("**💬 聊天控制**")
    
    # 2×2 布局
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    # 第一行：撤销 | 清空
    with row1_col1:
        if st.button("🔄 撤销", use_container_width=True, disabled=len(state.get_messages()) < 2):
            if len(state.get_messages()) >= 2:
                st.session_state.messages.pop()
                st.session_state.messages.pop()
                st.toast("✅ 已撤销")
                st.rerun()
    
    with row1_col2:
        if st.button("🧹 清空", use_container_width=True, disabled=len(state.get_messages()) == 0):
            st.session_state.messages = []
            st.session_state.suggestions_history = []
            st.toast("✅ 已清空")
            st.rerun()
    
    # 第二行：导出 | 统计
    with row2_col1:
        export_content = ""
        if len(state.get_messages()) > 0:
            from datetime import datetime
            export_content = f"# 对话记录 - {current_kb_name}\n\n"
            export_content += f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
            for i, msg in enumerate(st.session_state.messages, 1):
                role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
                export_content += f"## {role} ({i})\n\n{msg['content']}\n\n"
        
        st.download_button(
            "📥 导出",
            export_content,
            file_name=f"chat_{current_kb_name}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
            use_container_width=True,
            disabled=len(state.get_messages()) == 0
        )
    
    with row2_col2:
        if st.button("📊 统计", use_container_width=True, disabled=len(state.get_messages()) == 0):
            qa_count = len(state.get_messages()) // 2
            total_chars = sum(len(msg["content"]) for msg in st.session_state.messages)
            st.toast(f"💬 {qa_count} 轮对话 | 📝 {total_chars} 字符")
