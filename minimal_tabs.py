#!/usr/bin/env python3
"""
最简单的标签页修改 - 只在顶部添加标签页，内容保持原样
"""

def add_minimal_tabs():
    """添加最简单的标签页"""
    
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 只在侧边栏开始后添加标签页，所有内容放在第一个标签页
    old_line = 'with st.sidebar:'
    new_lines = '''with st.sidebar:
    # 横向标签页
    tab_main, tab_config, tab_monitor, tab_tools, tab_help = st.tabs(["🏠 主页", "⚙️ 配置", "📊 监控", "🔧 工具", "ℹ️ 帮助"])
    
    with tab_main:'''
    
    content = content.replace(old_line, new_lines)
    
    # 在文件末尾添加其他标签页（在最后一个侧边栏代码后）
    # 找到最后的侧边栏相关代码
    end_marker = '# 在侧边栏添加性能统计'
    if end_marker in content:
        insert_pos = content.find(end_marker)
        before = content[:insert_pos]
        after = content[insert_pos:]
        
        other_tabs = '''
    with tab_config:
        st.info("配置功能在主页标签中")
    
    with tab_monitor:
        st.info("监控功能在主页标签中")
    
    with tab_tools:
        st.info("🔧 工具功能开发中...")
    
    with tab_help:
        st.markdown("### 📖 帮助")
        st.info("RAG Pro Max v2.1.0")
        st.caption("横向标签页布局")

'''
        content = before + other_tabs + after
    
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ 最简单标签页已添加")

if __name__ == "__main__":
    add_minimal_tabs()
