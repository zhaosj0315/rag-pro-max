#!/usr/bin/env python3
"""
多标签页侧边栏演示原型
运行: streamlit run demo_tabbed_sidebar.py
"""

import streamlit as st
import sys
import os

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from ui.tabbed_sidebar import create_tabbed_sidebar
except ImportError:
    # 如果导入失败，使用简化版本
    def create_tabbed_sidebar():
        with st.sidebar:
            tabs = ["🏠 主页", "⚙️ 配置", "📊 监控", "🔧 工具", "ℹ️ 帮助"]
            selected = st.radio("导航", tabs, label_visibility="collapsed")
            
            st.divider()
            
            if "主页" in selected:
                st.markdown("### 📚 知识库管理")
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.selectbox("选择知识库", ["知识库1", "知识库2"], label_visibility="collapsed")
                with col2:
                    st.button("➕", help="新建")
                
                with st.expander("📄 文档上传"):
                    st.file_uploader("上传文档", type=['pdf', 'txt'])
                
                st.markdown("### ⚡ 快速操作")
                col1, col2 = st.columns(2)
                with col1:
                    st.button("🔍 搜索", use_container_width=True)
                    st.button("📈 统计", use_container_width=True)
                with col2:
                    st.button("🧹 清理", use_container_width=True)
                    st.button("💾 导出", use_container_width=True)
            
            elif "配置" in selected:
                st.markdown("### 🤖 模型配置")
                with st.expander("🧠 LLM设置", expanded=True):
                    st.selectbox("模型类型", ["OpenAI", "Ollama"])
                    st.text_input("API Key", type="password")
                
                with st.expander("🔤 嵌入模型"):
                    st.selectbox("嵌入模型", ["BGE", "OpenAI"])
                
                with st.expander("🔧 高级设置"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.slider("温度", 0.0, 1.0, 0.7)
                    with col2:
                        st.slider("Top-K", 1, 10, 5)
            
            elif "监控" in selected:
                st.markdown("### 💻 系统状态")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("CPU", "45%", "↑5%")
                    st.metric("内存", "8.2GB", "↑0.3GB")
                with col2:
                    st.metric("GPU", "78%", "↓2%")
                    st.metric("磁盘", "156GB", "↑1GB")
                
                st.checkbox("🔄 自动刷新")
            
            elif "工具" in selected:
                st.markdown("### 🛠️ 系统工具")
                col1, col2 = st.columns(2)
                with col1:
                    st.button("🧪 测试", use_container_width=True)
                    st.button("🔄 重启", use_container_width=True)
                    st.button("📋 日志", use_container_width=True)
                with col2:
                    st.button("⚡ 配置", use_container_width=True)
                    st.button("🚨 停止", use_container_width=True)
                    st.button("📦 导出", use_container_width=True)
            
            elif "帮助" in selected:
                st.markdown("### 📖 帮助中心")
                help_items = ["🚀 快速开始", "❓ 常见问题", "🔧 故障排除", "📞 联系支持"]
                for item in help_items:
                    st.button(item, use_container_width=True)
                
                st.markdown("### ℹ️ 版本信息")
                st.info("RAG Pro Max v2.1.0")
        
        return selected

def main():
    st.set_page_config(
        page_title="RAG Pro Max - 多标签页布局演示",
        page_icon="🚀",
        layout="wide"
    )
    
    # 渲染侧边栏
    current_tab = create_tabbed_sidebar()
    
    # 主内容区域
    st.title("🚀 RAG Pro Max - 多标签页布局演示")
    
    st.markdown(f"""
    ## 当前标签页: {current_tab}
    
    ### 🎯 设计优势
    
    ✅ **空间优化**: 垂直空间利用更高效  
    ✅ **功能分类**: 相关功能集中管理  
    ✅ **减少滚动**: 每个标签页内容聚焦  
    ✅ **视觉清晰**: 层次分明，易于导航  
    
    ### 📊 布局对比
    
    | 特性 | 原布局 | 新布局 |
    |------|--------|--------|
    | 垂直长度 | 很长，需滚动 | 紧凑，分标签 |
    | 功能查找 | 需要滚动查找 | 标签页直达 |
    | 视觉层次 | 平铺，单调 | 分层，清晰 |
    | 移动端 | 不友好 | 适配良好 |
    
    ### 🔧 技术实现
    
    - **组件化设计**: 每个标签页独立组件
    - **状态管理**: 统一的会话状态管理
    - **响应式布局**: 适配不同屏幕尺寸
    - **性能优化**: 懒加载，只渲染当前标签页
    
    ### 🚀 下一步
    
    1. **完善功能**: 补充所有现有功能
    2. **集成测试**: 与主应用集成测试
    3. **用户反馈**: 收集使用体验反馈
    4. **正式发布**: 作为v2.2.0重要特性
    """)
    
    # 演示区域
    with st.expander("🎮 交互演示", expanded=True):
        st.markdown("""
        **试试看:**
        1. 点击左侧不同的标签页
        2. 体验各个功能区域的布局
        3. 注意观察空间利用效率
        4. 对比原有布局的使用体验
        """)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏠 切换到主页", use_container_width=True):
                st.info("主页标签页包含核心功能：知识库管理、文档上传、快速操作")
        with col2:
            if st.button("⚙️ 切换到配置", use_container_width=True):
                st.info("配置标签页包含：LLM设置、嵌入模型、高级参数")
        with col3:
            if st.button("📊 切换到监控", use_container_width=True):
                st.info("监控标签页包含：系统状态、性能指标、实时数据")

if __name__ == "__main__":
    main()
