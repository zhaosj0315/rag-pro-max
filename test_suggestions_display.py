#!/usr/bin/env python3
"""
测试推荐问题前端显示
"""

import streamlit as st
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_suggestions_display():
    """测试推荐问题显示"""
    st.title("🧪 推荐问题显示测试")
    
    # 模拟推荐问题
    test_suggestions = [
        "这个方案的具体实施步骤是什么？",
        "可能遇到哪些实际问题？", 
        "有没有其他替代方案？"
    ]
    
    # 测试1：直接显示推荐问题
    st.subheader("1️⃣ 直接显示测试")
    if test_suggestions:
        st.markdown("##### 🚀 追问推荐")
        for idx, q in enumerate(test_suggestions):
            if st.button(f"👉 {q}", key=f"test_sug_{idx}", use_container_width=True):
                st.success(f"点击了: {q}")
    
    # 测试2：模拟session_state
    st.subheader("2️⃣ Session State 测试")
    if 'test_suggestions_history' not in st.session_state:
        st.session_state.test_suggestions_history = test_suggestions
    
    suggestions_count = len(st.session_state.get('test_suggestions_history', []))
    st.write(f"Session State 中的推荐问题数量: {suggestions_count}")
    
    if st.session_state.get('test_suggestions_history'):
        st.markdown("##### 🚀 Session State 推荐")
        for idx, q in enumerate(st.session_state.test_suggestions_history):
            if st.button(f"👉 {q}", key=f"session_sug_{idx}", use_container_width=True):
                st.success(f"Session State 点击了: {q}")
    else:
        st.warning("Session State 中没有推荐问题")
    
    # 测试3：统一推荐引擎
    st.subheader("3️⃣ 统一推荐引擎测试")
    if st.button("生成推荐问题"):
        try:
            from src.chat.unified_suggestion_engine import get_unified_suggestion_engine
            
            engine = get_unified_suggestion_engine("test_kb")
            suggestions = engine.generate_suggestions(
                context="这是一个测试方案，包含多种解决方法。",
                source_type='chat',
                num_questions=3
            )
            
            st.session_state.engine_suggestions = suggestions
            st.success(f"生成了 {len(suggestions)} 个推荐问题")
            
        except Exception as e:
            st.error(f"生成失败: {e}")
    
    if st.session_state.get('engine_suggestions'):
        st.markdown("##### 🚀 引擎生成的推荐")
        for idx, q in enumerate(st.session_state.engine_suggestions):
            if st.button(f"👉 {q}", key=f"engine_sug_{idx}", use_container_width=True):
                st.success(f"引擎推荐点击了: {q}")

if __name__ == "__main__":
    test_suggestions_display()
