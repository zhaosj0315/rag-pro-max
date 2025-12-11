#!/usr/bin/env python3
"""
迁移配置功能到配置标签页
"""

def migrate_config_tab():
    """将配置相关功能迁移到配置标签页"""
    
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 备份
    with open('src/apppro.py.backup_config', 'w', encoding='utf-8') as f:
        f.write(content)
    
    # 找到配置相关的代码段
    # 1. 基础配置部分
    config_start = content.find('# P0改进3: 侧边栏分组 - 基础配置（默认折叠）- 使用新组件 (Stage 3.2.2)')
    config_end = content.find('# P0改进3: 高级功能（默认折叠）- 使用新组件 (Stage 3.2.3)')
    
    if config_start == -1 or config_end == -1:
        print("❌ 未找到配置代码段")
        return False
    
    # 提取基础配置代码
    basic_config_code = content[config_start:config_end].strip()
    
    # 2. 高级功能部分
    advanced_start = config_end
    advanced_end = content.find('# v1.5.1: 性能监控面板', advanced_start)
    
    if advanced_end == -1:
        print("❌ 未找到高级功能结束位置")
        return False
    
    # 提取高级功能代码
    advanced_config_code = content[advanced_start:advanced_end].strip()
    
    # 从主页标签页中移除这些代码
    content_without_config = content[:config_start] + content[advanced_end:]
    
    # 找到配置标签页位置并替换
    config_tab_old = '''    with tab_config:
        st.info("所有配置功能在主页标签中")'''
    
    # 重新缩进配置代码（从4个空格改为8个空格）
    basic_config_indented = indent_code(basic_config_code, 4)
    advanced_config_indented = indent_code(advanced_config_code, 4)
    
    config_tab_new = f'''    with tab_config:
        st.markdown("### ⚙️ 模型配置")
        
{basic_config_indented}
        
{advanced_config_indented}'''
    
    # 替换配置标签页内容
    new_content = content_without_config.replace(config_tab_old, config_tab_new)
    
    # 写入文件
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ 配置功能已迁移到配置标签页")
    print("📁 备份文件: src/apppro.py.backup_config")
    return True

def indent_code(code, additional_spaces):
    """为代码添加额外的缩进"""
    lines = code.split('\n')
    indented_lines = []
    
    for line in lines:
        if line.strip():  # 非空行
            indented_lines.append(' ' * additional_spaces + line)
        else:  # 空行
            indented_lines.append('')
    
    return '\n'.join(indented_lines)

def restore_config():
    """恢复配置迁移前的状态"""
    try:
        with open('src/apppro.py.backup_config', 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open('src/apppro.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ 已恢复配置迁移前的状态")
        return True
    except FileNotFoundError:
        print("❌ 配置备份文件不存在")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_config()
    else:
        migrate_config_tab()
