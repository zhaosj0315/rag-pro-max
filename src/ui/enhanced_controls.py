"""增强的控制组件 - OCR选择、摘要控制、聊天控制"""

import streamlit as st
import time
from datetime import datetime
from typing import Optional


class EnhancedControls:
    """增强的控制组件"""
    
    @staticmethod
    def render_processing_options():
        """渲染处理选项控制（OCR和摘要）"""
        st.write("### 📋 处理选项")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_ocr = st.checkbox(
                "🔍 启用OCR识别",
                value=st.session_state.get('use_ocr', True),
                help="对PDF中的图片和扫描文档进行文字识别",
                key="use_ocr_checkbox"
            )
            st.session_state.use_ocr = use_ocr
            
            if use_ocr:
                st.caption("✅ 将识别图片中的文字内容")
            else:
                st.caption("⚠️ 跳过图片文字识别，处理更快")
        
        with col2:
            generate_summary = st.checkbox(
                "📝 生成文档摘要",
                value=st.session_state.get('generate_summary', False),
                help="为每个文档生成AI摘要",
                key="generate_summary_checkbox"
            )
            st.session_state.generate_summary = generate_summary
            
            if generate_summary:
                st.caption("✅ 将为每个文档生成摘要")
            else:
                st.caption("💨 跳过摘要生成，处理更快")
        
        return use_ocr, generate_summary
    
    @staticmethod
    def render_chat_controls_2x2(state, current_kb_name: Optional[str] = None):
        """渲染2×2布局的聊天控制"""
        st.write("### 💬 聊天控制")
        
        # 2×2 布局
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        
        # 第一行第一列：撤销
        with row1_col1:
            if st.button(
                "🔄 撤销", 
                use_container_width=True, 
                disabled=len(state.get_messages()) < 2,
                help="撤销上一组问答"
            ):
                if len(state.get_messages()) >= 2:
                    st.session_state.messages.pop()
                    st.session_state.messages.pop()
                    if current_kb_name:
                        from ..chat.history_manager import HistoryManager
                        HistoryManager.save(current_kb_name, state.get_messages())
                    st.toast("✅ 已撤销")
                    time.sleep(0.5)
                    st.rerun()
        
        # 第一行第二列：清空
        with row1_col2:
            if st.button(
                "🧹 清空", 
                use_container_width=True, 
                disabled=len(state.get_messages()) == 0,
                help="清空所有对话"
            ):
                st.session_state.messages = []
                st.session_state.suggestions_history = []
                if current_kb_name:
                    from ..chat.history_manager import HistoryManager
                    HistoryManager.save(current_kb_name, [])
                st.toast("✅ 已清空")
                time.sleep(0.5)
                st.rerun()
        
        # 第二行第一列：导出
        with row2_col1:
            export_content = ""
            if len(state.get_messages()) > 0:
                export_content = f"# 对话记录 - {current_kb_name}\n\n"
                export_content += f"**导出时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                export_content += "---\n\n"
                for i, msg in enumerate(st.session_state.messages, 1):
                    role = "👤 用户" if msg["role"] == "user" else "🤖 助手"
                    export_content += f"## {role} ({i})\n\n{msg['content']}\n\n"
            
            st.download_button(
                "📥 导出",
                export_content,
                file_name=f"chat_{current_kb_name}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                use_container_width=True,
                disabled=len(state.get_messages()) == 0,
                help="导出为Markdown文件"
            )
        
        # 第二行第二列：统计
        with row2_col2:
            if st.button(
                "📊 统计", 
                use_container_width=True, 
                disabled=len(state.get_messages()) == 0,
                help="查看对话统计"
            ):
                qa_count = len(state.get_messages()) // 2
                total_chars = sum(len(msg["content"]) for msg in st.session_state.messages)
                user_chars = sum(len(msg["content"]) for msg in st.session_state.messages if msg["role"] == "user")
                assistant_chars = sum(len(msg["content"]) for msg in st.session_state.messages if msg["role"] == "assistant")
                
                st.toast(f"💬 {qa_count} 轮对话 | 📝 {total_chars} 字符")
                
                # 显示详细统计
                with st.expander("📊 详细统计", expanded=True):
                    col_stat1, col_stat2 = st.columns(2)
                    with col_stat1:
                        st.metric("对话轮数", qa_count)
                        st.metric("用户输入", f"{user_chars} 字符")
                    with col_stat2:
                        st.metric("总字符数", total_chars)
                        st.metric("AI回复", f"{assistant_chars} 字符")
    
    @staticmethod
    def render_system_operations():
        """渲染系统操作控制"""
        st.write("### 🛠️ 系统操作")
        
        # 2×2 布局
        row1_col1, row1_col2 = st.columns(2)
        row2_col1, row2_col2 = st.columns(2)
        
        # 第一行第一列：新窗口
        with row1_col1:
            if st.button("🔀 新窗口", use_container_width=True, help="在新窗口中打开应用"):
                st.toast("💡 请手动复制当前URL到新标签页")
        
        # 第一行第二列：快速配置
        with row1_col2:
            if st.button("⚡ 快速配置", use_container_width=True, help="一键配置推荐设置"):
                # 设置推荐配置
                st.session_state.use_ocr = True
                st.session_state.generate_summary = False
                st.toast("✅ 已应用推荐配置")
                st.rerun()
        
        # 第二行第一列：删除知识库
        with row2_col1:
            current_kb = st.session_state.get('selected_kb')
            if st.button(
                "🗑️ 删除知识库", 
                use_container_width=True, 
                disabled=not current_kb,
                help="删除当前选中的知识库"
            ):
                if current_kb:
                    # 这里应该调用实际的删除逻辑
                    st.warning(f"⚠️ 确认删除知识库 '{current_kb}' 吗？")
                    if st.button("确认删除", type="primary"):
                        st.toast(f"🗑️ 已删除知识库: {current_kb}")
                        st.session_state.selected_kb = None
                        st.rerun()
        
        # 第二行第二列：预留
        with row2_col2:
            if st.button("🔧 高级设置", use_container_width=True, help="打开高级设置"):
                st.session_state.show_advanced = not st.session_state.get('show_advanced', False)
                st.rerun()
    
    @staticmethod
    def render_processing_status(use_ocr: bool, generate_summary: bool):
        """渲染处理状态提示"""
        if use_ocr or generate_summary:
            st.info("ℹ️ 处理选项已启用，构建知识库时将执行相应操作")
            
            status_items = []
            if use_ocr:
                status_items.append("🔍 OCR文字识别")
            if generate_summary:
                status_items.append("📝 文档摘要生成")
            
            st.write("**启用功能**: " + " | ".join(status_items))
        else:
            st.success("⚡ 快速模式：跳过OCR和摘要，处理速度最快")


def render_enhanced_sidebar_controls():
    """在侧边栏渲染增强控制组件"""
    controls = EnhancedControls()
    
    # 处理选项
    use_ocr, generate_summary = controls.render_processing_options()
    
    st.write("")
    
    # 聊天控制
    from ..core.state_manager import StateManager
    state = StateManager()
    current_kb = st.session_state.get('selected_kb')
    controls.render_chat_controls_2x2(state, current_kb)
    
    st.write("")
    
    # 系统操作
    controls.render_system_operations()
    
    st.write("")
    
    # 状态提示
    controls.render_processing_status(use_ocr, generate_summary)
    
    return use_ocr, generate_summary
