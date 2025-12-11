#!/usr/bin/env python3
"""
简单横向标签页修改
"""

def apply_simple_tabs():
    """应用简单的横向标签页"""
    
    # 读取原文件
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('src/apppro.py.backup2', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 简单替换：在侧边栏开始后立即添加标签页
    old_start = 'with st.sidebar:'
    new_start = '''with st.sidebar:
    # 横向标签页导航
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 主页", "⚙️ 配置", "📊 监控", "🔧 工具", "ℹ️ 帮助"])
    
    with tab1:  # 主页标签'''
    
    # 在侧边栏末尾添加其他标签页
    sidebar_end_marker = '# 在侧边栏添加性能统计'
    tabs_content = '''
    
    with tab2:  # 配置标签
        st.info("配置功能在主页标签中")
    
    with tab3:  # 监控标签  
        st.info("监控功能在主页标签中")
    
    with tab4:  # 工具标签
        st.info("工具功能开发中...")
    
    with tab5:  # 帮助标签
        st.markdown("### 📖 帮助")
        st.info("RAG Pro Max v2.1.0 - 横向标签页版本")

'''
    
    # 执行替换
    content = content.replace(old_start, new_start)
    
    # 在性能统计前添加其他标签页
    if sidebar_end_marker in content:
        content = content.replace(sidebar_end_marker, tabs_content + sidebar_end_marker)
    
    # 写入文件
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 简单横向标签页已应用")

if __name__ == "__main__":
    apply_simple_tabs()
