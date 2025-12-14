#!/usr/bin/env python3
"""
增强控制组件演示
展示OCR选择、摘要控制、2×2聊天控制布局
"""

import streamlit as st
import sys
import os

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def main():
    st.set_page_config(
        page_title="增强控制组件演示",
        page_icon="🎛️",
        layout="wide"
    )
    
    st.title("🎛️ 增强控制组件演示")
    st.write("展示OCR选择、摘要控制、2×2聊天控制布局")
    
    # 初始化session state
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {"role": "user", "content": "你好，这是一个测试消息"},
            {"role": "assistant", "content": "你好！我是AI助手，很高兴为你服务。这是一个演示对话。"},
            {"role": "user", "content": "请介绍一下RAG技术"},
            {"role": "assistant", "content": "RAG（Retrieval-Augmented Generation）是一种结合检索和生成的AI技术，它能够从知识库中检索相关信息，然后基于这些信息生成准确的回答。"}
        ]
    
    if 'selected_kb' not in st.session_state:
        st.session_state.selected_kb = "演示知识库"
    
    # 创建两列布局
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("🎛️ 控制面板")
        
        # 导入控制组件
        try:
            from src.ui.controls_patch import (
                render_processing_options_inline,
                render_chat_controls_2x2_inline,
                render_system_operations_2x2_inline
            )
            
            # 模拟state对象
            class MockState:
                def get_messages(self):
                    return st.session_state.messages
            
            state = MockState()
            
            # 处理选项控制
            st.subheader("📋 处理选项")
            use_ocr, generate_summary = render_processing_options_inline()
            
            st.write("")
            
            # 聊天控制（2×2布局）
            st.subheader("💬 聊天控制")
            render_chat_controls_2x2_inline(state, st.session_state.selected_kb)
            
            st.write("")
            
            # 系统操作（2×2布局）
            st.subheader("🛠️ 系统操作")
            render_system_operations_2x2_inline()
            
        except ImportError as e:
            st.error(f"❌ 导入控制组件失败: {e}")
            st.info("请确保src/ui/controls_patch.py文件存在")
    
    with col2:
        st.header("📊 状态显示")
        
        # 显示当前设置
        st.subheader("⚙️ 当前设置")
        col_setting1, col_setting2 = st.columns(2)
        
        with col_setting1:
            ocr_status = "✅ 启用" if st.session_state.get('use_ocr', True) else "❌ 禁用"
            st.metric("OCR识别", ocr_status)
            
        with col_setting2:
            summary_status = "✅ 启用" if st.session_state.get('generate_summary', False) else "❌ 禁用"
            st.metric("摘要生成", summary_status)
        
        # 显示对话统计
        st.subheader("📈 对话统计")
        qa_count = len(st.session_state.messages) // 2
        total_chars = sum(len(msg["content"]) for msg in st.session_state.messages)
        user_chars = sum(len(msg["content"]) for msg in st.session_state.messages if msg["role"] == "user")
        assistant_chars = sum(len(msg["content"]) for msg in st.session_state.messages if msg["role"] == "assistant")
        
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            st.metric("对话轮数", qa_count)
            st.metric("用户输入", f"{user_chars} 字符")
        with col_stat2:
            st.metric("总字符数", total_chars)
            st.metric("AI回复", f"{assistant_chars} 字符")
        
        # 显示对话历史
        st.subheader("💬 对话历史")
        for i, msg in enumerate(st.session_state.messages):
            role_icon = "👤" if msg["role"] == "user" else "🤖"
            role_name = "用户" if msg["role"] == "user" else "助手"
            
            with st.chat_message(msg["role"]):
                st.write(f"{role_icon} **{role_name}**: {msg['content']}")
    
    # 底部说明
    st.write("")
    st.write("---")
    st.subheader("📖 功能说明")
    
    col_desc1, col_desc2, col_desc3 = st.columns(3)
    
    with col_desc1:
        st.write("**📋 处理选项**")
        st.write("- 🔍 OCR识别：控制是否对PDF图片进行文字识别")
        st.write("- 📝 摘要生成：控制是否为文档生成AI摘要")
        st.write("- ⚡ 快速模式：跳过耗时操作，提升处理速度")
    
    with col_desc2:
        st.write("**💬 聊天控制（2×2布局）**")
        st.write("- 🔄 撤销：撤销最后一轮问答")
        st.write("- 🧹 清空：清空所有对话历史")
        st.write("- 📥 导出：导出对话为Markdown文件")
        st.write("- 📊 统计：显示对话统计信息")
    
    with col_desc3:
        st.write("**🛠️ 系统操作（2×2布局）**")
        st.write("- 🔀 新窗口：在新标签页打开应用")
        st.write("- ⚡ 快速配置：应用推荐设置")
        st.write("- 🗑️ 删除知识库：删除当前知识库")
        st.write("- 🔧 高级设置：打开高级配置")


if __name__ == "__main__":
    main()
