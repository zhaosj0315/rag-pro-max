#!/usr/bin/env python3
"""
精确迁移配置功能
"""

def migrate_config_precise():
    """精确迁移配置功能"""
    
    with open('src/apppro.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 备份
    with open('src/apppro.py.backup_precise', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    # 找到配置相关的行
    config_start_line = -1
    config_end_line = -1
    advanced_start_line = -1
    advanced_end_line = -1
    
    for i, line in enumerate(lines):
        if '# P0改进3: 侧边栏分组 - 基础配置（默认折叠）- 使用新组件 (Stage 3.2.2)' in line:
            config_start_line = i
        elif '# P0改进3: 高级功能（默认折叠）- 使用新组件 (Stage 3.2.3)' in line:
            config_end_line = i
            advanced_start_line = i
        elif '# v1.5.1: 性能监控面板' in line:
            advanced_end_line = i
            break
    
    if config_start_line == -1 or advanced_end_line == -1:
        print("❌ 未找到配置代码位置")
        return False
    
    # 提取配置代码行
    config_lines = lines[config_start_line:advanced_end_line]
    
    # 从原位置删除这些行
    new_lines = lines[:config_start_line] + lines[advanced_end_line:]
    
    # 找到配置标签页位置
    config_tab_line = -1
    for i, line in enumerate(new_lines):
        if 'with tab_config:' in line:
            config_tab_line = i
            break
    
    if config_tab_line == -1:
        print("❌ 未找到配置标签页")
        return False
    
    # 替换配置标签页内容
    # 删除原来的提示信息行
    del new_lines[config_tab_line + 1]  # 删除 st.info 行
    
    # 在配置标签页后插入配置代码
    insert_pos = config_tab_line + 1
    
    # 添加标题
    new_lines.insert(insert_pos, '        st.markdown("### ⚙️ 模型配置")\n')
    insert_pos += 1
    new_lines.insert(insert_pos, '        \n')
    insert_pos += 1
    
    # 插入配置代码（增加4个空格缩进）
    for config_line in config_lines:
        if config_line.strip():  # 非空行
            new_lines.insert(insert_pos, '    ' + config_line)
        else:  # 空行
            new_lines.insert(insert_pos, config_line)
        insert_pos += 1
    
    # 写入文件
    with open('src/apppro.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("✅ 配置功能已精确迁移到配置标签页")
    return True

if __name__ == "__main__":
    migrate_config_precise()
