#!/usr/bin/env python3
"""
多标签页侧边栏布局原型
"""

import streamlit as st

def create_tabbed_sidebar():
    """创建多标签页侧边栏"""
    
    with st.sidebar:
        # 标签页选择
        tab_options = ["🏠 主页", "⚙️ 配置", "📊 监控", "🔧 工具", "ℹ️ 帮助"]
        selected_tab = st.selectbox("", tab_options, key="sidebar_tab")
        
        st.divider()
        
        # 根据选择的标签页显示不同内容
        if selected_tab == "🏠 主页":
            render_home_tab()
        elif selected_tab == "⚙️ 配置":
            render_config_tab()
        elif selected_tab == "📊 监控":
            render_monitor_tab()
        elif selected_tab == "🔧 工具":
            render_tools_tab()
        elif selected_tab == "ℹ️ 帮助":
            render_help_tab()

def render_home_tab():
    """主页标签 - 核心功能"""
    st.subheader("📚 知识库管理")
    
    # 知识库选择（紧凑布局）
    col1, col2 = st.columns([3, 1])
    with col1:
        st.selectbox("选择知识库", ["知识库1", "知识库2"], key="kb_select")
    with col2:
        st.button("➕", help="新建知识库")
    
    # 文档上传（折叠式）
    with st.expander("📄 文档上传"):
        st.file_uploader("上传文档", type=['pdf', 'docx', 'txt'])
        st.button("📁 批量上传")
    
    # 快速操作
    st.subheader("⚡ 快速操作")
    col1, col2 = st.columns(2)
    with col1:
        st.button("🔍 搜索文档")
        st.button("📊 查看统计")
    with col2:
        st.button("🧹 清理缓存")
        st.button("💾 导出数据")

def render_config_tab():
    """配置标签 - 系统设置"""
    st.subheader("🤖 模型配置")
    
    # 折叠式配置组
    with st.expander("LLM 设置", expanded=True):
        st.selectbox("模型类型", ["OpenAI", "Ollama"])
        st.text_input("API Key")
    
    with st.expander("嵌入模型"):
        st.selectbox("嵌入模型", ["BGE", "OpenAI"])
    
    with st.expander("高级设置"):
        st.slider("温度", 0.0, 1.0, 0.7)
        st.slider("Top-K", 1, 10, 5)

def render_monitor_tab():
    """监控标签 - 系统状态"""
    st.subheader("💻 系统监控")
    
    # 实时指标（紧凑显示）
    col1, col2 = st.columns(2)
    with col1:
        st.metric("CPU", "45%", "↑5%")
        st.metric("内存", "8.2GB", "↑0.3GB")
    with col2:
        st.metric("GPU", "78%", "↓2%")
        st.metric("磁盘", "156GB", "↑1GB")
    
    # 性能图表
    with st.expander("📈 性能趋势"):
        st.line_chart({"CPU": [40, 45, 42, 48], "GPU": [75, 78, 80, 78]})

def render_tools_tab():
    """工具标签 - 实用工具"""
    st.subheader("🛠️ 实用工具")
    
    # 工具按钮网格
    col1, col2 = st.columns(2)
    with col1:
        st.button("🧪 运行测试")
        st.button("🔄 重启服务")
        st.button("📋 查看日志")
    with col2:
        st.button("⚡ 一键配置")
        st.button("🚨 紧急停止")
        st.button("📦 导出配置")

def render_help_tab():
    """帮助标签 - 文档和支持"""
    st.subheader("📖 帮助文档")
    
    help_sections = [
        "🚀 快速开始",
        "❓ 常见问题", 
        "🔧 故障排除",
        "📞 联系支持"
    ]
    
    for section in help_sections:
        if st.button(section, use_container_width=True):
            st.info(f"打开 {section}")

# 使用示例
if __name__ == "__main__":
    st.set_page_config(page_title="RAG Pro Max - 多标签页布局", layout="wide")
    
    create_tabbed_sidebar()
    
    # 主内容区域
    st.title("🚀 RAG Pro Max - 新布局设计")
    st.write("侧边栏现在使用多标签页布局，更加简洁高效！")
