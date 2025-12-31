#!/usr/bin/env python3
"""
测试新添加的功能
"""

import streamlit as st

def test_question_templates():
    """测试问题模板功能"""
    st.title("🧪 测试问题模板功能")
    
    # 模拟问题模板选择器
    question_templates = [
        "请选择问题模板...",
        "请总结这个文档的主要内容",
        "这个文档中有哪些重要的数据或结论？",
        "基于文档内容，给我一些实用建议"
    ]
    
    selected = st.selectbox("选择问题模板", question_templates)
    
    if selected != "请选择问题模板...":
        st.success(f"✅ 已选择模板: {selected}")
        
        # 模拟输入框
        user_input = st.text_input("问题输入框", value=selected)
        
        if st.button("发送问题"):
            st.write(f"发送的问题: {user_input}")

def test_progress_display():
    """测试进度显示功能"""
    st.title("🧪 测试文档处理进度")
    
    if st.button("模拟文档处理"):
        # 模拟文件列表
        mock_files = [
            {"name": "文档1.pdf", "size": 1024*1024},
            {"name": "文档2.docx", "size": 512*1024},
            {"name": "文档3.txt", "size": 256*1024}
        ]
        
        # 显示进度
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        import time
        
        for i, file in enumerate(mock_files):
            progress = (i + 1) / len(mock_files)
            progress_bar.progress(progress)
            status_text.text(f"正在处理: {file['name']} ({i+1}/{len(mock_files)})")
            time.sleep(1)
        
        status_text.success("✅ 处理完成！")
        
        # 显示统计
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("文件数量", len(mock_files))
        with col2:
            total_size = sum(f['size'] for f in mock_files) / (1024*1024)
            st.metric("总大小", f"{total_size:.1f} MB")
        with col3:
            st.metric("处理时间", "3 秒")

def main():
    st.set_page_config(page_title="功能测试", layout="wide")
    
    tab1, tab2 = st.tabs(["问题模板测试", "进度显示测试"])
    
    with tab1:
        test_question_templates()
    
    with tab2:
        test_progress_display()

if __name__ == "__main__":
    main()
