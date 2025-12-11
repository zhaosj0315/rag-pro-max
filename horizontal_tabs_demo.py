#!/usr/bin/env python3
"""
横向标签页演示 - 独立运行
streamlit run horizontal_tabs_demo.py
"""

import streamlit as st

st.set_page_config(
    page_title="RAG Pro Max - 横向标签页演示",
    page_icon="🚀",
    layout="wide"
)

with st.sidebar:
    # 横向标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 主页", "⚙️ 配置", "📊 监控", "🔧 工具", "ℹ️ 帮助"])
    
    with tab1:
        st.markdown("### ⚡ 快速开始")
        st.button("⚡ 一键配置", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.markdown("### 📚 知识库管理")
        
        col1, col2 = st.columns([4, 1])
        with col1:
            st.selectbox("选择知识库", ["知识库1", "知识库2"], label_visibility="collapsed")
        with col2:
            st.button("➕", help="新建")
        
        st.file_uploader("上传文档", type=['pdf', 'txt'])
        
        st.markdown("### ⚡ 快速操作")
        col1, col2 = st.columns(2)
        with col1:
            st.button("🔍 搜索", use_container_width=True)
            st.button("📈 统计", use_container_width=True)
        with col2:
            st.button("🧹 清理", use_container_width=True)
            st.button("💾 导出", use_container_width=True)
    
    with tab2:
        st.markdown("### 🤖 模型配置")
        st.selectbox("模型类型", ["OpenAI", "Ollama"])
        st.text_input("API Key", type="password")
        st.slider("温度", 0.0, 1.0, 0.7)
    
    with tab3:
        st.markdown("### 💻 系统监控")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("CPU", "45%", "↑5%")
            st.metric("内存", "8.2GB")
        with col2:
            st.metric("GPU", "78%", "↓2%")
            st.metric("磁盘", "156GB")
        
        st.checkbox("🔄 自动刷新")
    
    with tab4:
        st.markdown("### 🛠️ 系统工具")
        col1, col2 = st.columns(2)
        with col1:
            st.button("🧪 测试", use_container_width=True)
            st.button("🔄 重启", use_container_width=True)
        with col2:
            st.button("📋 日志", use_container_width=True)
            st.button("🚨 停止", use_container_width=True)
    
    with tab5:
        st.markdown("### 📖 帮助")
        st.info("RAG Pro Max v2.1.0")
        st.caption("横向标签页布局演示")
        
        help_items = ["🚀 快速开始", "❓ 常见问题", "🔧 故障排除"]
        for item in help_items:
            st.button(item, use_container_width=True)

# 主内容区域
st.title("🚀 RAG Pro Max - 横向标签页布局")

st.markdown("""
## 🎯 横向标签页设计

左侧侧边栏现在使用横向标签页布局：

### ✅ 优势
- **空间优化**: 5个标签页横向排列，节省垂直空间
- **功能分类**: 主页、配置、监控、工具、帮助清晰分类
- **操作便捷**: 点击标签页快速切换功能区域
- **视觉清晰**: 现代化的标签页界面

### 🏷️ 标签页说明
- **🏠 主页**: 核心功能 - 知识库管理、文档上传、快速操作
- **⚙️ 配置**: 模型配置 - LLM设置、参数调整
- **📊 监控**: 系统监控 - CPU、GPU、内存、磁盘状态
- **🔧 工具**: 系统工具 - 测试、重启、日志等维护功能
- **ℹ️ 帮助**: 帮助信息 - 文档、FAQ、版本信息

### 🚀 下一步
这个布局可以集成到主应用中，提供更好的用户体验。
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("**当前状态**: 演示模式")
with col2:
    st.success("**布局**: 横向标签页")
with col3:
    st.warning("**版本**: v2.1.0")
