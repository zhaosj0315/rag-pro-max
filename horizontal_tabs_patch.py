#!/usr/bin/env python3
"""
横向标签页补丁 - 最小修改，只改变布局样式
"""

import re

def apply_horizontal_tabs_patch():
    """将侧边栏改为横向标签页布局"""
    
    # 读取原文件
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份原文件
    with open('src/apppro.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 找到侧边栏开始位置
    sidebar_start = content.find('with st.sidebar:')
    if sidebar_start == -1:
        print("❌ 未找到侧边栏代码")
        return False
    
    # 找到侧边栏结束位置（下一个主要代码块）
    lines = content[sidebar_start:].split('\n')
    sidebar_lines = []
    indent_level = 0
    
    for i, line in enumerate(lines):
        if i == 0:  # 第一行 "with st.sidebar:"
            sidebar_lines.append(line)
            continue
            
        # 检查缩进级别
        stripped = line.lstrip()
        if stripped and not line.startswith('    '):  # 不是侧边栏内容
            break
        sidebar_lines.append(line)
    
    # 提取侧边栏内容（去掉第一行和最后的空行）
    sidebar_content = '\n'.join(sidebar_lines[1:]).rstrip()
    
    # 按功能分组侧边栏内容
    sections = {
        'quick_start': extract_section(sidebar_content, '快速开始', '---'),
        'config': extract_section(sidebar_content, '基础配置', '高级功能'),
        'advanced': extract_section(sidebar_content, '高级功能', '性能监控'),
        'monitor': extract_section(sidebar_content, '系统工具', '知识库控制台'),
        'kb_management': extract_section(sidebar_content, '知识库控制台', None)
    }
    
    # 创建横向标签页布局
    new_sidebar = f'''with st.sidebar:
    # 横向标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 主页", "⚙️ 配置", "📊 监控", "🔧 工具", "ℹ️ 帮助"])
    
    with tab1:  # 🏠 主页 - 快速开始 + 知识库管理
{indent_content(sections['quick_start'], 8)}
        st.markdown("---")
{indent_content(sections['kb_management'], 8)}
    
    with tab2:  # ⚙️ 配置 - 基础配置 + 高级功能  
{indent_content(sections['config'], 8)}
        st.markdown("---")
{indent_content(sections['advanced'], 8)}
    
    with tab3:  # 📊 监控 - 系统监控
{indent_content(sections['monitor'], 8)}
    
    with tab4:  # 🔧 工具 - 预留工具功能
        st.markdown("### 🛠️ 工具箱")
        st.info("工具功能开发中...")
    
    with tab5:  # ℹ️ 帮助 - 帮助信息
        st.markdown("### 📖 帮助")
        st.info("RAG Pro Max v2.1.0")
        st.caption("横向标签页布局")
'''
    
    # 替换原侧边栏
    sidebar_end = sidebar_start + len('\n'.join(sidebar_lines))
    new_content = content[:sidebar_start] + new_sidebar + content[sidebar_end:]
    
    # 写入新文件
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 横向标签页补丁已应用")
    print("📁 原文件备份: src/apppro.py.backup")
    return True

def extract_section(content, start_marker, end_marker):
    """提取指定区域的内容"""
    start_pos = content.find(start_marker)
    if start_pos == -1:
        return ""
    
    if end_marker:
        end_pos = content.find(end_marker, start_pos)
        if end_pos == -1:
            return content[start_pos:]
        return content[start_pos:end_pos]
    else:
        return content[start_pos:]

def indent_content(content, spaces):
    """为内容添加指定数量的空格缩进"""
    if not content:
        return ""
    
    lines = content.split('\n')
    indented_lines = []
    
    for line in lines:
        if line.strip():  # 非空行
            indented_lines.append(' ' * spaces + line)
        else:  # 空行
            indented_lines.append('')
    
    return '\n'.join(indented_lines)

def restore_original():
    """恢复原始文件"""
    try:
        with open('src/apppro.py.backup', 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open('src/apppro.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 已恢复原始文件")
        return True
    except FileNotFoundError:
        print("❌ 备份文件不存在")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_original()
    else:
        apply_horizontal_tabs_patch()
