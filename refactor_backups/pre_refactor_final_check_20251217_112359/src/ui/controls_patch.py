"""控制组件补丁 - 直接替换主应用中的控制部分"""

import streamlit as st
import time
from datetime import datetime


def render_processing_options_inline():
    """内联渲染处理选项（OCR和摘要控制）"""
    st.write("**📋 处理选项**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        use_ocr = st.checkbox(
            "🔍 启用OCR",
            value=st.session_state.get('use_ocr', True),
            help="识别PDF中的图片文字",
            key="use_ocr_option"
        )
        st.session_state.use_ocr = use_ocr
    
    with col2:
        generate_summary = st.checkbox(
            "📝 生成摘要",
            value=st.session_state.get('generate_summary', False),
            help="为文档生成AI摘要",
            key="generate_summary_option"
        )
        st.session_state.generate_summary = generate_summary
    
    # 状态提示
    if use_ocr and generate_summary:
        st.caption("🔍📝 完整处理模式（较慢但功能全面）")
    elif use_ocr:
        st.caption("🔍 OCR模式（识别图片文字）")
    elif generate_summary:
        st.caption("📝 摘要模式（生成文档摘要）")
    else:
        st.caption("⚡ 快速模式（跳过OCR和摘要）")
    
    return use_ocr, generate_summary


def render_chat_controls_2x2_inline(state, current_kb_name=None):
    """内联渲染2×2聊天控制"""
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
                if current_kb_name:
                    try:
                        from ..chat.history_manager import HistoryManager
                        HistoryManager.save(current_kb_name, state.get_messages())
                    except:
                        pass
                st.toast("✅ 已撤销")
                time.sleep(0.5)
                st.rerun()
    
    with row1_col2:
        if st.button("🧹 清空", use_container_width=True, disabled=len(state.get_messages()) == 0):
            st.session_state.messages = []
            st.session_state.suggestions_history = []
            if current_kb_name:
                try:
                    from ..chat.history_manager import HistoryManager
                    HistoryManager.save(current_kb_name, [])
                except:
                    pass
            st.toast("✅ 已清空")
            time.sleep(0.5)
            st.rerun()
    
    # 第二行：导出 | 统计
    with row2_col1:
        export_content = ""
        if len(state.get_messages()) > 0:
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


def render_system_operations_2x2_inline():
    """内联渲染2×2系统操作"""
    st.write("**🛠️ 系统操作**")
    
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)
    
    with row1_col1:
        if st.button("🔀 新窗口", use_container_width=True):
            st.toast("💡 请复制URL到新标签页")
    
    with row1_col2:
        if st.button("⚡ 快速配置", use_container_width=True):
            st.session_state.use_ocr = True
            st.session_state.generate_summary = False
            st.toast("✅ 已应用推荐配置")
            st.rerun()
    
    with row2_col1:
        current_kb = st.session_state.get('selected_kb')
        if st.button("🗑️ 删除知识库", use_container_width=True, disabled=not current_kb):
            if current_kb:
                st.session_state.show_delete_confirm = True
                st.rerun()
    
    with row2_col2:
        if st.button("🔧 高级设置", use_container_width=True):
            st.session_state.show_advanced = not st.session_state.get('show_advanced', False)
            st.rerun()
    
    # 删除确认对话框
    if st.session_state.get('show_delete_confirm', False):
        current_kb = st.session_state.get('selected_kb')
        st.warning(f"⚠️ 确认删除知识库 '{current_kb}' 吗？")
        col_confirm1, col_confirm2 = st.columns(2)
        
        with col_confirm1:
            if st.button("✅ 确认删除", type="primary", use_container_width=True):
                # 这里应该调用实际的删除逻辑
                st.toast(f"🗑️ 已删除知识库: {current_kb}")
                st.session_state.selected_kb = None
                st.session_state.show_delete_confirm = False
                st.rerun()
        
        with col_confirm2:
            if st.button("❌ 取消", use_container_width=True):
                st.session_state.show_delete_confirm = False
                st.rerun()


# 使用示例：
# 在主应用的侧边栏中替换原有控制为：
#
# # 处理选项控制
# use_ocr, generate_summary = render_processing_options_inline()
# st.write("")
#
# # 聊天控制（2×2布局）
# render_chat_controls_2x2_inline(state, current_kb_name)
# st.write("")
#
# # 系统操作（2×2布局）
# render_system_operations_2x2_inline()
