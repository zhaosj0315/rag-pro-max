#!/usr/bin/env python3
"""
精确的横向转置 - 保持所有原有内容和功能完全一致
"""

def exact_transpose():
    """精确转置，只改变布局方向"""
    
    # 读取原文件
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('src/apppro.py.backup_exact', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 找到侧边栏开始和结束位置
    start_marker = 'with st.sidebar:'
    start_pos = content.find(start_marker)
    
    if start_pos == -1:
        print("❌ 未找到侧边栏")
        return False
    
    # 找到侧边栏结束位置（下一个不缩进的代码块）
    lines = content[start_pos:].split('\n')
    sidebar_lines = [lines[0]]  # 包含 'with st.sidebar:'
    
    for i in range(1, len(lines)):
        line = lines[i]
        # 如果是空行或者以4个空格开始的行，属于侧边栏
        if not line.strip() or line.startswith('    '):
            sidebar_lines.append(line)
        else:
            # 遇到不缩进的行，侧边栏结束
            break
    
    # 提取侧边栏内容（去掉第一行）
    sidebar_content = '\n'.join(sidebar_lines[1:])
    
    # 创建新的横向标签页结构，将所有原内容放在第一个标签页
    new_sidebar = f'''with st.sidebar:
    # 横向标签页布局
    tab_main, tab_config, tab_monitor, tab_tools, tab_help = st.tabs(["🏠 主页", "⚙️ 配置", "📊 监控", "🔧 工具", "ℹ️ 帮助"])
    
    with tab_main:
{indent_all_lines(sidebar_content, 4)}
    
    with tab_config:
        st.info("所有配置功能在主页标签中")
    
    with tab_monitor:
        st.info("所有监控功能在主页标签中")
    
    with tab_tools:
        st.info("所有工具功能在主页标签中")
    
    with tab_help:
        st.markdown("### 📖 帮助")
        st.info("RAG Pro Max v2.1.0 - 横向标签页版本")
'''
    
    # 替换原侧边栏
    sidebar_end_pos = start_pos + len('\n'.join(sidebar_lines))
    new_content = content[:start_pos] + new_sidebar + content[sidebar_end_pos:]
    
    # 写入新文件
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 精确横向转置完成")
    print("📁 备份文件: src/apppro.py.backup_exact")
    print("🔍 所有原有内容都在 '🏠 主页' 标签页中")
    return True

def indent_all_lines(text, spaces):
    """为所有行添加指定数量的空格缩进"""
    if not text:
        return ""
    
    lines = text.split('\n')
    indented_lines = []
    
    for line in lines:
        if line.strip():  # 非空行
            indented_lines.append(' ' * spaces + line)
        else:  # 空行保持空行
            indented_lines.append('')
    
    return '\n'.join(indented_lines)

def restore_exact():
    """恢复原始文件"""
    try:
        with open('src/apppro.py.backup_exact', 'r', encoding='utf-8') as f:
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
        restore_exact()
    else:
        exact_transpose()
